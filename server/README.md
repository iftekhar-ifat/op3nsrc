# API server

The FastAPI service powers the web client and the recommender. Start it from the repository root with:

```sh
uvicorn app.main:app --app-dir server --reload
```

Manual recommendation requests are saved to PostgreSQL before the recommender runs. Install `server/requirements.txt` and set `DATABASE_URL` to a PostgreSQL connection string in the server environment. The service creates the `recommendation_submissions` table on the first manual submission. Each row stores the submitted interests, language, and timestamp.

For a hosted frontend, set `FRONTEND_ORIGINS` to the frontend origin(s), comma-separated, for example `https://your-app.vercel.app`. The browser client also needs `VITE_API_BASE_URL` set to this API's public base URL at frontend build time.

GitHub profile requests accept a username or profile URL. A personal README in the matching `username/username` repository is required to build a profile; if it is missing, the API asks the user to provide a language and interests manually. Public profile reads use the GitHub API client, which requires `GITHUB_TOKEN` in the project environment.
