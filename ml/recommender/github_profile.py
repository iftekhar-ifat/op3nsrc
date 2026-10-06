"""Turn a user's GitHub data into one profile text.

Input: trimmed GitHub REST API responses (see dummy_users/README.md) with four keys:
user (login), repos (own repos: name, description, topics, language, fork),
languages (bytes per language per repo) and pull_requests (merged PRs: title, body).
Until the live fetch exists, `load_user` reads the dummy users.
"""

import json

from .classification import BODY_CHARS
from .data import ROOT, clean_text, name_words

USERS = ROOT / "dummy_users"


def list_users():
    return sorted(p.stem for p in USERS.glob("*.json"))


def load_user(username):
    """GitHub data for one user (dummy file for now)."""
    return json.loads((USERS / f"{username}.json").read_text())


def _repo_name(api_url):
    """'https://api.github.com/repos/encode/starlette' -> 'encode/starlette'."""
    return api_url.split("/repos/", 1)[-1]


def build_profile(gh):
    """Returns (profile_text, summary dict). Forked repos are skipped."""
    own = [r for r in gh["repos"] if not r["fork"]]

    lang_bytes = {}
    for r in own:
        for lang, n in gh["languages"].get(r["full_name"], {}).items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + n
    top_langs = [l.lower() for l, _ in sorted(lang_bytes.items(), key=lambda kv: -kv[1])[:5]]

    parts = [" ".join(top_langs)]
    for r in own:
        parts.append(" ".join([name_words(r["name"]), clean_text(r["description"]),
                               " ".join(r["topics"]), (r["language"] or "").lower()]))
    for pr in gh["pull_requests"]["items"]:
        parts.append(" ".join([clean_text(pr["title"]), clean_text(pr["body"])[:BODY_CHARS],
                               name_words(_repo_name(pr["repository_url"]))]))

    summary = {
        "login": gh["user"]["login"],
        "own repos": len(own),
        "forks skipped": len(gh["repos"]) - len(own),
        "top languages": ", ".join(top_langs),
        "merged PRs": gh["pull_requests"]["total_count"],
    }
    return " | ".join(p for p in parts if p), summary
