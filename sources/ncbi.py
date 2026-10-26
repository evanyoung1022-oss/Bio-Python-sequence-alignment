"""NCBI Entrez, through Biopython's Bio.Entrez module (https://www.ncbi.nlm.nih.gov).

Used to find the same protein in other species. NCBI asks for an email address with
every request; it is read from .streamlit/secrets.toml (NCBI_EMAIL), never from code."""
import time
from io import StringIO

import streamlit as st
from Bio import Entrez, SeqIO

from sources import web

SOURCE = "NCBI"
WEEK = 7 * 24 * 3600


def configure():
    """Load the NCBI email (and optional API key) from st.secrets. Returns True when an
    email is set. An API key makes NCBI allow about 3x more requests per second."""
    try:
        Entrez.email = st.secrets["NCBI_EMAIL"]
    except Exception:
        Entrez.email = None
    try:
        Entrez.api_key = st.secrets["NCBI_API_KEY"]
    except Exception:
        pass
    return bool(Entrez.email)


def call(function, **arguments):
    """Run one Entrez request and read the answer. NCBI allows about 3 requests a second
    without an API key and answers "too many requests" when busy, so failed requests are
    retried after a short, growing pause before giving up with a SourceError."""
    for attempt in range(4):
        try:
            handle = function(**arguments)
            try:
                return Entrez.read(handle) if function is not Entrez.efetch else handle.read()
            finally:
                handle.close()
        except Exception as error:
            if attempt == 3:
                raise web.SourceError("NCBI didn't answer properly (" + type(error).__name__ + "). It limits how "
                                      "fast it can be asked, so wait a few seconds and try again.") from error
            time.sleep(1.5 * (attempt + 1))


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=2000)
def search_accession(term):
    """Accession of the top NCBI protein hit for a search term, or None."""
    result = call(Entrez.esearch, db="protein", term=term, retmax=1, idtype="acc")
    return result["IdList"][0] if result["IdList"] else None


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=200)
def fetch_records(accessions):
    """Download many proteins in one request. Takes a tuple of accessions and returns
    {accession: (description, sequence)}."""
    text = call(Entrez.efetch, db="protein", id=",".join(accessions), rettype="fasta", retmode="text")
    return {r.id: (r.description, str(r.seq)) for r in SeqIO.parse(StringIO(text), "fasta")}


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=500)
def find_gene_id(gene, species):
    """NCBI Gene ID for a gene symbol in one species, or None."""
    result = call(Entrez.esearch, db="gene", term=gene + '[Gene Name] AND "' + species + '"[Organism]', retmax=1)
    return result["IdList"][0] if result["IdList"] else None


@st.cache_data(show_spinner=False, ttl=WEEK, max_entries=2000)
def ortholog_accession(gene_id, species):
    """NCBI keeps lists of the same gene across species (orthologs). Find the one for
    this species and return the accession of its first RefSeq protein, or None."""
    term = "ortholog_gene_" + gene_id + '[group] AND "' + species + '"[Organism]'
    result = call(Entrez.esearch, db="gene", term=term, retmax=1)
    if not result["IdList"]:
        return None
    links = call(Entrez.elink, dbfrom="gene", db="protein", id=result["IdList"][0], linkname="gene_protein_refseq")
    protein_ids = [item["Id"] for linkset in links for db in linkset.get("LinkSetDb", []) for item in db["Link"]]
    if not protein_ids:
        return None
    accession = call(Entrez.efetch, db="protein", id=protein_ids[0], rettype="acc", retmode="text").strip()
    return accession or None
