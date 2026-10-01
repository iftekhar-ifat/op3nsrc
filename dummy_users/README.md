# Dummy GitHub users

Fictional users for building and demoing the app before the live GitHub fetch exists. Each file has the
**same structure as the GitHub REST API responses**, so the live fetch only has to produce the same keys
and nothing downstream changes.

| Key             | GitHub API call it mirrors                                               |
| --------------- | ------------------------------------------------------------------------ |
| `user`          | `GET /users/{username}`                                                  |
| `repos`         | `GET /users/{username}/repos?type=owner&sort=pushed&per_page=100`        |
| `languages`     | `GET /repos/{owner}/{repo}/languages`, one per repo, keyed by `full_name` |
| `pull_requests` | `GET /search/issues?q=author:{username}+type:pr+is:merged`               |
| `issues`        | `GET /search/issues?q=author:{username}+type:issue`                      |
| `starred`       | `GET /users/{username}/starred`                                          |

`_dummy`, `_note` and `_sources` are metadata for us; a live fetch would leave them out.

## Personas

| File                   | Who                                         | Covers                                                         |
| ---------------------- | ------------------------------------------- | -------------------------------------------------------------- |
| `demo-alex-py.json`    | Python backend dev (FastAPI, pydantic, SQL) | 7 repos incl. **one fork** (should be ignored), 3 merged PRs, 2 issues, 5 starred |
| `demo-sam-rust.json`   | Rust / Go systems dev (tokio, clap, k8s)    | 5 repos, 3 merged PRs, 1 issue, 4 starred                      |
| `demo-jordan-web.json` | Beginner frontend dev (HTML, React, Vite)   | 4 small repos, **no merged PRs** (cold start), 1 issue, 4 starred |

The logins (`demo-…`) are made up. PR/issue numbers in the target repos are fictional too; only the
repo names refer to projects in our pool.
