"""Species the app can compare, with common names and the group used to color the tree."""

# scientific name: (common name, group)
SPECIES = {
    # Primates
    "Homo sapiens": ("Human", "Primates"),
    "Pan troglodytes": ("Chimpanzee", "Primates"),
    "Pan paniscus": ("Bonobo", "Primates"),
    "Gorilla gorilla gorilla": ("Gorilla", "Primates"),
    "Pongo abelii": ("Sumatran orangutan", "Primates"),
    "Macaca mulatta": ("Rhesus macaque", "Primates"),
    "Callithrix jacchus": ("Marmoset", "Primates"),
    # Rodents and rabbits
    "Mus musculus": ("Mouse", "Rodents & rabbits"),
    "Rattus norvegicus": ("Rat", "Rodents & rabbits"),
    "Cavia porcellus": ("Guinea pig", "Rodents & rabbits"),
    "Oryctolagus cuniculus": ("Rabbit", "Rodents & rabbits"),
    # Hoofed mammals
    "Bos taurus": ("Cow", "Hoofed mammals"),
    "Ovis aries": ("Sheep", "Hoofed mammals"),
    "Capra hircus": ("Goat", "Hoofed mammals"),
    "Sus scrofa": ("Pig", "Hoofed mammals"),
    "Camelus dromedarius": ("Dromedary camel", "Hoofed mammals"),
    "Equus caballus": ("Horse", "Hoofed mammals"),
    # Whales and dolphins
    "Tursiops truncatus": ("Bottlenose dolphin", "Whales & dolphins"),
    "Orcinus orca": ("Orca", "Whales & dolphins"),
    # Carnivores
    "Canis lupus familiaris": ("Dog", "Carnivores"),
    "Felis catus": ("Cat", "Carnivores"),
    "Ailuropoda melanoleuca": ("Giant panda", "Carnivores"),
    "Ursus maritimus": ("Polar bear", "Carnivores"),
    # Other mammals
    "Myotis lucifugus": ("Little brown bat", "Other mammals"),
    "Loxodonta africana": ("African elephant", "Other mammals"),
    "Monodelphis domestica": ("Opossum", "Other mammals"),
    "Ornithorhynchus anatinus": ("Platypus", "Other mammals"),
    # Birds and reptiles
    "Gallus gallus": ("Chicken", "Birds & reptiles"),
    "Taeniopygia guttata": ("Zebra finch", "Birds & reptiles"),
    "Chelonia mydas": ("Green sea turtle", "Birds & reptiles"),
    "Anolis carolinensis": ("Green anole", "Birds & reptiles"),
    # Amphibians and fish
    "Xenopus tropicalis": ("Western clawed frog", "Amphibians & fish"),
    "Danio rerio": ("Zebrafish", "Amphibians & fish"),
    "Salmo salar": ("Atlantic salmon", "Amphibians & fish"),
}

# Fungi for the Mushroom enzymes tab (kept separate so "All vertebrates" stays vertebrates)
FUNGI = {
    # Gilled mushrooms (Agaricales)
    "Agaricus bisporus": ("Button mushroom", "Gilled mushrooms"),
    "Pleurotus ostreatus": ("Oyster mushroom", "Gilled mushrooms"),
    "Lentinula edodes": ("Shiitake", "Gilled mushrooms"),
    "Flammulina velutipes": ("Enoki", "Gilled mushrooms"),
    "Psilocybe cubensis": ("Psilocybe cubensis", "Gilled mushrooms"),
    "Coprinopsis cinerea": ("Inky cap", "Gilled mushrooms"),
    "Schizophyllum commune": ("Split gill", "Gilled mushrooms"),
    "Laccaria bicolor": ("Bicolored deceiver", "Gilled mushrooms"),
    "Amanita muscaria": ("Fly agaric", "Gilled mushrooms"),
    # Bracket and wood-rot fungi (Polyporales)
    "Trametes versicolor": ("Turkey tail", "Bracket fungi"),
    "Ganoderma lucidum": ("Reishi", "Bracket fungi"),
    "Phanerochaete chrysosporium": ("White-rot crust fungus", "Bracket fungi"),
    # Other mushrooms
    "Hericium erinaceus": ("Lion's mane", "Other mushrooms"),
    "Serpula lacrymans": ("Dry rot fungus", "Other mushrooms"),
    # Molds and yeasts (Ascomycota), for comparison
    "Cordyceps militaris": ("Cordyceps", "Molds & yeasts"),
    "Aspergillus niger": ("Black mold", "Molds & yeasts"),
    "Neurospora crassa": ("Red bread mold", "Molds & yeasts"),
    "Saccharomyces cerevisiae": ("Baker's yeast", "Molds & yeasts"),
}

MAMMAL_GROUPS = {"Primates", "Rodents & rabbits", "Hoofed mammals",
                 "Whales & dolphins", "Carnivores", "Other mammals"}

# The six species from the original hemoglobin analysis
CLASSIC_SIX = ["Homo sapiens", "Pan troglodytes", "Macaca mulatta",
               "Bos taurus", "Sus scrofa", "Equus caballus"]

GROUP_COLORS = {
    "Primates": "#2a78d6",
    "Rodents & rabbits": "#8e5bd0",
    "Hoofed mammals": "#c9822b",
    "Whales & dolphins": "#1aa3a3",
    "Carnivores": "#d1495b",
    "Other mammals": "#6b7f3a",
    "Birds & reptiles": "#e0a800",
    "Amphibians & fish": "#4a6fa5",
    "Gilled mushrooms": "#b5651d",
    "Bracket fungi": "#7a9a3a",
    "Other mushrooms": "#c2577a",
    "Molds & yeasts": "#5b7db1",
    "Other": "#888888",
}


ALL_NAMES = {**SPECIES, **FUNGI}


def label(name):
    """'Homo_sapiens' or 'Homo sapiens' -> 'Human'."""
    scientific = name.replace("_", " ")
    return ALL_NAMES.get(scientific, (scientific, "Other"))[0]


def group(name):
    scientific = name.replace("_", " ")
    return ALL_NAMES.get(scientific, (scientific, "Other"))[1]

