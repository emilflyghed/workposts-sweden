import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";
import ThemeToggle from "./components/ThemeToggle.jsx";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const normaliseId = (value) => String(value);

const formatDate = (value) => {
  if (!value) return "–";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("sv-SE");
};

const formatEmploymentType = (value) => {
  if (!value) return "Okänd anställning";
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

function useSavedJobs() {
  const [savedIds, setSavedIds] = useState(() => {
    try {
      const raw = localStorage.getItem("savedJobs");
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem("savedJobs", JSON.stringify(savedIds));
  }, [savedIds]);

  const isSaved = (id) => savedIds.includes(normaliseId(id));

  const toggleSave = (id) => {
    const key = normaliseId(id);
    setSavedIds((prev) =>
      prev.includes(key) ? prev.filter((value) => value !== key) : [...prev, key]
    );
  };

  return { savedIds, isSaved, toggleSave };
}

function Navbar() {
  return (
    <nav className="bg-white/80 backdrop-blur border-b border-slate-200 dark:bg-slate-900/60 dark:border-slate-800">
      <div className="container mx-auto flex items-center justify-between px-4 py-3">
        <Link
          to="/"
          className="text-xl font-semibold text-indigo-700 hover:text-indigo-800 dark:text-indigo-300 dark:hover:text-indigo-200"
        >
          JobbSök
        </Link>
        <div className="flex items-center gap-4">
          <Link to="/" className="nav-link">
            Hem
          </Link>
          <Link to="/saved" className="nav-link">
            Sparade
          </Link>
          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}

function JobCard({ job, onSave, saved }) {
  const navigate = useNavigate();
  const categories = Array.isArray(job.categories) ? job.categories.slice(0, 6) : [];

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">{job.title}</h3>
          <p className="text-slate-600 dark:text-slate-400">
            {job.company || "Okänt företag"} · {job.location || "Okänd plats"} · {formatEmploymentType(job.employment_type)}
          </p>
        </div>
        <button
          onClick={() => onSave(job.id)}
          className={`rounded-md px-3 py-1 text-sm ${
            saved
              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          }`}
          aria-pressed={saved}
        >
          {saved ? "Sparad" : "Spara"}
        </button>
      </div>
      {categories.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {categories.map((tag) => (
            <span key={tag} className="chip">
              {tag}
            </span>
          ))}
        </div>
      )}
      <p className="mt-3 line-clamp-3 text-slate-700 dark:text-slate-200">
        {job.summary || job.description || "Ingen beskrivning tillgänglig."}
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
        <span>Källa: {job.source}</span>
        {job.published_at && <span>Publicerad: {formatDate(job.published_at)}</span>}
        {job.last_application_date && (
          <span>Sista ansökan: {formatDate(job.last_application_date)}</span>
        )}
      </div>
      <div className="mt-4 flex gap-3">
        <button onClick={() => navigate(`/job/${job.id}`)} className="btn btn-primary">
          Läs mer
        </button>
        {job.url && (
          <a href={job.url} target="_blank" rel="noreferrer" className="btn-secondary">
            Till annons
          </a>
        )}
      </div>
    </div>
  );
}

function JobSearch({ jobs, onSearch, loading, scraping, error, lastQuery }) {
  const [title, setTitle] = useState(lastQuery.title ?? "");
  const [location, setLocation] = useState(lastQuery.location ?? "");
  const { isSaved, toggleSave } = useSavedJobs();

  useEffect(() => {
    setTitle(lastQuery.title ?? "");
    setLocation(lastQuery.location ?? "");
  }, [lastQuery]);

  const handleSubmit = (event) => {
    event.preventDefault();
    onSearch({ title, location });
  };

  const resultInfo = useMemo(() => {
    if (loading || scraping) return "Uppdaterar resultat …";
    if (!jobs.length) return "Inga jobb matchar nuvarande filter.";
    return `${jobs.length} jobb hämtade.`;
  }, [jobs.length, loading, scraping]);

  return (
    <div className="container mx-auto max-w-6xl px-4 py-6">
      <form onSubmit={handleSubmit} className="card">
        <div className="grid gap-3 sm:grid-cols-[2fr_2fr_auto]">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Sök titel eller företag"
            className="w-full rounded-md border border-slate-300 bg-white/90 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-300 dark:bg-slate-800 dark:border-slate-700"
          />
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Plats (t.ex. Stockholm)"
            className="w-full rounded-md border border-slate-300 bg-white/90 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-300 dark:bg-slate-800 dark:border-slate-700"
          />
          <button
            type="submit"
            className="btn btn-primary w-full sm:w-auto"
            disabled={loading || scraping}
          >
            {scraping ? "Hämtar…" : "Sök och uppdatera"}
          </button>
        </div>
        <div className="mt-3 text-sm text-slate-500 dark:text-slate-400">{resultInfo}</div>
        {error && (
          <div className="mt-3 rounded-md border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/60 dark:text-rose-200">
            {error}
          </div>
        )}
      </form>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {jobs.map((job) => (
          <JobCard key={job.id} job={job} saved={isSaved(job.id)} onSave={toggleSave} />
        ))}
        {!jobs.length && !loading && !scraping && (
          <p className="text-center text-slate-600 dark:text-slate-400">
            Inga jobb hittades. Prova en annan sökning.
          </p>
        )}
      </div>
    </div>
  );
}

function JobDetailPage({ jobs, fetchJob }) {
  const { id } = useParams();
  const jobId = Number(id);
  const { isSaved, toggleSave } = useSavedJobs();
  const [job, setJob] = useState(() => jobs.find((item) => item.id === jobId));
  const [loading, setLoading] = useState(!job);
  const [error, setError] = useState("");

  useEffect(() => {
    const existing = jobs.find((item) => item.id === jobId);
    if (existing) {
      setJob(existing);
      setLoading(false);
      setError("");
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError("");
    fetchJob(jobId)
      .then((data) => {
        if (!cancelled) setJob(data);
      })
      .catch(() => {
        if (!cancelled) setError("Jobbet kunde inte hämtas.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [fetchJob, jobId, jobs]);

  if (loading) {
    return (
      <div className="container mx-auto max-w-3xl px-4 py-6 text-slate-600 dark:text-slate-300">
        Hämtar jobb …
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="container mx-auto max-w-3xl px-4 py-6">
        <p className="text-slate-700 dark:text-slate-300">{error || "Jobbet kunde inte hittas."}</p>
        <Link to="/" className="text-indigo-700 underline dark:text-indigo-300">
          Tillbaka
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl px-4 py-6">
      <div className="card p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{job.title}</h1>
            <p className="text-slate-600 dark:text-slate-300">
              {job.company || "Okänt företag"} · {job.location || "Okänd plats"} · {formatEmploymentType(job.employment_type)}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {(job.categories || []).map((tag) => (
                <span key={tag} className="chip">
                  {tag}
                </span>
              ))}
            </div>
          </div>
          <button
            onClick={() => toggleSave(job.id)}
            className={`rounded-md px-3 py-1.5 text-sm ${
              isSaved(job.id)
                ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            {isSaved(job.id) ? "Sparad" : "Spara"}
          </button>
        </div>
        <div className="mt-6 space-y-3 text-sm text-slate-500 dark:text-slate-400">
          <div>Publicerad: {formatDate(job.published_at)}</div>
          <div>Sista ansökningsdag: {formatDate(job.last_application_date)}</div>
          <div>Källa: {job.source}</div>
          {job.url && (
            <div>
              Annons: <a href={job.url} target="_blank" rel="noreferrer" className="text-indigo-600 underline dark:text-indigo-300">Öppna i nytt fönster</a>
            </div>
          )}
        </div>
        <p className="mt-6 whitespace-pre-line leading-relaxed text-slate-700 dark:text-slate-200">
          {job.description || "Ingen detaljerad beskrivning finns tillgänglig."}
        </p>
      </div>
    </div>
  );
}

function SavedPage({ jobs, fetchJob }) {
  const { savedIds, toggleSave } = useSavedJobs();
  const [savedJobs, setSavedJobs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!savedIds.length) {
      setSavedJobs([]);
      return undefined;
    }

    async function load() {
      setLoading(true);
      try {
        const list = await Promise.all(
          savedIds.map(async (id) => {
            const numericId = Number(id);
            const existing = jobs.find((job) => job.id === numericId);
            if (existing) {
              return existing;
            }
            try {
              return await fetchJob(numericId);
            } catch {
              return null;
            }
          })
        );
        if (!cancelled) {
          setSavedJobs(list.filter(Boolean));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [savedIds, jobs, fetchJob]);

  return (
    <div className="container mx-auto max-w-6xl px-4 py-6">
      <h2 className="mb-4 text-xl font-semibold text-slate-800 dark:text-slate-100">Sparade jobb</h2>
      {loading && <p className="text-slate-600 dark:text-slate-300">Hämtar sparade jobb …</p>}
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {savedJobs.map((job) => (
          <JobCard key={job.id} job={job} saved={true} onSave={toggleSave} />
        ))}
        {!savedJobs.length && !loading && (
          <p className="text-slate-600 dark:text-slate-400">Du har inga sparade jobb ännu.</p>
        )}
      </div>
    </div>
  );
}

function HomePage(props) {
  return <JobSearch {...props} />;
}

function NotFoundPage() {
  return (
    <div className="container mx-auto max-w-3xl px-4 py-6">
      <p className="text-slate-700 dark:text-slate-300">Sidan kunde inte hittas.</p>
      <Link to="/" className="text-indigo-700 underline dark:text-indigo-300">
        Tillbaka
      </Link>
    </div>
  );
}

export default function JobSearchApp() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scraping, setScraping] = useState(false);
  const [error, setError] = useState("");
  const [lastQuery, setLastQuery] = useState({ title: "", location: "" });

  const fetchJobs = useCallback(async (filters = {}) => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (filters.title) params.append("title", filters.title);
      if (filters.location) params.append("location", filters.location);
      const query = params.toString();
      const response = await fetch(`${API_BASE}/jobs${query ? `?${query}` : ""}`);
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Kunde inte hämta jobb.");
      }
      const payload = await response.json();
      const list = Array.isArray(payload) ? payload : payload.jobs ?? [];
      setJobs(list);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Ett fel uppstod vid hämtning av jobb.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchJobById = useCallback(async (jobId) => {
    const response = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!response.ok) {
      throw new Error("Jobbet kunde inte hämtas.");
    }
    return response.json();
  }, []);

  const handleSearch = useCallback(
    async (filters) => {
      const criteria = {
        title: filters.title?.trim() ?? "",
        location: filters.location?.trim() ?? "",
      };
      setLastQuery(criteria);
      setError("");
      setScraping(true);
      try {
        const response = await fetch(`${API_BASE}/scrape`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            job_title: criteria.title || undefined,
            location: criteria.location || undefined,
          }),
        });
        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || "Webbsökningen misslyckades.");
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Webbsökningen misslyckades.";
        setError(message);
      }
      setScraping(false);
      await fetchJobs(criteria);
    },
    [fetchJobs]
  );

  useEffect(() => {
    fetchJobs({});
  }, [fetchJobs]);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
        <Navbar />
        <Routes>
          <Route
            path="/"
            element={
              <HomePage
                jobs={jobs}
                onSearch={handleSearch}
                loading={loading}
                scraping={scraping}
                error={error}
                lastQuery={lastQuery}
              />
            }
          />
          <Route
            path="/job/:id"
            element={<JobDetailPage jobs={jobs} fetchJob={fetchJobById} />}
          />
          <Route
            path="/saved"
            element={<SavedPage jobs={jobs} fetchJob={fetchJobById} />}
          />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
