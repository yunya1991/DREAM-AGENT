import re


def _slugify(title):
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def resolve_knowledge_target(asset_type, title):
    slug = _slugify(title)
    if not slug:
        raise ValueError("empty_title")
    if asset_type == "operations":
        return f"docs/feishu-collab/runbooks/{slug}.md"
    if asset_type == "delivery":
        return f"docs/feishu-collab/handoffs/{slug}.md"
    if asset_type == "architecture":
        return f"docs/feishu-collab/governance/{slug}.md"
    if asset_type == "policy":
        return f"docs/feishu-collab/governance/{slug}.md"
    raise ValueError("unknown_asset_type")
