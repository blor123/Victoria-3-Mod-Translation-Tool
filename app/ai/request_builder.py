def conflict_payload(conflict) -> dict:
    """Only evidence snippets and display metadata are sent; never whole mods."""
    return {"type": conflict.category, "severity": conflict.severity, "subject": conflict.subject, "reason": conflict.reason,
            "mod_a": conflict.mod_a, "mod_b": conflict.mod_b, "file_a": conflict.file_a, "file_b": conflict.file_b,
            "snippet_a": conflict.snippet_a, "snippet_b": conflict.snippet_b, "replace_paths": list(conflict.replace_paths)}
