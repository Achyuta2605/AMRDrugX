KPC_BETA_LACTAMASE_SEED_SET = [
    {
        "compound_name": "avibactam",
        "candidate_role": "known_beta_lactamase_inhibitor",
        "evidence_type": "seed_query_from_known_beta_lactamase_inhibitor_context",
        "label_status": "known_positive",
        "ground_truth_interaction": "positive",
        "control_type": "expected_positive",
        "notes": "Known beta-lactamase inhibitor seed for KPC/beta-lactamase inhibitor retrieval.",
    },
    {
        "compound_name": "vaborbactam",
        "candidate_role": "known_beta_lactamase_inhibitor",
        "evidence_type": "seed_query_from_known_beta_lactamase_inhibitor_context",
        "label_status": "known_positive",
        "ground_truth_interaction": "positive",
        "control_type": "expected_positive",
        "notes": "Known beta-lactamase inhibitor seed for KPC/beta-lactamase inhibitor retrieval.",
    },
    {
        "compound_name": "clavulanic acid",
        "candidate_role": "known_beta_lactamase_inhibitor",
        "evidence_type": "seed_query_from_beta_lactamase_inhibitor_context",
        "label_status": "to_be_verified",
        "ground_truth_interaction": "unknown",
        "control_type": "candidate",
        "notes": "Beta-lactamase inhibitor seed. Specific relevance to KPC-2 should be verified.",
    },
    {
        "compound_name": "tazobactam",
        "candidate_role": "known_beta_lactamase_inhibitor",
        "evidence_type": "seed_query_from_beta_lactamase_inhibitor_context",
        "label_status": "to_be_verified",
        "ground_truth_interaction": "unknown",
        "control_type": "candidate",
        "notes": "Beta-lactamase inhibitor seed. Specific relevance to KPC-2 should be verified.",
    },
    {
        "compound_name": "sulbactam",
        "candidate_role": "known_beta_lactamase_inhibitor",
        "evidence_type": "seed_query_from_beta_lactamase_inhibitor_context",
        "label_status": "to_be_verified",
        "ground_truth_interaction": "unknown",
        "control_type": "candidate",
        "notes": "Beta-lactamase inhibitor seed. Specific relevance to KPC-2 should be verified.",
    },
    {
        "compound_name": "relebactam",
        "candidate_role": "known_beta_lactamase_inhibitor",
        "evidence_type": "seed_query_from_beta_lactamase_inhibitor_context",
        "label_status": "to_be_verified",
        "ground_truth_interaction": "unknown",
        "control_type": "candidate",
        "notes": "Beta-lactamase inhibitor seed. Specific relevance to KPC-2 should be verified.",
    },
    {
        "compound_name": "nacubactam",
        "candidate_role": "beta_lactamase_inhibitor_candidate",
        "evidence_type": "seed_query_from_beta_lactamase_inhibitor_context",
        "label_status": "to_be_verified",
        "ground_truth_interaction": "unknown",
        "control_type": "candidate",
        "notes": "Candidate seed for beta-lactamase inhibitor retrieval. Requires verification.",
    },
    {
        "compound_name": "zidebactam",
        "candidate_role": "beta_lactamase_inhibitor_candidate",
        "evidence_type": "seed_query_from_beta_lactamase_inhibitor_context",
        "label_status": "to_be_verified",
        "ground_truth_interaction": "unknown",
        "control_type": "candidate",
        "notes": "Candidate seed for beta-lactamase inhibitor retrieval. Requires verification.",
    },
    {
        "compound_name": "aspirin",
        "candidate_role": "negative_control",
        "evidence_type": "negative_control_seed",
        "label_status": "negative_control",
        "ground_truth_interaction": "negative",
        "control_type": "negative_control",
        "notes": "Non-AMR control molecule used to test whether scoring ranks irrelevant compounds highly.",
    },
    {
        "compound_name": "caffeine",
        "candidate_role": "negative_control",
        "evidence_type": "negative_control_seed",
        "label_status": "negative_control",
        "ground_truth_interaction": "negative",
        "control_type": "negative_control",
        "notes": "Non-AMR control molecule used to test whether scoring ranks irrelevant compounds highly.",
    },
    {
        "compound_name": "paracetamol",
        "candidate_role": "negative_control",
        "evidence_type": "negative_control_seed",
        "label_status": "negative_control",
        "ground_truth_interaction": "negative",
        "control_type": "negative_control",
        "notes": "Non-AMR control molecule used to test whether scoring ranks irrelevant compounds highly.",
    },
]


def get_seed_set_for_target(target_name: str):
    normalized_target = target_name.strip().lower()

    if "kpc" in normalized_target or "beta-lactamase" in normalized_target:
        return KPC_BETA_LACTAMASE_SEED_SET

    return []