# Local API server

The FastAPI service connects the web client to the recommender. Follow the root [README](../README.md) to install dependencies, collect the dataset, and start the full app. From the repository root, start the API with:

```sh
uvicorn app.main:app --app-dir server --reload --host 127.0.0.1 --port 8000
```

The API needs the locally collected dataset under `ml/data/cleaned/` and a GitHub token in `ml/.env` for live profile requests. Check <http://127.0.0.1:8000/health> to confirm it started.

Manual recommendation requests (the interests form) are saved to PostgreSQL before the recommender runs. Configure `DATABASE_URL` in `ml/.env` for that mode. On the first manual submission, the service creates a `recommendation_submissions` table containing the submitted interests, language, and timestamp. GitHub profile recommendations do not use this database.

For a hosted frontend, set `FRONTEND_ORIGINS` to the frontend origin(s), comma-separated, for example `https://your-app.vercel.app`. The browser client also needs `VITE_API_BASE_URL` set to this API's public base URL at frontend build time.

GitHub profile requests accept a username or profile URL. To match a live profile, the user needs a public personal README in a repository named `username/username`; if the README is missing, the API clearly reports that and recommends the interests form. That is different from an unknown username, which gets a “GitHub user not found” error. The interests form uses the entered language and description instead of GitHub profile data.
