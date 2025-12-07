def summarize_memory(memories):
    """
    Very simple summarizer: joins last few memories into a readable summary.
    """
    if not memories:
        return ""

    # Take last 5 items for summary
    last_items = memories[-5:]

    lines = []
    for m in last_items:
        line = f"- ({m.added_at}) {m.source} said: {m.content}"
        lines.append(line)

    summary = "\n".join(lines)
    return summary