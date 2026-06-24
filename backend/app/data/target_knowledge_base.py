TARGET_KNOWLEDGE_BASE = [
    {
        "pathogen": "Klebsiella pneumoniae",
        "antibiotic": "meropenem",
        "resistance_mechanism": "carbapenem resistance",
        "gene": "blaKPC-2",
        "resolved_target_name": "KPC-2 beta-lactamase",
        "target_type": "carbapenemase enzyme",
        "target_family": "class A beta-lactamase",
        "mechanism_category": "antibiotic hydrolysis",
        "explanation": (
            "KPC-2 beta-lactamase is a class A carbapenemase associated with "
            "carbapenem resistance in Klebsiella pneumoniae. It can hydrolyze "
            "carbapenem antibiotics such as meropenem."
        ),
        "evidence_source": "local curated AMR target knowledge base",
    },
    {
        "pathogen": "Escherichia coli",
        "antibiotic": "cefotaxime",
        "resistance_mechanism": "extended-spectrum beta-lactam resistance",
        "gene": "blaCTX-M-15",
        "resolved_target_name": "CTX-M-15 beta-lactamase",
        "target_type": "extended-spectrum beta-lactamase enzyme",
        "target_family": "class A beta-lactamase",
        "mechanism_category": "antibiotic hydrolysis",
        "explanation": (
            "CTX-M-15 is an extended-spectrum beta-lactamase associated with "
            "resistance to third-generation cephalosporins such as cefotaxime."
        ),
        "evidence_source": "local curated AMR target knowledge base",
    },
    {
        "pathogen": "Staphylococcus aureus",
        "antibiotic": "methicillin",
        "resistance_mechanism": "methicillin resistance",
        "gene": "mecA",
        "resolved_target_name": "Penicillin-binding protein 2a",
        "target_type": "altered antibiotic target protein",
        "target_family": "penicillin-binding protein",
        "mechanism_category": "target modification",
        "explanation": (
            "The mecA gene encodes penicillin-binding protein 2a, which has "
            "reduced affinity for beta-lactam antibiotics and is associated "
            "with methicillin-resistant Staphylococcus aureus."
        ),
        "evidence_source": "local curated AMR target knowledge base",
    },
    {
        "pathogen": "Mycobacterium tuberculosis",
        "antibiotic": "rifampicin",
        "resistance_mechanism": "rifampicin resistance",
        "gene": "rpoB",
        "resolved_target_name": "RNA polymerase beta subunit",
        "target_type": "mutated antibiotic target protein",
        "target_family": "RNA polymerase",
        "mechanism_category": "target alteration",
        "explanation": (
            "Rifampicin resistance in Mycobacterium tuberculosis is commonly "
            "associated with mutations in rpoB, which encodes the beta subunit "
            "of RNA polymerase, the drug target of rifampicin."
        ),
        "evidence_source": "local curated AMR target knowledge base",
    },
]