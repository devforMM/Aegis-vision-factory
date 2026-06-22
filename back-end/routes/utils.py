def format_video_time(seconds):
    """Return a human-readable video timestamp from elapsed seconds."""
    try:
        total_seconds = int(round(seconds))
    except (TypeError, ValueError):
        total_seconds = 0

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours:
        return f"{hours:02}:{minutes:02}:{secs:02}"
    return f"{minutes:02}:{secs:02}"
