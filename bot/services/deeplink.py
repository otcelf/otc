from uuid import uuid4


def generate_start_token() -> str:
    return uuid4().hex[:10]


def buyer_link(bot_username: str, token: str) -> str:
    return f"https://t.me/{bot_username}?start={token}"
