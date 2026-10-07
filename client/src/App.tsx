import { FormEvent, useState } from "react";
import { fetchRecommendations, type Recommendation } from "./services/api";

type InputMode = "github" | "text";

function GithubMark({ className = "size-5" }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
    >
      <path d="M12 .7a11.5 11.5 0 0 0-3.64 22.4c.58.1.79-.25.79-.56v-2.22c-3.22.7-3.9-1.37-3.9-1.37-.52-1.34-1.28-1.7-1.28-1.7-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.74-1.55-2.57-.3-5.27-1.28-5.27-5.69 0-1.26.45-2.28 1.18-3.09-.12-.29-.51-1.46.11-3.05 0 0 .97-.31 3.16 1.18a10.94 10.94 0 0 1 5.75 0c2.2-1.49 3.16-1.18 3.16-1.18.63 1.59.24 2.76.12 3.05.74.81 1.18 1.83 1.18 3.09 0 4.42-2.71 5.39-5.29 5.68.42.36.79 1.07.79 2.16v3.2c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .7Z" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg
      aria-hidden="true"
      className="size-[18px]"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-4-4" />
    </svg>
  );
}

function StarIcon() {
  return (
    <svg
      aria-hidden="true"
      className="size-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
    >
      <path d="m12 3 2.75 5.57 6.15.9-4.45 4.33 1.05 6.12L12 17.03l-5.5 2.89 1.05-6.12L3.1 9.47l6.15-.9L12 3Z" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg
      aria-hidden="true"
      className="size-4 transition-transform group-hover:translate-x-0.5"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export default function App() {
  const [mode, setMode] = useState<InputMode>("github");
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const switchMode = (nextMode: InputMode) => {
    setMode(nextMode);
    setQuery("");
    setSubmittedQuery("");
    setRecommendations([]);
    setError("");
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    const normalizedQuery = trimmedQuery.replace(/^@/, "");
    setSubmittedQuery(normalizedQuery);
    setError("");
    setRecommendations([]);
    setIsLoading(true);
    try {
      const result = await fetchRecommendations({ mode, query: normalizedQuery });
      setRecommendations(result.repos);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not load recommendations.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8f8f7] text-[#181817]">
      <header className="border-b border-black/[0.07] bg-[#f8f8f7]/90">
        <div className="mx-auto flex h-[72px] max-w-[1160px] items-center justify-between px-5 sm:px-8">
          <a
            href="#"
            className="flex items-center gap-2.5 text-[15px] font-semibold tracking-[-0.02em]"
            aria-label="Repos home"
          >
            <span className="grid size-8 place-items-center rounded-[10px] bg-[#181817] text-white">
              <GithubMark className="size-[17px]" />
            </span>
            Repo<span className="-ml-2.5 text-[#787873]">scope</span>
          </a>
          <span className="hidden text-[13px] text-[#8a8a84] sm:block">
            Find your next favorite project
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-[920px] px-5 pb-20 pt-16 sm:px-8 sm:pt-24">
        <section className="mx-auto max-w-[720px] text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-black/[0.08] bg-white px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#72726d] shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
            <span className="size-1.5 rounded-full bg-[#65a30d]" />
            Open source discovery
          </div>
          <h1 className="text-[40px] font-semibold leading-[1.05] tracking-[-0.045em] sm:text-[58px]">
            Repositories, picked
            <br />
            <span className="text-[#9b9b95]">for how you build.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-[540px] text-[15px] leading-7 text-[#71716c] sm:text-base">
            Share your GitHub profile or describe what you&apos;re looking for.
            We&apos;ll surface open-source projects worth exploring.
          </p>
        </section>

        <section className="mx-auto mt-10 max-w-[720px] sm:mt-12">
          <div className="rounded-[20px] border border-black/[0.08] bg-white p-2 shadow-[0_14px_45px_rgba(27,27,24,0.07)]">
            <div className="flex gap-1 border-b border-black/[0.06] px-2 pb-2">
              <button
                type="button"
                onClick={() => switchMode("github")}
                className={`flex flex-1 items-center justify-center gap-2 rounded-[10px] px-3 py-2.5 text-[13px] font-medium transition-colors ${
                  mode === "github"
                    ? "bg-[#f0f0ed] text-[#20201e]"
                    : "text-[#898984] hover:text-[#333330]"
                }`}
              >
                <GithubMark className="size-4" />
                GitHub profile
              </button>
              <button
                type="button"
                onClick={() => switchMode("text")}
                className={`flex flex-1 items-center justify-center gap-2 rounded-[10px] px-3 py-2.5 text-[13px] font-medium transition-colors ${
                  mode === "text"
                    ? "bg-[#f0f0ed] text-[#20201e]"
                    : "text-[#898984] hover:text-[#333330]"
                }`}
              >
                <SearchIcon />
                Describe your interests
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-2 sm:p-3">
              <label
                htmlFor="recommendation-query"
                className="mb-2 block text-[12px] font-medium text-[#6f6f6a]"
              >
                {mode === "github"
                  ? "GitHub username"
                  : "What are you interested in?"}
              </label>
              <div className="flex flex-col gap-2 sm:flex-row">
                <div className="relative flex-1">
                  {mode === "github" && (
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[15px] text-[#aaa9a3]">
                      @
                    </span>
                  )}
                  <input
                    id="recommendation-query"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder={
                      mode === "github"
                        ? "your-github-handle"
                        : "e.g. minimal tools for building an AI app"
                    }
                    className={`h-12 w-full rounded-[11px] border border-black/[0.09] bg-[#fafaf8] pr-4 text-[14px] text-[#252522] outline-none transition placeholder:text-[#aeaea8] focus:border-[#77776f] focus:bg-white focus:ring-2 focus:ring-black/[0.04] ${
                      mode === "github" ? "pl-8" : "pl-4"
                    }`}
                  />
                </div>
                <button
                  type="submit"
                  disabled={!query.trim() || isLoading}
                  className="group flex h-12 items-center justify-center gap-2 rounded-[11px] bg-[#1d1d1b] px-5 text-[13px] font-medium text-white transition hover:bg-black disabled:cursor-not-allowed disabled:opacity-35"
                >
                  {isLoading ? "Finding..." : "Find repositories"}
                  <ArrowIcon />
                </button>
              </div>
            </form>
          </div>
          {error && <p className="mt-3 text-center text-[12px] text-[#b42318]">{error}</p>}
          <p className="mt-3 text-center text-[11px] text-[#a0a09a]">
            No sign-in required. We only use public GitHub data.
          </p>
        </section>

        {recommendations.length > 0 ? (
          <section className="mt-16" aria-live="polite">
            <div className="mb-5 flex items-end justify-between gap-4">
              <div>
                <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#999993]">
                  Curated for you
                </p>
                <h2 className="text-[22px] font-semibold tracking-[-0.03em]">
                  Recommended repositories
                </h2>
              </div>
              <p className="hidden max-w-64 truncate text-[12px] text-[#969690] sm:block">
                Based on{" "}
                <span className="font-medium text-[#555550]">
                  {mode === "github" ? `@${submittedQuery}` : submittedQuery}
                </span>
              </p>
            </div>

            <div className="overflow-hidden rounded-[16px] border border-black/[0.08] bg-white">
              {recommendations.map((repository, index) => (
                <article
                  key={`${repository.owner}/${repository.name}`}
                  className={`group relative p-5 transition-colors hover:bg-[#fbfbf9] sm:p-6 ${
                    index !== recommendations.length - 1
                      ? "border-b border-black/[0.07]"
                      : ""
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div className="mt-0.5 hidden size-10 shrink-0 place-items-center rounded-[11px] border border-black/[0.07] bg-[#f5f5f2] text-[#686862] sm:grid">
                      <GithubMark className="size-[18px]" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-4">
                        <div className="min-w-0">
                          <p className="truncate text-[11px] text-[#9a9a94]">
                            {repository.owner}
                          </p>
                          <h3 className="mt-0.5 text-[17px] font-semibold tracking-[-0.02em]">
                            {repository.name}
                          </h3>
                        </div>
                        <span className="shrink-0 rounded-full bg-[#eef6de] px-2.5 py-1 text-[10px] font-semibold text-[#527c10]">
                          {Math.round(repository.probability * 100)}% match
                        </span>
                      </div>
                      <p className="mt-2 max-w-[650px] text-[13px] leading-6 text-[#70706b]">
                        {repository.description}
                      </p>
                      <div className="mt-4 flex items-center justify-between">
                        <div className="flex items-center gap-4 text-[11px] text-[#898984]">
                          <span className="flex items-center gap-1.5">
                            <span
                              className="size-2 rounded-full"
                              style={{ backgroundColor: repository.language ? "#3178c6" : "#aaa9a3" }}
                            />
                            {repository.language}
                          </span>
                          <span className="flex items-center gap-1">
                            <StarIcon />
                            {repository.stars.toLocaleString()}
                          </span>
                        </div>
                        <a
                          href={repository.url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1.5 text-[12px] font-medium text-[#5f5f5a] transition-colors hover:text-black"
                          aria-label={`View ${repository.owner}/${repository.name} on GitHub`}
                        >
                          View repo
                          <ArrowIcon />
                        </a>
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>
        ) : (
          <div className="mx-auto mt-16 flex max-w-[720px] items-center gap-4 border-t border-black/[0.06] pt-5 text-[11px] text-[#aaa9a3]">
            <span className="shrink-0">Built for curious developers</span>
            <span className="h-px flex-1 bg-black/[0.05]" />
            <span className="shrink-0">Updated from GitHub</span>
          </div>
        )}
      </main>
    </div>
  );
}
