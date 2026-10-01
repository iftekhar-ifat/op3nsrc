"""Load the cleaned tables and build the texts that the models compare."""

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "cleaned"

README_CHARS = 5000   # the start of a README is enough; long READMEs would drown the description

JSON_COLUMNS = {
    "repositories": ["topics", "languages"],
    "issues": ["labels", "linked_pr_ids"],
    "pull_requests": ["labels", "closes_issue_ids", "references_issue_ids", "closes_issue_ids_in_data"],
    "developer_profiles": ["languages", "topics", "repos_contributed", "featured_repo_descs",
                           "pr_titles", "issue_titles"],
}
TIME_COLUMNS = {
    "repositories": ["created_at", "pushed_at"],
    "issues": ["created_at", "updated_at", "closed_at"],
    "pull_requests": ["created_at", "merged_at"],
    "developer_profiles": ["first_contribution_at", "last_contribution_at"],
}
BOOL_COLUMNS = {"issues": ["is_beginner_friendly", "is_help_wanted", "created_in_window"]}


def load(name):
    """Read one table from data/cleaned/ with JSON, time and bool columns parsed."""
    df = pd.read_csv(DATA / f"{name}.csv", keep_default_na=False)
    for c in JSON_COLUMNS[name]:
        df[c] = df[c].map(json.loads)
    for c in TIME_COLUMNS[name]:
        df[c] = pd.to_datetime(df[c].replace("", None), utc=True)
    for c in BOOL_COLUMNS.get(name, []):
        df[c] = df[c].astype(str) == "True"
    return df


def load_all():
    """All five cleaned tables, keyed by name."""
    return {name: load(name) for name in JSON_COLUMNS}


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_CODE = re.compile(r"```.*?(```|\Z)|`[^`\n]+`", re.DOTALL)
_NOISE = re.compile(r"<!--.*?-->|!\[[^\]]*\]\([^)]*\)|<[^>]+>|https?://\S+", re.DOTALL)
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def clean_text(raw):
    """Light cleaning for raw GitHub text (user data): no code, URLs, markdown; lowercase."""
    t = _CODE.sub(" ", raw or "")
    t = _LINK.sub(r"\1", _NOISE.sub(" ", t))
    t = re.sub(r"[#>*_|]", " ", t)
    return " ".join(t.lower().split())


def name_words(full_name):
    """'tiangolo/fastapi' -> 'tiangolo fastapi'; 'react-native' -> 'react native'."""
    return re.sub(r"[/_.-]", " ", full_name.lower())


def repo_context(repos):
    """Short description of each repo: name, language, topics, description."""
    return {r.repo_id: " ".join([name_words(r.repo_id), r.primary_language,
                                 " ".join(r.topics), r.description_clean])
            for r in repos.itertuples()}


def repo_texts(repos):
    """Repo document = context + start of the README (one per row of `repos`)."""
    ctx = repo_context(repos)
    return [f"{ctx[r.repo_id]} {r.readme_clean[:README_CHARS]}" for r in repos.itertuples()]


def issue_texts(issues, repos):
    """Issue document = title + body (final_text) + the context of its repo."""
    ctx = repo_context(repos)
    return list(issues["final_text"] + " | " + issues["repo_id"].map(ctx))
