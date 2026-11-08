def external_reference(record, kind: str) -> str:
    """Return the stable cross-system ID for a Scheduling record.

    Falls back to a deterministic namespaced ID so downstream services can
    correlate records even when no explicit external UUID was assigned.
    """
    value = getattr(record, f"external_{kind}_id", None)
    if value:
        return str(value)
    return f"scheduling:{kind}:{record.id}"
