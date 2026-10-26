"""Canned database answers, so the tests run offline and always see the same data.

`FakeWeb` stands in for sources.web.fetch: it looks at the URL and returns the matching
answer below. The answers are trimmed copies of what the real databases send."""
import json

from sources import web


def uniprot_entry(accession, name, gene, sequence, organism="Homo sapiens", taxon=9606, **extra):
    """A UniProt entry in the same shape as rest.uniprot.org returns."""
    entry = {
        "primaryAccession": accession,
        "entryType": "UniProtKB reviewed (Swiss-Prot)",
        "organism": {"scientificName": organism, "commonName": "Human", "taxonId": taxon,
                     "lineage": ["Eukaryota", "Metazoa", "Chordata", "Mammalia", "Primates"]},
        "proteinDescription": {"recommendedName": {"fullName": {"value": name}}},
        "genes": [{"geneName": {"value": gene}}],
        "sequence": {"value": sequence},
        "comments": [],
        "features": [],
        "uniProtKBCrossReferences": [{"database": "AlphaFoldDB", "id": accession}],
    }
    entry.update(extra)
    return entry


IGHE_SEQUENCE = "ASTQSPSVFPLTRCCKNIPSNATSVTLGCLATGYFPEPVMVTWDTGSLNGTTMTLPATTLTLSGHYATISLLTVSGAWAKQMFTCRVAHTPSSTDWVDNKTFS"
IGHE = uniprot_entry(
    "P01854", "Immunoglobulin heavy constant epsilon", "IGHE", IGHE_SEQUENCE,
    comments=[
        {"commentType": "FUNCTION", "texts": [{"value": "Constant region of immunoglobulin heavy chains (PubMed:123). "
                                                        "Mediates allergic reactions."}]},
        {"commentType": "SUBUNIT", "texts": [{"value": "Interacts with FCER2 (PubMed:16172256). Part of a complex "
                                                       "with CD79A and CD79B."}]},
        {"commentType": "SUBCELLULAR LOCATION", "molecule": "Isoform 1",
         "subcellularLocations": [{"location": {"value": "Secreted"}}]},
        {"commentType": "SUBCELLULAR LOCATION", "molecule": "Isoform 2",
         "subcellularLocations": [{"location": {"value": "Cell membrane"},
                                   "topology": {"value": "Single-pass type I membrane protein"}}]},
        {"commentType": "DISEASE", "disease": {"diseaseId": "Hyper-IgE syndrome", "description": "An immune disorder. More text."}},
    ],
    features=[
        {"type": "Binding site", "location": {"start": {"value": 10}, "end": {"value": 10}},
         "description": "", "ligand": {"name": "Zn(2+)"}},
        {"type": "Active site", "location": {"start": {"value": 20}, "end": {"value": 20}}, "description": "Nucleophile"},
        {"type": "Helix", "location": {"start": {"value": 5}, "end": {"value": 5}}},
    ],
    uniProtKBCrossReferences=[
        {"database": "PDB", "id": "1F6A", "properties": [{"key": "Method", "value": "X-ray"},
                                                         {"key": "Resolution", "value": "3.50 A"},
                                                         {"key": "Chains", "value": "B/D=1-100"}]},
        {"database": "PDB", "id": "1G84", "properties": [{"key": "Method", "value": "NMR"},
                                                         {"key": "Resolution", "value": "-"},
                                                         {"key": "Chains", "value": "A=1-100"}]},
        {"database": "PDB", "id": "2WQR", "properties": [{"key": "Method", "value": "X-ray"},
                                                         {"key": "Resolution", "value": "1.90 A"},
                                                         {"key": "Chains", "value": "A/B=1-100"}]},
        {"database": "GO", "id": "GO:0005576", "properties": [{"key": "GoTerm", "value": "C:extracellular region"}]},
        {"database": "GO", "id": "GO:0005886", "properties": [{"key": "GoTerm", "value": "C:plasma membrane"}]},
        {"database": "GO", "id": "GO:0003823", "properties": [{"key": "GoTerm", "value": "F:antigen binding"}]},
        {"database": "ComplexPortal", "id": "CPX-6969", "properties": [{"key": "EntryName", "value": "IgE complex"}]},
        {"database": "GeneID", "id": "3497"},
        {"database": "AlphaFoldDB", "id": "P01854"},
    ],
)

FCER1A = uniprot_entry("P12319", "High affinity immunoglobulin epsilon receptor subunit alpha", "FCER1A", "MAPAMESPTLLCVALLFFAPDGVLA")
FCER2 = uniprot_entry("P06734", "Low affinity immunoglobulin epsilon Fc receptor", "FCER2", "MEEGQYSEIEELPRRRCCRRGTQ")
CD79A = uniprot_entry("P11912", "B-cell antigen receptor complex-associated protein alpha chain", "CD79A", "MPGGPGVLQALPATIFLLFLLSA")
IGKC = uniprot_entry("P01834", "Immunoglobulin kappa constant", "IGKC", "RTVAAPSVFIFPPSDEQLKSGTASVVCLL")


def search_answer(*entries):
    return json.dumps({"results": list(entries)})


# A tiny mmCIF file: two protein chains (A, B), a heme, a water, and a second NMR model
CIF = """data_TEST
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.auth_seq_id
_atom_site.auth_asym_id
_atom_site.pdbx_PDB_model_num
ATOM 1 N N ALA A 1 1.0 1.0 1.0 101 A 1
ATOM 2 C CA ALA A 1 1.5 1.0 1.0 101 A 1
ATOM 3 C CA SER A 2 3.0 1.0 1.0 102 A 1
ATOM 4 C CA THR A 3 4.5 1.0 1.0 103 A 1
ATOM 5 C CA GLN B 1 1.0 5.0 1.0 1 B 1
ATOM 6 C CA SER B 2 2.0 5.0 1.0 2 B 1
HETATM 7 FE FE HEM C . 2.0 2.0 2.0 201 A 1
HETATM 8 O O HOH D . 9.0 9.0 9.0 301 A 1
ATOM 9 C CA ALA A 1 1.6 1.1 1.1 101 A 2
#
"""

PDB_TEXT = """ATOM      1  N   ALA A   1      11.104  13.207   2.100  1.00 90.00           N
ATOM      2  CA  ALA A   1      12.560  13.207   2.100  1.00 90.00           C
ATOM      3  CA  SER A   2      13.000  14.000   2.100  1.00 80.00           C
ATOM      4  CA  THR A   3      14.000  15.000   2.100  1.00 70.00           C
END
"""

ENTRY_4HHB = {"rcsb_id": "4HHB", "struct": {"title": "THE CRYSTAL STRUCTURE OF HUMAN DEOXYHAEMOGLOBIN"},
              "rcsb_entry_info": {"resolution_combined": [1.74], "experimental_method": "X-ray",
                                  "deposited_atom_count": 4779, "polymer_entity_count": 2},
              "polymer_entities": [
                  {"rcsb_polymer_entity": {"pdbx_description": "Hemoglobin subunit alpha"},
                   "rcsb_polymer_entity_container_identifiers": {"auth_asym_ids": ["A", "C"]},
                   "uniprots": [{"rcsb_id": "P69905"}], "entity_poly": {"rcsb_entity_polymer_type": "Protein"},
                   "rcsb_entity_source_organism": [{"scientific_name": "Homo sapiens"}]},
                  {"rcsb_polymer_entity": {"pdbx_description": "Hemoglobin subunit beta"},
                   "rcsb_polymer_entity_container_identifiers": {"auth_asym_ids": ["B", "D"]},
                   "uniprots": [{"rcsb_id": "P68871"}], "entity_poly": {"rcsb_entity_polymer_type": "Protein"},
                   "rcsb_entity_source_organism": [{"scientific_name": "Homo sapiens"}]}]}

COMPLEX = {"complexAc": "CPX-6969", "name": "IgE - Ig kappa immunoglobulin complex", "species": "Homo sapiens; 9606",
           "functions": ["Antibody that triggers allergic reactions. It binds mast cells."],
           "participants": [
               {"identifier": "P01854", "name": "IGHE", "description": "Immunoglobulin heavy constant epsilon",
                "interactorType": "protein", "stochiometry": "minValue: 2, maxValue: 2"},
               {"identifier": "P01834", "name": "IGKC", "description": "Immunoglobulin kappa constant",
                "interactorType": "protein", "stochiometry": "minValue: 2, maxValue: 2"},
               {"identifier": "CHEBI:1", "name": "sugar", "interactorType": "small molecule"}],
           "crossReferences": [
               {"database": "gene ontology", "qualifier": "cellular component", "identifier": "GO:0005576",
                "description": "extracellular region"},
               {"database": "gene ontology", "qualifier": "molecular function", "identifier": "GO:1",
                "description": "antigen binding"},
               {"database": "wwpdb", "identifier": "4HHB"}]}


class FakeWeb:
    """Replaces web.fetch. Answers are picked by the first URL fragment that matches;
    `fail` lists fragments that should behave like a database that is down."""

    def __init__(self, fail=()):
        self.fail = fail
        self.calls = []

    def answers(self):
        return [
            # UniProt
            ("uniprotkb/P01854.json", json.dumps(IGHE)),
            ("uniprotkb/P12319.json", json.dumps(FCER1A)),
            ("uniprotkb/Q99999.json", web.NotFound("UniProt has no record for that ID.")),
            ("cc_subunit%3AIGHE", search_answer(FCER1A, FCER2)),
            ("gene_exact%3AFCER2", search_answer(FCER2, CD79A)),
            ("gene_exact%3AIGHE", search_answer(IGHE)),
            ("accession%3AP69905", search_answer(uniprot_entry("P69905", "Hemoglobin subunit alpha", "HBA1", "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMF",
                                                               comments=[{"commentType": "SUBCELLULAR LOCATION",
                                                                          "subcellularLocations": [{"location": {"value": "Cytoplasm"}}]}]))),
            ("rest.uniprot.org", search_answer()),
            # RCSB PDB
            ("files.rcsb.org/download/", CIF),
            ("data.rcsb.org/graphql", json.dumps({"data": {"entries": [ENTRY_4HHB]}})),
            ("search.rcsb.org", json.dumps({"result_set": [{"identifier": "4HHB"}]})),
            ("rcsb.org/fasta", ">4HHB_1|Chains A, C|Hemoglobin subunit alpha\nMVLSPADK\n"),
            # AlphaFold
            ("alphafold.ebi.ac.uk/api/prediction/P01854", json.dumps([{"pdbUrl": "https://alphafold.ebi.ac.uk/files/AF.pdb",
                                                                       "globalMetricValue": 76.5}])),
            ("alphafold.ebi.ac.uk/api/prediction", web.NotFound("AlphaFold DB has no record for that ID.")),
            ("alphafold.ebi.ac.uk/files/", PDB_TEXT),
            # STRING (it doesn't know IGHE, like the real one)
            ("interaction_partners?identifiers=IGHE", web.NotFound("STRING has no record for that ID.")),
            ("interaction_partners", json.dumps([{"preferredName_B": "MS4A2", "score": 0.999},
                                                 {"preferredName_B": "FCER1G", "score": 0.998}])),
            ("string-db.org/api/json/network", json.dumps([])),
            # Complex Portal
            ("complex-ws/complex/", json.dumps(COMPLEX)),
            ("complex-ws/search/", json.dumps({"elements": [
                {"complexAC": "CPX-5993", "complexName": "26S proteasome complex", "organismName": "Homo sapiens; 9606",
                 "predictedComplex": False},
                {"complexAC": "CPX-6170", "complexName": "MBL2-MASP1 lectin-protease complex",
                 "organismName": "Homo sapiens; 9606", "predictedComplex": False},
                {"complexAC": "CPX-9999", "complexName": "Predicted proteasome thing", "predictedComplex": True}]})),
        ]

    def __call__(self, url, payload=None, timeout=30, source="the database"):
        self.calls.append(url)
        if any(fragment in url for fragment in self.fail):
            raise web.SourceError(source + " didn't answer in time.")
        for fragment, answer in self.answers():
            if fragment in url:
                if isinstance(answer, Exception):
                    raise answer
                return answer
        raise AssertionError("The test asked for a URL with no canned answer: " + url)
