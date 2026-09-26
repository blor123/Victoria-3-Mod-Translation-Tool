REQUIRED_CONFLICT_FIELDS={"summary","interaction_type","overwrite_risk","important_differences","possible_effects","compatibility_patch_needed","uncertainties","recommended_checks"}


def validate_conflict_result(result: dict) -> dict:
    if not isinstance(result,dict) or not REQUIRED_CONFLICT_FIELDS.issubset(result): raise ValueError("AI conflict result is incomplete.")
    return {key:result[key] for key in REQUIRED_CONFLICT_FIELDS}
