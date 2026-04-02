X_CHAR_LIMIT = 280


def format_post(content: str, hashtags: list[str], platform: str) -> str:
    """Append hashtags to content. Platform-aware:
    - For X: drop hashtags if total length > 280 chars
    - For LinkedIn: always append hashtags
    """
    if not hashtags:
        return content

    hashtag_str = " " + " ".join(f"#{tag}" for tag in hashtags)

    if platform == "x":
        if len(content + hashtag_str) > X_CHAR_LIMIT:
            return content
        return content + hashtag_str

    return content + hashtag_str
