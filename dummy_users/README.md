# Dummy GitHub users

Fictional users for building and demoing the app before the live GitHub fetch exists. Each file holds
**GitHub REST API responses trimmed to the fields the profile uses**, so the live fetch only has to
produce the same keys and nothing downstream changes.

| Key             | GitHub API call it mirrors                                  | Fields kept                                                  |
| --------------- | ----------------------------------------------------------- | ------------------------------------------------------------ |
| `user`          | `GET /users/{username}`                                     | `login`, `name`                                              |
| `repos`         | `GET /users/{username}/repos?type=owner&sort=pushed`        | `name`, `full_name`, `description`, `topics`, `language`, `fork` |
| `languages`     | `GET /repos/{owner}/{repo}/languages`, one per repo, keyed by `full_name` | bytes of code per language                     |
| `pull_requests` | `GET /search/issues?q=author:{username}+type:pr+is:merged`  | `total_count`; per PR `title`, `body`, `repository_url`      |

`_dummy`, `_note` and `_sources` are metadata for us; a live fetch would leave them out.

## Personas

| File                   | Who                                         | Covers                                                    |
| ---------------------- | ------------------------------------------- | --------------------------------------------------------- |
| `demo-alex-py.json`    | Python backend dev (FastAPI, pydantic, SQL) | 7 repos incl. **one fork** (should be ignored), 3 merged PRs |
| `demo-sam-rust.json`   | Rust / Go systems dev (tokio, clap, k8s)    | 5 repos, 3 merged PRs                                     |
| `demo-jordan-web.json` | Beginner frontend dev (HTML, React, Vite)   | 4 small repos, **no merged PRs** (the newcomer case)      |

The logins (`demo-…`) are made up. PR numbers in the target repos are fictional too; only the repo names
refer to projects in our pool.
