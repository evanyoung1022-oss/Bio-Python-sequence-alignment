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
    "Other": "#888888",
}


def label(name):
    """'Homo_sapiens' or 'Homo sapiens' -> 'Human'."""
    scientific = name.replace("_", " ")
    return SPECIES.get(scientific, (scientific, "Other"))[0]


def group(name):
    scientific = name.replace("_", " ")
    return SPECIES.get(scientific, (scientific, "Other"))[1]
