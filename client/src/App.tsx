import { FormEvent, useEffect, useState } from "react";
import { fetchRecommendations, type Recommendation } from "./services/api";
import appLogo from "../op3nsrc_lighttheme.png";

type InputMode = "github" | "text";
type UiLanguage = "en" | "fi";

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

function CheckIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="size-4">
      <path d="m5 12 4 4L19 6" />
    </svg>
  );
}

function PlayIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor" className="size-4">
      <path d="M8 5.5a1 1 0 0 1 1.52-.85l9.1 5.5a2.15 2.15 0 0 1 0 3.7l-9.1 5.5A1 1 0 0 1 8 18.5v-13Z" />
    </svg>
  );
}

function FeatureIcon({ kind }: { kind: "match" | "projects" | "issues" | "growth" }) {
  const paths = {
    match: <><circle cx="10.5" cy="13.5" r="6.5" /><path d="m15 9 6-6m-5 1h4v4M7 14l2.2 2.2L14 11" /></>,
    projects: <><circle cx="12" cy="12" r="9" /><path d="m14.7 9.3-2.1 5.4-5.3 2.1 2.1-5.4 5.3-2.1ZM12 3v2m9 7h-2M5 12H3m9 9v-2" /></>,
    issues: <><path d="M9 6h12M9 12h12M9 18h12" /><circle cx="4" cy="6" r="1" /><circle cx="4" cy="12" r="1" /><circle cx="4" cy="18" r="1" /></>,
    growth: <><path d="M5 16.5c3.2-6.4 7.3-9.7 14-10.5-.8 6.7-4.1 10.8-10.5 14L5 16.5Z" /><path d="M8 18c0-3 2-5 5-6m-7 7-2 2m11-12h.01" /></>,
  };
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="size-6">
      {paths[kind]}
    </svg>
  );
}

export default function App() {
  const [uiLanguage, setUiLanguage] = useState<UiLanguage>(() => (localStorage.getItem("op3nsrc-language") === "fi" ? "fi" : "en"));
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("op3nsrc-theme") === "dark");
  const [mode, setMode] = useState<InputMode>("github");
  const [query, setQuery] = useState("");
  const [language, setLanguage] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const fi = uiLanguage === "fi";

  useEffect(() => {
    document.documentElement.lang = uiLanguage;
    localStorage.setItem("op3nsrc-language", uiLanguage);
    localStorage.setItem("op3nsrc-theme", darkMode ? "dark" : "light");
  }, [uiLanguage, darkMode]);

  useEffect(() => {
    document.documentElement.dataset.theme = darkMode ? "dark" : "light";
  }, [darkMode]);

  useEffect(() => {
    if (!recommendations.length) return;
    const cards = Array.from(document.querySelectorAll<HTMLElement>(".recommendation-card"));
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          cards.forEach((card) => card.classList.toggle("recommendation-card-active", card === entry.target));
        }
      }
    }, { rootMargin: "-35% 0px -35% 0px", threshold: 0.15 });
    cards.forEach((card) => observer.observe(card));
    return () => observer.disconnect();
  }, [recommendations]);

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

    const normalizedQuery = mode === "github"
      ? trimmedQuery.replace(/^https?:\/\/github\.com\//i, "").replace(/^@/, "").replace(/\/$/, "")
      : trimmedQuery;
    setSubmittedQuery(normalizedQuery);
    setError("");
    setRecommendations([]);
    setIsLoading(true);
    try {
      const result = await fetchRecommendations({ mode, query: normalizedQuery, language });
      setRecommendations(result.repos);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not load recommendations.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`site-background min-h-screen text-[#181817] ${darkMode ? "theme-dark" : ""}`}>
      <header className="sticky top-0 z-20 border-b border-transparent bg-transparent backdrop-blur-sm">
        <div className="flex min-h-[68px] w-full items-center justify-between gap-4 px-4 sm:min-h-[72px] sm:px-8 lg:px-12">
          <a
            href="#"
            className="flex shrink-0 items-center gap-2 text-[15px] font-semibold tracking-[-0.03em]"
            aria-label="OpenSRC home"
          >
            <img src={appLogo} alt="" className="size-10 shrink-0 object-contain" />
            <span>Op3nSRC</span>
          </a>
          <nav aria-label={fi ? "Päänavigaatio" : "Main navigation"} className="flex items-center gap-2 text-[13px] sm:gap-5">
            <div className="hidden items-center gap-5 md:flex">
              <a href="#how-it-works" className="text-[#777770] hover:text-black">{fi ? "Näin se toimii" : "How it works"}</a>
              <a href="#features" className="text-[#777770] hover:text-black">{fi ? "Ominaisuudet" : "Features"}</a>
              <a href="#recommendation" className="text-[#777770] hover:text-black">{fi ? "Tutustu" : "Explore"}</a>
              <a href="#about" className="text-[#777770] hover:text-black">{fi ? "Tietoa" : "About"}</a>
            </div>
            <button type="button" className="ui-control" onClick={() => setUiLanguage(uiLanguage === "en" ? "fi" : "en")} aria-label={fi ? "Vaihda englantiin" : "Switch to Finnish"}>{fi ? "FI" : "EN"}</button>
            <button type="button" className="ui-control theme-control" onClick={() => setDarkMode(!darkMode)} aria-label={darkMode ? (fi ? "Vaihda vaaleaan tilaan" : "Switch to light mode") : (fi ? "Vaihda tummaan tilaan" : "Switch to dark mode")} title={darkMode ? (fi ? "Vaalea tila" : "Light mode") : (fi ? "Tumma tila" : "Dark mode")}>{darkMode ? "☀" : "☾"}<span className="hidden sm:inline">{darkMode ? (fi ? "Vaalea" : "Light") : (fi ? "Tumma" : "Dark")}</span></button>
            <a href="#recommendation" className="interactive-cta whitespace-nowrap rounded-full bg-[#263e30] px-3 py-2 text-[12px] font-medium text-white shadow-[0_4px_14px_rgba(38,62,48,0.16)] sm:px-4 sm:text-[13px]"><span className="sm:hidden">{fi ? "Aloita" : "Get started"}</span><span className="hidden sm:inline">{fi ? "Hae suosituksia" : "Get recommendations"}</span></a>
          </nav>
        </div>
      </header>

      <main id="main-content" className="mx-auto max-w-[1600px] px-5 pb-20 sm:px-8 lg:px-12">
        <section className="hero-layout relative isolate" aria-labelledby="page-title">
          <div className="hero-copy">
            <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#dce8d8] bg-white/75 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#58705c]"><span className="size-1.5 rounded-full bg-[#65a30d]" />{fi ? "Avoimen lähdekoodin löytöretki" : "Open source discovery"}</p>
            <h1 id="page-title" className="text-[clamp(2.5rem,5.5vw,5.2rem)] font-semibold leading-[1.02] tracking-[-0.055em]">{fi ? "Löydä avoimen lähdekoodin projekteja, jotka " : "Find open source that "}<span className="hero-title-accent">{fi ? "sopivat juuri sinulle." : "feels made for you."}</span></h1>
            <p className="mt-6 max-w-[600px] text-[15px] leading-7 text-[#58665a] sm:text-[18px]">{fi ? "Op3nSRC yhdistää kiinnostuksen kohteesi tai GitHub-profiilisi projekteihin, joihin voit osallistua, ja auttaa löytämään sopivia tehtäviä." : "Op3nSRC matches your developer interests or GitHub profile with projects you can contribute to, then points you toward issues to get started."}</p>
            <div className="mt-7 flex flex-wrap gap-3">
              <a href="#recommendation" className="interactive-cta group inline-flex min-h-12 items-center justify-center gap-2 rounded-[12px] bg-[#263e30] px-6 text-[14px] font-semibold text-white shadow-[0_8px_22px_rgba(45,83,58,0.18)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#527c10]">{fi ? "Tutustu suosituksiin" : "Explore recommendations"} <ArrowIcon /></a>
              <a href="#how-it-works" className="inline-flex min-h-12 items-center gap-2 rounded-[12px] border border-[#dfe5dd] bg-white/70 px-5 text-[14px] font-medium text-[#3d4940] transition hover:bg-white"><PlayIcon />{fi ? "Katso miten se toimii" : "See how it works"}</a>
            </div>
            <ul className="mt-7 flex flex-wrap gap-x-6 gap-y-3 text-[12px] text-[#667269] sm:text-[13px]">
              {(fi ? ['Kiinnostuksiesi mukaan', 'Valikoituja avoimen lähdekoodin projekteja', 'Aloittelijaystävällisiä tehtäviä'] : ['Personalized to your interests', 'Curated open source projects', 'Beginner-friendly issues']).map((label) => <li key={label} className="inline-flex items-center gap-2"><span className="grid size-6 place-items-center rounded-full border border-[#bce9c2] bg-[#effbf0] text-[#45a95d]"><CheckIcon /></span>{label}</li>)}
            </ul>
          </div>
          <div className="hero-visual" aria-label="Illustration of how OpenSRC matches developers to projects">
            <div className="hero-orbit" />
            <div className="hero-orbit-dot orbit-dot-one" /><div className="hero-orbit-dot orbit-dot-two" /><div className="hero-orbit-dot orbit-dot-three" />
            <img src={appLogo} alt="OpenSRC mascot" className="hero-mascot" />
            <div className="hero-float-card profile-card"><div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-full bg-[#f1f1f4]"><GithubMark className="size-6" /></span><div><b>{fi ? "GitHub-profiilisi" : "Your GitHub"}</b><p>{fi ? "Kiinnostukset · Taidot · Toiminta" : "Interests · Skills · Activity"}</p></div></div><div className="mini-bars"><i/><i/><i/><i/></div></div>
            <div className="hero-float-card matches-card"><b>{fi ? "Sopivat projektit" : "Matched projects"}</b><p><span/>AI / ML</p><p><span/>{fi ? "Verkkokehitys" : "Web development"}</p><p><span/>{fi ? "Data-analytiikka" : "Data science"}</p></div>
            <div className="hero-float-card issues-card"><div className="flex items-center gap-2"><span className="issue-check"><CheckIcon /></span><b>{fi ? "Hyvät aloitustehtävät" : "Good first issues"}</b></div><p>{fi ? "Korjaa kirjoitusvirhe" : "Fix typo in docs"} <em>good first issue</em></p><p>{fi ? "Paranna virheenkäsittelyä" : "Improve error handling"} <em>help wanted</em></p><p>{fi ? "Lisää testitapauksia" : "Add test cases"} <em>beginner</em></p></div>
          </div>
        </section>

        <section id="features" className="feature-strip scroll-mt-24" aria-label="OpenSRC benefits">
          {([
            ['match', fi ? 'Henkilökohtaiset osumat' : 'Personalized matching', fi ? 'Kiinnostustesi tai GitHub-profiilisi perusteella' : 'Based on your interests or GitHub profile'],
            ['projects', fi ? 'Valikoidut projektit' : 'Curated projects', fi ? 'Laadukkaita ja aktiivisia avoimen lähdekoodin projekteja' : 'High-quality, active open source repositories'],
            ['issues', fi ? 'Käytännön suositukset' : 'Actionable recommendations', fi ? 'Ehdotuksia tehtävistä, joista voit aloittaa' : 'Get suggested issues to start contributing'],
            ['growth', fi ? 'Tue kehittymistäsi' : 'Support your growth', fi ? 'Kehitä taitojasi ja vaikuta projekteihin' : 'Build skills and make real impact'],
          ] as const).map(([kind, title, description]) => <article key={kind} className="feature-item"><span className={`feature-icon feature-${kind}`}><FeatureIcon kind={kind} /></span><div><h2>{title}</h2><p>{description}</p></div></article>)}
        </section>

        <section id="how-it-works" className="how-section scroll-mt-24" aria-labelledby="how-title">
          <div className="how-copy"><p className="section-kicker">{fi ? "Aloita tästä" : "Get started"}</p><h2 id="how-title">{fi ? "Näin se toimii" : "How it works"}</h2><p className="how-intro">{fi ? "Kiinnostuksen kohteista ensimmäiseen kontribuutioon muutamalla helpolla askeleella." : "Go from your interests to your first contribution in a few simple steps."}</p>
            <div className="step-grid">{[
              ['01', fi ? 'Kerro itsestäsi' : 'Tell us about you', fi ? 'Yhdistä GitHub tai kerro kiinnostuksen kohteistasi.' : 'Connect your GitHub or select your interests.'],
              ['02', fi ? 'Saat henkilökohtaisia osumia' : 'Get personalized matches', fi ? 'Etsimme taitoihisi ja kiinnostuksiisi sopivia projekteja.' : 'We find projects that fit your skills and interests.'],
              ['03', fi ? 'Tutki tehtäväsuosituksia' : 'Explore recommended issues', fi ? 'Löydä sopivia ja aloittelijaystävällisiä tehtäviä.' : 'See curated, beginner-friendly issues to start with.'],
              ['04', fi ? 'Aloita osallistuminen' : 'Start contributing', fi ? 'Tee ensimmäinen kontribuutiosi ja kehity eteenpäin.' : 'Make your first contribution and grow from there.'],
            ].map(([number, title, description], index) => <article key={number} className="step-item"><span className={`step-icon step-icon-${index}`}><FeatureIcon kind={(['match','projects','issues','growth'] as const)[index]} /></span><h3>{number}. {title}</h3><p>{description}</p></article>)}</div>
          </div>
          <div className="project-stack" aria-label="Example project recommendations"><div className="stack-glow"/><article className="project-example project-example-one"><div className="project-emoji">🦜🔗</div><div className="project-example-body"><div className="flex items-center justify-between gap-2"><b>LangChain</b><span className="project-stars"><StarIcon />52.3k</span></div><p>Build with LLMs using LangChain.</p><div className="project-tags"><span>Python</span><span>AI</span><span>Good first issue</span></div></div></article><article className="project-example project-example-two"><div className="project-emoji fastapi-mark">ϟ</div><div className="project-example-body"><div className="flex items-center justify-between gap-2"><b>FastAPI</b><span className="project-stars">★ 74.1k</span></div><p>Modern, fast web framework for Python.</p><div className="project-tags"><span>Python</span><span>Web</span><span>Help wanted</span></div></div></article></div>
        </section>

      <div id="recommendation" className="scroll-mt-24">
        <section className="mx-auto max-w-[720px] text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-black/[0.08] bg-white px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#72726d] shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
            <span className="size-1.5 rounded-full bg-[#65a30d]" />
            {fi ? "Avoimen lähdekoodin löytöretki" : "Open source discovery"}
          </div>
            <h2 className="text-[34px] font-semibold leading-[1.05] tracking-[-0.045em] sm:text-[48px]">
            {fi ? "Projektit valittu" : "Repositories, picked"}
            <br />
            <span className="text-[#66816a]">{fi ? "tapaasi rakentaa." : "for how you build."}</span>
            </h2>
          <p className="mx-auto mt-6 max-w-[540px] text-[15px] leading-7 text-[#71716c] sm:text-base">
            {fi ? "Jaa GitHub-profiilisi tai kuvaile, mitä etsit. Löydämme kiinnostavia avoimen lähdekoodin projekteja." : "Share your GitHub profile or describe what you&apos;re looking for. We&apos;ll surface open-source projects worth exploring."}
          </p>
        </section>

        <section className="mx-auto mt-10 max-w-[720px] sm:mt-12">
          <div className="rounded-[20px] border border-black/[0.08] bg-white p-2 shadow-[0_14px_45px_rgba(27,27,24,0.07)]">
            <div className="flex gap-1 border-b border-black/[0.06] px-2 pb-2">
              <button
                type="button"
                onClick={() => switchMode("github")}
                className={`mode-tab flex min-h-11 flex-1 items-center justify-center gap-2 rounded-[10px] px-2 py-2.5 text-[12px] font-medium sm:px-3 sm:text-[13px] ${
                  mode === "github"
                    ? "mode-tab-active"
                    : "mode-tab-inactive"
                }`}
                aria-pressed={mode === "github"}
              >
                <GithubMark className="size-4" />
                {fi ? "GitHub-profiili" : "GitHub profile"}
              </button>
              <button
                type="button"
                onClick={() => switchMode("text")}
                className={`mode-tab flex min-h-11 flex-1 items-center justify-center gap-2 rounded-[10px] px-2 py-2.5 text-[12px] font-medium sm:px-3 sm:text-[13px] ${
                  mode === "text"
                    ? "mode-tab-active"
                    : "mode-tab-inactive"
                }`}
                aria-pressed={mode === "text"}
              >
                <SearchIcon />
                <span className="sm:hidden">{fi ? "Kiinnostukset" : "Interests"}</span>
                <span className="hidden sm:inline">{fi ? "Kuvaile kiinnostuksen kohteitasi" : "Describe your interests"}</span>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-2 sm:p-3">
              <label
                htmlFor="recommendation-query"
                className="mb-2 block text-[12px] font-medium text-[#6f6f6a]"
              >
                {mode === "github"
                  ? (fi ? "GitHub-käyttäjänimi tai profiilin URL" : "GitHub username or profile URL")
                  : (fi ? "Mistä olet kiinnostunut?" : "What are you interested in?")}
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
                    required
                    aria-required="true"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder={
                      mode === "github"
                        ? "your-github-handle"
                        : (fi ? "Esim. kevyet työkalut tekoälysovelluksen rakentamiseen" : "e.g. minimal tools for building an AI app")
                    }
                    className={`h-12 w-full rounded-[11px] border border-black/[0.09] bg-[#fafaf8] pr-4 text-[14px] text-[#252522] outline-none transition placeholder:text-[#aeaea8] focus:border-[#77776f] focus:bg-white focus:ring-2 focus:ring-black/[0.04] ${
                      mode === "github" ? "pl-8" : "pl-4"
                    }`}
                  />
                </div>
                <button
                  type="submit"
                  disabled={!query.trim() || (mode === "text" && !language.trim()) || isLoading}
                  className="find-repositories group flex h-12 items-center justify-center gap-2 rounded-[11px] px-5 text-[13px] font-semibold text-white disabled:cursor-not-allowed"
                >
                  {isLoading ? (fi ? "Etsitään..." : "Finding...") : (fi ? "Etsi projekteja" : "Find repositories")}
                  <ArrowIcon />
                </button>
              </div>
              {mode === "text" && <div className="mt-3">
                <label htmlFor="language" className="mb-2 block text-[12px] font-medium text-[#6f6f6a]">{fi ? "Ensisijainen ohjelmointikieli" : "Primary programming language"}</label>
                <input id="language" value={language} onChange={(event) => setLanguage(event.target.value)} placeholder="e.g. Python" required aria-required="true" className="h-12 w-full rounded-[11px] border border-black/[0.09] bg-[#fafaf8] px-4 text-[14px] outline-none focus:border-[#77776f] focus:bg-white focus:ring-2 focus:ring-black/[0.04]" />
              </div>}
            </form>
          </div>
          {error && <p role="alert" className="mt-3 text-center text-[12px] text-[#b42318]">{error}</p>}
          <p className="mt-3 text-center text-[11px] text-[#a0a09a]">
            {fi ? "Kirjautumista ei tarvita. Kirjoita kiinnostuksen kohteet ja ohjelmointikieli englanniksi; suositukset näytetään englanniksi." : "No sign-in required. Enter your interests and programming language in English; recommendations are shown in English."}
          </p>
        </section>

        {recommendations.length > 0 ? (
          <section className="mt-16" aria-live="polite">
            <div className="mb-5 flex items-end justify-between gap-4">
              <div>
                <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#999993]">{fi ? "Sinulle valitut" : "Curated for you"}</p>
                <h2 className="text-[22px] font-semibold tracking-[-0.03em]">{fi ? "Suositellut projektit" : "Recommended repositories"}</h2>
              </div>
            </div>

            <div className="results-for mb-4 rounded-2xl border border-emerald-200/70 bg-emerald-50 px-5 py-4 shadow-sm" aria-live="polite">
              <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-emerald-700">{mode === "github" ? (fi ? "Suositukset käyttäjälle" : "Recommendations for") : (fi ? "Sinun vastauksiesi perusteella" : "Recommendations based on your answers")}</p>
              <p className="mt-1 text-lg font-semibold text-[#203b2a]">{mode === "github" ? `@${submittedQuery}` : (fi ? "Kiinnostuksen kohteidesi ja ohjelmointikielesi perusteella" : "Your interests and programming language")}</p>
              {mode === "text" && <p className="mt-1 text-sm text-[#526357]">{fi ? "Nämä projektit sopivat kuvailemaasi osaamiseen ja kiinnostukseen." : "These projects were selected to match the interests and language you shared."}</p>}
            </div>

            <div className="overflow-hidden rounded-[16px] border border-black/[0.08] bg-white">
              {recommendations.map((repository, index) => (
                <article
                  key={`${repository.owner}/${repository.name}`}
                  className={`recommendation-card group relative p-5 transition-colors hover:bg-[#fbfbf9] sm:p-6 ${
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
                          {Math.round(repository.probability * 100)}% {fi ? "osuma" : "match"}
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
                          {fi ? "Avaa projekti" : "View repo"}
                          <ArrowIcon />
                        </a>
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>
        ) : null}
      </div>
      </main>
      <footer id="about" className="mx-auto flex max-w-[1600px] items-center gap-5 px-5 pb-8 pt-2 text-[11px] text-[#748275] sm:px-8 lg:px-12">
        <span className="shrink-0">{fi ? "Tehty uteliaille kehittäjille" : "Built for curious developers"}</span>
        <span aria-hidden="true" className="h-px flex-1 bg-[#cbd8ca]" />
      </footer>
    </div>
  );
}
