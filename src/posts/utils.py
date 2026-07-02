# General utils for posts module
def format_post_summary(title: str, content: str) -> str:
    summary = content[:100]
    if len(content) > 100:
        summary += "..."
    return f"{title}: {summary}"
