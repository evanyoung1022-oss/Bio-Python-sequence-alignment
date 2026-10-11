"""Short notes on each species, focused on how far it is from humans and what that
means for how similar its proteins are. Split times are rough estimates in
millions of years ago (mya); different studies give somewhat different numbers."""

BIOS = {
    "Homo sapiens": "The reference species. Every other species is compared to the human protein.",
    "Pan troglodytes": "Our closest living relative. Our lineages split about 6 to 7 mya, so most "
                       "of its proteins are identical or nearly identical to ours.",
    "Gorilla gorilla": "The largest living primate. Gorillas split from the human and chimpanzee "
                       "lineage about 8 to 10 mya, so their proteins usually differ from ours by "
                       "only a handful of amino acids.",
    "Pongo abelii": "The Sumatran orangutan, the only great ape living in Asia. Its lineage split "
                    "from ours about 15 mya.",
    "Macaca mulatta": "The rhesus macaque, an Old World monkey that split from our lineage about 25 "
                      "to 30 mya. It is widely used in medical research, and the Rh blood group "
                      "is named after it.",
    "Callithrix jacchus": "The common marmoset, a small New World monkey from South America. New "
                          "World monkeys split from our lineage about 40 mya.",
    "Mus musculus": "The house mouse, the most widely used lab mammal. Rodents split from our "
                    "lineage about 85 to 90 mya and have short generations, so their proteins "
                    "often show more changes than other mammals'. Some mouse genes have different "
                    "names, such as Hbb-bs for hemoglobin beta.",
    "Rattus norvegicus": "The brown rat. Its lineage split from the mouse about 12 to 24 mya, so it "
                         "usually lands right next to the mouse on the tree.",
    "Oryctolagus cuniculus": "The European rabbit. Rabbits are not rodents but are their closest "
                             "relatives, and split from our lineage about 85 to 90 mya.",
    "Bos taurus": "Cattle. Hoofed mammals split from our lineage about 95 mya. Cow insulin differs "
                  "from human insulin at only 3 amino acids, which is why it was once used to "
                  "treat diabetes.",
    "Sus scrofa": "The pig. Pig insulin differs from human insulin at just 1 amino acid and was "
                  "used to treat people with diabetes for decades.",
    "Ovis aries": "The sheep, a ruminant like the cow. Dolly the sheep, born in 1996, was the "
                  "first mammal cloned from an adult cell.",
    "Capra hircus": "The goat, one of the first animals people domesticated, about 10,000 years "
                    "ago. It is a close relative of sheep.",
    "Equus caballus": "The horse. Its lineage split from ours about 95 mya. Horse hemoglobin was "
                      "the first hemoglobin structure solved, by Max Perutz, who shared the 1962 "
                      "Nobel Prize in Chemistry for it.",
    "Canis lupus familiaris": "The dog, domesticated from wolves more than 15,000 years ago. "
                              "Carnivores split from our lineage about 95 mya.",
    "Felis catus": "The house cat, a strict carnivore. Like dogs, cats split from our lineage "
                   "about 95 mya.",
    "Tursiops truncatus": "The bottlenose dolphin. Its ancestors were land mammals that returned "
                          "to the sea about 50 mya. Diving mammals pack their muscles with "
                          "myoglobin to store oxygen, and their myoglobin has changes that help "
                          "it stay dissolved at those high levels.",
    "Loxodonta africana": "The African savanna elephant, the largest land animal. Its group "
                          "(Afrotheria) split from ours about 100 mya.",
    "Monodelphis domestica": "The gray short-tailed opossum, a marsupial. Marsupials split from "
                             "our lineage about 160 mya, so their proteins differ much more than "
                             "other mammals'.",
    "Ornithorhynchus anatinus": "The platypus, an egg-laying mammal (monotreme). Its lineage "
                                "split from ours about 180 mya, making it our most distant "
                                "living mammal relative.",
    "Gallus gallus": "The chicken. Birds and mammals split about 320 mya. It was the first bird "
                     "to have its genome sequenced, in 2004.",
    "Taeniopygia guttata": "The zebra finch, a songbird used to study how animals learn sounds. "
                           "Birds split from mammals about 320 mya.",
    "Anolis carolinensis": "The green anole, a lizard from the southeastern United States. It was "
                           "the first reptile to have its genome sequenced, in 2011.",
    "Xenopus tropicalis": "The western clawed frog. Amphibians split from our lineage about "
                          "350 mya, and frog embryos are a classic model for studying "
                          "development.",
    "Danio rerio": "The zebrafish. Fish split from our lineage about 430 mya. Its see-through "
                   "embryos make it a favorite for watching organs develop.",
    "Takifugu rubripes": "The Japanese pufferfish (fugu). It has one of the smallest vertebrate "
                         "genomes, about one eighth the size of ours.",
    "Oryzias latipes": "The Japanese rice fish (medaka), a small fish used in genetics labs "
                       "for over 100 years.",
    "Latimeria chalumnae": "The coelacanth, a lobe-finned fish once thought extinct until one was "
                           "caught in 1938. Lobe-finned fish are closer to us than to most other "
                           "fish.",
}


# Cartoon icon (emoji) for each species
ICONS = {
    "Homo sapiens": "🧑", "Pan troglodytes": "🐒", "Gorilla gorilla": "🦍", "Pongo abelii": "🦧",
    "Macaca mulatta": "🐵", "Callithrix jacchus": "🐒", "Mus musculus": "🐁", "Rattus norvegicus": "🐀",
    "Oryctolagus cuniculus": "🐇", "Bos taurus": "🐄", "Sus scrofa": "🐖", "Ovis aries": "🐑",
    "Capra hircus": "🐐", "Equus caballus": "🐎", "Canis lupus familiaris": "🐕", "Felis catus": "🐈",
    "Tursiops truncatus": "🐬", "Loxodonta africana": "🐘", "Monodelphis domestica": "🐀",
    "Ornithorhynchus anatinus": "🦆", "Gallus gallus": "🐔", "Taeniopygia guttata": "🐦",
    "Anolis carolinensis": "🦎", "Xenopus tropicalis": "🐸", "Danio rerio": "🐟",
    "Takifugu rubripes": "🐡", "Oryzias latipes": "🐠", "Latimeria chalumnae": "🐟",
}


def icon(species):
    """The emoji for a species, or a generic paw print if we don't have one."""
    return ICONS.get(species.replace("_", " "), "🐾")


def bio(species, group=None):
    """The note for a species, or a general one built from its group if we don't have one."""
    species = species.replace("_", " ")
    if species in BIOS:
        return BIOS[species]
    if group:
        return "A member of the " + group + " group. Compare its numbers below with the other species."
    return "No notes yet for this species. Compare its numbers below with the other species."