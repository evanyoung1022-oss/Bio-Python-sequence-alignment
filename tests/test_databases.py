"""How searches are built and how UniProt answers are read. No internet needed."""
from databases import (build_query, is_ec_number, is_the_enzyme, is_uniprot_accession,
                       ncbi_exclusions, parse_sites, plain_name, summarize)


def test_recognizes_enzyme_numbers():
    assert is_ec_number("1.10.3.2")
    assert is_ec_number("3.2.1.-")
    assert not is_ec_number("1.10.3")
    assert not is_ec_number("laccase")


def test_recognizes_uniprot_accessions():
    assert is_uniprot_accession("P68871")
    assert is_uniprot_accession("a0a0b4j2f0")
    assert not is_uniprot_accession("TP53")
    assert not is_uniprot_accession("4HHB")


def test_build_query():
    assert build_query("1.10.3.2") == "ec:1.10.3.2"
    assert build_query("p68871") == "accession:P68871"
    assert build_query("TP53") == "gene_exact:TP53 OR TP53"
    assert build_query("hemoglobin beta") == "hemoglobin beta"
    assert build_query("laccase", "Pleurotus") == '(laccase) AND organism_name:"Pleurotus"'


def test_summarize_reads_a_search_result():
    result = {
        "primaryAccession": "P68871",
        "entryType": "UniProtKB reviewed (Swiss-Prot)",
        "organism": {"scientificName": "Homo sapiens"},
        "proteinDescription": {"recommendedName": {"fullName": {"value": "Hemoglobin subunit beta"}}},
        "genes": [{"geneName": {"value": "HBB"}}],
        "sequence": {"value": "MVHLTPEEK"},
    }
    info = summarize(result)
    assert info == {"accession": "P68871", "name": "Hemoglobin subunit beta", "ec": [], "gene": "HBB",
                    "organism": "Homo sapiens", "reviewed": True, "sequence": "MVHLTPEEK"}
    unreviewed = dict(result, entryType="UniProtKB unreviewed (TrEMBL)", proteinDescription={
        "submissionNames": [{"fullName": {"value": "laccase"}, "ecNumbers": [{"value": "1.10.3.2"}]}]})
    assert summarize(unreviewed)["reviewed"] is False
    assert summarize(unreviewed)["ec"] == ["1.10.3.2"]


def test_parse_sites_keeps_single_residue_sites():
    def feature(kind, start, end, **extra):
        return {"type": kind, "location": {"start": {"value": start}, "end": {"value": end}}, **extra}

    entry = {"features": [
        feature("Active site", 64, 64, description="Proton donor/acceptor"),
        feature("Binding site", 94, 94, description="", ligand={"name": "Zn(2+)"}),
        feature("Binding site", 10, 20, description="range, skipped"),
        feature("Helix", 5, 5, description="not a functional site"),
    ]}
    assert parse_sites(entry) == [
        {"position": 64, "kind": "Active site", "label": "Proton donor/acceptor"},
        {"position": 94, "kind": "Binding site", "label": "Zn(2+)"},
    ]


def test_is_the_enzyme_skips_look_alikes():
    def match(name, ec=()):
        return {"name": name, "ec": list(ec)}

    assert is_the_enzyme(match("Actin-1"), "actin", "")
    assert is_the_enzyme(match("Beta-actin"), "actin", "")
    assert not is_the_enzyme(match("Actin-binding protein"), "actin", "")
    assert not is_the_enzyme(match("Cofilin"), "actin", "")
    assert not is_the_enzyme(match("Alpha-actinin"), "actin", "")
    # A matching EC number counts even when the name is unhelpful
    assert is_the_enzyme(match("Contig An01c0440, genomic contig", ["1.10.3.2"]), "laccase", "1.10.3.2")
    # Words that are part of the search itself aren't held against a match
    assert is_the_enzyme(match("Chitin-binding protein"), "chitin-binding protein", "")


def test_plain_name():
    assert plain_name("Laccase 1b", "laccase")
    assert plain_name("Actin, gamma", "actin")
    assert plain_name("Beta-actin", "actin")
    assert not plain_name("Actin cytoskeleton organization protein", "actin")


def test_ncbi_exclusions():
    text = ncbi_exclusions("actin")
    assert " NOT binding[Title]" in text
    assert "kinase" not in ncbi_exclusions("protein kinase")
