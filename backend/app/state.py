def determine_threat_level(threat_score: int) -> str:
    if not 0 <= threat_score <= 100:
        raise ValueError("Threat score must be between 0 and 100.")

    if threat_score <= 30:
        return "NORMAL"
    if threat_score <= 50:
        return "SUSPICIOUS"
    if threat_score <= 70:
        return "ELEVATED"
    if threat_score <= 90:
        return "HIGH_THREAT"

    return "CRITICAL"