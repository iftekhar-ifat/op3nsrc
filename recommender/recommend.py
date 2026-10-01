"""GitHub user -> top 5 repos (classifier) -> top 3 open issues in each (text matching)."""

import numpy as np

from .data import issue_texts, repo_texts
from .github_profile import build_profile, load_user
from .models import TextMatcher

LABEL_BOOST = 0.05   # small bonus for issues labelled good first issue / help wanted


class Recommender:
    def __init__(self, classifier, repos, issues):
        """classifier: a fitted pipeline from models.make_classifiers (classes = repo_ids)."""
        self.classifier = classifier
        open_issues = issues[issues["state"] == "open"]
        # recommendable = repos the classifier knows AND that have open issues to start on
        ok = set(classifier.classes_) & set(open_issues["repo_id"])
        self.class_mask = np.array([c in ok for c in classifier.classes_])
        self.repos = repos.set_index("repo_id")
        self.issues = open_issues[open_issues["repo_id"].isin(ok)].reset_index(drop=True)
        self.issue_rows = self.issues.groupby("repo_id").indices

        # TF-IDF matcher for ranking issues and for the "Why"
        repo_docs = dict(zip(repos["repo_id"], repo_texts(repos)))
        issue_docs = issue_texts(self.issues, repos)
        self.matcher = TextMatcher().fit(list(repo_docs.values()) + issue_docs)
        self.repo_vecs = {r: self.matcher.embed([d]) for r, d in repo_docs.items() if r in ok}
        self.issue_matrix = self.matcher.embed(issue_docs)

    def recommend(self, gh, top_repos=5, top_issues=3):
        """gh: GitHub data in API format. Returns {"user": summary, "repos": [...]}."""
        profile, summary = build_profile(gh)
        proba = self.classifier.predict_proba([profile])[0]
        proba = np.where(self.class_mask, proba, -1)
        vec = self.matcher.embed([profile])

        results = []
        for i in np.argsort(-proba)[:top_repos]:
            repo_id = self.classifier.classes_[i]
            results.append({
                "repo_id": repo_id,
                "url": self.repos.at[repo_id, "html_url"],
                "probability": float(proba[i]),
                "why": self.matcher.shared_terms(vec, self.repo_vecs[repo_id]),
                "issues": self._issues(vec, repo_id, top_issues),
            })
        return {"user": summary, "repos": results}

    def recommend_user(self, username, **kw):
        return self.recommend(load_user(username), **kw)

    def _issues(self, vec, repo_id, k):
        rows = self.issue_rows[repo_id]
        sub = self.issues.iloc[rows]
        s = self.matcher.similarity(vec, self.issue_matrix[rows])
        s = s + LABEL_BOOST * (sub["is_beginner_friendly"] | sub["is_help_wanted"]).to_numpy()
        out = []
        for j in np.argsort(-s)[:k]:
            row = sub.iloc[j]
            title = " ".join(row.title.split())
            if len(title) < 12:   # template-only titles like "Bug:" -> add the start of the body
                title = f"{title} {row.body_clean[:60]}…"
            tags = [t for t, f in [("good first issue", row.is_beginner_friendly),
                                   ("help wanted", row.is_help_wanted)] if f]
            out.append({"number": int(row.number), "title": title, "url": row.html_url,
                        "tags": tags, "why": self.matcher.shared_terms(vec, self.issue_matrix[rows[j]], n=4)})
        return out


def show(rec):
    """Print recommendations the way the app will show them."""
    u = rec["user"]
    print(f"Recommendations for {u['login']}  (languages: {u['top languages']}; merged PRs: {u['merged PRs']})\n")
    for n, r in enumerate(rec["repos"], 1):
        print(f"{n}. {r['repo_id']}")
        print(f"   Why: {', '.join(r['why'])}")
        print("   Issues to start with:")
        for i in r["issues"]:
            tags = f"  [{', '.join(i['tags'])}]" if i["tags"] else ""
            print(f"     • #{i['number']} {i['title'][:70]}{tags}")
        print()
