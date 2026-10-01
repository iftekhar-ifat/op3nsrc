"""Clean the raw GitHub data and build the tables for EDA + the NLP models.

Run (offline, no GitHub access needed):
    python3 data_collection/clean.py

Reads  data/repo_list.csv + data/raw/{repos,readmes,issues,pulls}/
Writes data/cleaned/
    repositories.csv           one row per repo
    issues.csv                 one row per issue (final_text = cleaned title + body)
    pull_requests.csv          one row per merged PR that links an issue
    developer_profiles.csv     one row per PR author (summary used in EDA)

Conventions:
    - repo_id  = name in repo_list.csv ("owner/repo"). Some repos were renamed
                 on GitHub; the current name is kept in `current_full_name`.
    - issue_id = "owner/repo#123",  pr_id = "owner/repo!456"
    - list columns are stored as JSON strings -> json.loads() in pandas.
    - empty text is written as "" -> read with
      pd.read_csv(path, keep_default_na=False) so it stays "" instead of NaN.
    - Raw files are never modified (see data-collection-and-processing.md §5).
"""

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REPO_LIST = ROOT / "data" / "repo_list.csv"
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "cleaned"

SINCE = "2026-06-24T00:00:00Z"   # collection window start (same as collector)
README_MAX_CHARS = 20_000        # long READMEs add little beyond the intro

# ---------------------------------------------------------------------------
# Text cleaning (data-collection-and-processing.md §6.2)
# Light on purpose: no stemming / stopwords here; the TF-IDF baseline does that
# itself, and Sentence-BERT works better on natural text.
# ---------------------------------------------------------------------------

HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)        # issue-template hints
CODE_BLOCK = re.compile(r"```.*?(```|\Z)|~~~.*?(~~~|\Z)", re.DOTALL)  # also unclosed fences
INLINE_CODE = re.compile(r"`[^`\n]+`")
MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")              # [text](url) -> text
HTML_TAG = re.compile(r"<[^>]+>")
URL = re.compile(r"https?://\S+|www\.\S+")
CHECKBOX_LINE = re.compile(r"^\s*[-*]\s*\[[ xX]\].*$", re.MULTILINE)  # template checklists
MD_SYNTAX = re.compile(r"^\s{0,3}(#{1,6}|>+|[-*+]|\d+\.)\s+", re.MULTILINE)
EMPHASIS = re.compile(r"[*_]{1,3}([^*_\n]+)[*_]{1,3}")
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{3,}.*$", re.MULTILINE)


def clean_text(raw):
    t = raw or ""
    t = HTML_COMMENT.sub(" ", t)
    t = CODE_BLOCK.sub(" ", t)
    t = INLINE_CODE.sub(" ", t)
    t = MD_IMAGE.sub(" ", t)
    t = MD_LINK.sub(r"\1", t)
    t = HTML_TAG.sub(" ", t)
    t = URL.sub(" ", t)
    t = CHECKBOX_LINE.sub(" ", t)
    t = TABLE_RULE.sub(" ", t)
    t = MD_SYNTAX.sub("", t)
    t = EMPHASIS.sub(r"\1", t)
    t = t.replace("|", " ")
    t = t.lower()
    return " ".join(t.split())


# ---------------------------------------------------------------------------
# PR -> issue links (§4.5)
# GitHub's closing keywords: close(s/d), fix(es/ed), resolve(s/d).
# "refs #N" only mentions an issue, so it is kept as a reference but is NOT
# used as a positive label.
# ---------------------------------------------------------------------------

CLOSING = r"(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)"
REFERENCE = r"refs?"
LINK_PATTERNS = [
    # "Fixes #12"
    re.compile(rf"\b(?P<kw>{CLOSING}|{REFERENCE}):?\s+#(?P<num>\d+)", re.I),
    # "Fixes owner/repo#12"
    re.compile(rf"\b(?P<kw>{CLOSING}|{REFERENCE}):?\s+(?P<repo>[\w.-]+/[\w.-]+)#(?P<num>\d+)", re.I),
    # "Fixes https://github.com/owner/repo/issues/12"
    re.compile(
        rf"\b(?P<kw>{CLOSING}|{REFERENCE}):?\s+https?://github\.com/(?P<repo>[\w.-]+/[\w.-]+)/issues/(?P<num>\d+)",
        re.I,
    ),
]


def extract_links(text, repo_names):
    """Return {issue_number: "closing"|"reference"} for links into this repo.

    repo_names: lowercase names the repo is known by (CSV name + current name),
    so cross-repo links ("other/repo#5") are ignored.
    """
    links = {}
    for pat in LINK_PATTERNS:
        for m in pat.finditer(text or ""):
            repo = m.groupdict().get("repo")
            if repo and repo.lower() not in repo_names:
                continue
            kind = "reference" if re.fullmatch(REFERENCE, m["kw"], re.I) else "closing"
            num = int(m["num"])
            if links.get(num) != "closing":       # closing wins over reference
                links[num] = kind
    return links


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

BEGINNER = re.compile(
    r"good.?first|first.?(time|timers?|contribution)|beginner|starter|newcomer|(^|[\s:/-])easy\b",
    re.I,
)
NOT_BEGINNER = re.compile(r"not.?as.?easy", re.I)
HELP_WANTED = re.compile(r"help.?wanted|help.?needed|contrib.?help", re.I)


def normalize_label(name):
    """'🌱 Good First Issue' -> 'good first issue'."""
    name = re.sub(r":[a-z_]+:", " ", name.lower())           # :sos: style emoji codes
    name = re.sub(r"[^\w\s/:.+#-]", " ", name)               # unicode emoji etc.
    return " ".join(name.split())


def is_beginner(labels):
    return any(BEGINNER.search(l) and not NOT_BEGINNER.search(l) for l in labels)


def is_help_wanted(labels):
    return any(HELP_WANTED.search(l) for l in labels)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def stem_of(full_name):
    return full_name.replace("/", "__")


def load_pages(subfolder, stem):
    records = []
    for f in sorted((RAW / subfolder).glob(f"{stem}__page*.json")):
        records += json.loads(f.read_text())
    return records


def login_of(rec):
    return (rec.get("user") or {}).get("login") or "ghost"   # deleted accounts


# Automation accounts registered as normal users (CI failure reporters).
KNOWN_AUTOMATION = {"cockroach-teamcity", "elasticsearchmachine", "GordonTheTurtle"}
BOT_LOGIN = re.compile(r"(\[bot\]|bot|robot)$", re.I)   # gopherbot, tekton-robot, ...


def is_bot(rec):
    user = rec.get("user") or {}
    login = user.get("login") or ""
    return (
        user.get("type") == "Bot"                           # e.g. Copilot agent
        or bool(BOT_LOGIN.search(login))
        or login in KNOWN_AUTOMATION
    )


def jdump(value):
    return json.dumps(value, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def build_repositories(repo_ids):
    rows = []
    for rid in repo_ids:
        stem = stem_of(rid)
        info = json.loads((RAW / "repos" / f"{stem}.json").read_text())
        langs = json.loads((RAW / "repos" / f"{stem}__languages.json").read_text())
        topics = json.loads((RAW / "repos" / f"{stem}__topics.json").read_text()).get("names", [])
        readme = (RAW / "readmes" / f"{stem}.md").read_text(errors="ignore")
        total = sum(langs.values()) or 1
        rows.append({
            "repo_id": rid,
            "current_full_name": info["full_name"],
            "description_clean": clean_text(info.get("description")),
            "readme_clean": clean_text(readme)[:README_MAX_CHARS],
            "topics": jdump([t.lower() for t in topics]),
            "primary_language": (info.get("language") or "").lower(),
            # language -> share of bytes, largest first (§6.1 keeps the byte info)
            "languages": jdump({k.lower(): round(v / total, 4) for k, v in
                                sorted(langs.items(), key=lambda kv: -kv[1])}),
            "stars": info.get("stargazers_count"),
            "forks": info.get("forks_count"),
            "open_issues": info.get("open_issues_count"),
            "is_archived": info.get("archived", False),
            "license": ((info.get("license") or {}).get("spdx_id") or ""),
            "created_at": info.get("created_at"),
            "pushed_at": info.get("pushed_at"),
            "html_url": info.get("html_url"),
        })
    return pd.DataFrame(rows)


def build_issues(repo_ids):
    rows, seen = [], set()
    for rid in repo_ids:
        for rec in load_pages("issues", stem_of(rid)):
            key = (rid, rec["number"])
            login = login_of(rec)
            # collector already filters these; re-check so the table is safe
            # even if raw data was collected differently
            if key in seen or rec.get("pull_request") or is_bot(rec):
                continue
            seen.add(key)
            labels = [normalize_label(l["name"]) for l in rec.get("labels", [])]
            title_clean = clean_text(rec.get("title"))
            body_clean = clean_text(rec.get("body"))
            issue_type = rec.get("type")
            rows.append({
                "issue_id": f"{rid}#{rec['number']}",
                "repo_id": rid,
                "number": rec["number"],
                "title": rec.get("title") or "",
                "title_clean": title_clean,
                "body_clean": body_clean,
                # title + body, or title alone when the body is empty (§6.2)
                "final_text": f"{title_clean}. {body_clean}" if body_clean else title_clean,
                "labels": jdump(labels),
                "is_beginner_friendly": is_beginner(labels),
                "is_help_wanted": is_help_wanted(labels),
                "issue_type": (issue_type or {}).get("name", "").lower() if isinstance(issue_type, dict) else "",
                "state": rec.get("state"),
                "state_reason": rec.get("state_reason") or "",
                "created_at": rec.get("created_at"),
                "updated_at": rec.get("updated_at"),
                "closed_at": rec.get("closed_at"),
                "created_in_window": (rec.get("created_at") or "") >= SINCE,
                "comment_count": rec.get("comments", 0),
                "reactions": (rec.get("reactions") or {}).get("total_count", 0),
                "author_login": login,
                "author_association": rec.get("author_association", ""),
                "assignee_count": len(rec.get("assignees") or []),
                "html_url": rec.get("html_url"),
            })
    df = pd.DataFrame(rows)
    df = df[df["final_text"].str.len() > 0]
    return df


def build_pull_requests(repo_ids, repos_df):
    names = {
        r.repo_id: {r.repo_id.lower(), r.current_full_name.lower()}
        for r in repos_df.itertuples()
    }
    rows, seen = [], set()
    for rid in repo_ids:
        for rec in load_pages("pulls", stem_of(rid)):
            key = (rid, rec["number"])
            login = login_of(rec)
            # pages can overlap when new PRs arrive mid-collection -> dedupe
            if key in seen or not rec.get("merged_at") or is_bot(rec):
                continue
            seen.add(key)
            links = extract_links(f"{rec.get('title') or ''}\n{rec.get('body') or ''}", names[rid])
            closing = sorted(n for n, k in links.items() if k == "closing")
            refs = sorted(n for n, k in links.items() if k == "reference")
            rows.append({
                "pr_id": f"{rid}!{rec['number']}",
                "repo_id": rid,
                "number": rec["number"],
                "title": rec.get("title") or "",
                "title_clean": clean_text(rec.get("title")),
                "body_clean": clean_text(rec.get("body")),
                "author_login": login,
                "author_association": rec.get("author_association", ""),
                "created_at": rec.get("created_at"),
                "merged_at": rec.get("merged_at"),
                "labels": jdump([normalize_label(l["name"]) for l in rec.get("labels", [])]),
                "closes_issue_ids": jdump([f"{rid}#{n}" for n in closing]),
                "references_issue_ids": jdump([f"{rid}#{n}" for n in refs]),
                "html_url": rec.get("html_url"),
            })
    return pd.DataFrame(rows)


def add_issue_links(issues, prs):
    """Fill linked_pr_ids on issues and link_verified on PRs (§6.1 step 6)."""
    known = set(issues["issue_id"])
    linked = defaultdict(list)
    verified = []
    for pr in prs.itertuples():
        ids = json.loads(pr.closes_issue_ids)
        verified.append([i for i in ids if i in known])
        for i in ids:
            linked[i].append(pr.pr_id)
    prs["closes_issue_ids_in_data"] = [jdump(v) for v in verified]
    prs["link_verified"] = [bool(v) for v in verified]
    issues["linked_pr_ids"] = issues["issue_id"].map(lambda i: jdump(linked.get(i, [])))
    return issues, prs


def build_developer_profiles(prs, issues, repos):
    """One row per PR author; experience_text summarises their contributions (used in EDA)."""
    repo_info = repos.set_index("repo_id")
    issues_by_author = issues.groupby("author_login")["title_clean"].apply(list)
    rows = []
    for login, grp in prs.sort_values("merged_at").groupby("author_login"):
        lang_weight, topic_count = Counter(), Counter()
        for rid, n in grp["repo_id"].value_counts().items():
            for lang, share in json.loads(repo_info.at[rid, "languages"]).items():
                lang_weight[lang] += share * n
            for t in json.loads(repo_info.at[rid, "topics"]):
                topic_count[t] += n
        languages = [l for l, w in lang_weight.most_common() if w >= 0.1][:8]
        topics = [t for t, _ in topic_count.most_common(15)]
        repos_contrib = list(grp["repo_id"].unique())
        repo_descs = [repo_info.at[r, "description_clean"] for r in repos_contrib]
        pr_titles = list(grp["title_clean"])
        issue_titles = issues_by_author.get(login, [])
        experience_text = " | ".join(
            part for part in [
                " ".join(languages),
                " ".join(topics),
                " | ".join(repo_descs),
                " | ".join(pr_titles),
                " | ".join(issue_titles),
            ] if part
        )
        rows.append({
            "developer_id": login,
            "login": login,
            "languages": jdump(languages),
            "topics": jdump(topics),
            "repos_contributed": jdump(repos_contrib),
            "featured_repo_descs": jdump(repo_descs),
            "pr_titles": jdump(pr_titles),
            "issue_titles": jdump(list(issue_titles)),
            "experience_text": experience_text,
            "merged_pr_count": len(grp),
            "repo_count": len(repos_contrib),
            "issues_opened": len(issue_titles),
            "first_contribution_at": grp["merged_at"].min(),
            "last_contribution_at": grp["merged_at"].max(),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------

def main():
    repo_ids = [r["full_name"].strip() for r in csv.DictReader(REPO_LIST.open())]
    OUT.mkdir(parents=True, exist_ok=True)

    repos = build_repositories(repo_ids)
    repos = repos[~repos["is_archived"]]
    repo_ids = list(repos["repo_id"])

    issues = build_issues(repo_ids)
    prs = build_pull_requests(repo_ids, repos)
    issues, prs = add_issue_links(issues, prs)
    devs = build_developer_profiles(prs, issues, repos)

    tables = {
        "repositories": repos,
        "issues": issues,
        "pull_requests": prs,
        "developer_profiles": devs,
    }
    for name, df in tables.items():
        df.to_csv(OUT / f"{name}.csv", index=False)

    print(f"Wrote {OUT}/")
    print(f"  repositories          {len(repos):>6}")
    print(f"  issues                {len(issues):>6}  "
          f"(open {int((issues['state'] == 'open').sum())}, "
          f"beginner-friendly {int(issues['is_beginner_friendly'].sum())}, "
          f"help wanted {int(issues['is_help_wanted'].sum())}, "
          f"created before window {int((~issues['created_in_window']).sum())})")
    print(f"  pull_requests         {len(prs):>6}  "
          f"(closing link to an issue in our data: {int(prs['link_verified'].sum())})")
    print(f"  developer_profiles    {len(devs):>6}  "
          f"(1 PR: {int((devs['merged_pr_count'] == 1).sum())})")


if __name__ == "__main__":
    main()
