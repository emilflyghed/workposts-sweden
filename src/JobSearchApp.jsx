import React, { useEffect, useMemo, useState } from 'react';
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  useParams,
  useNavigate,
} from 'react-router-dom';

/**
 * Self-contained job search app
 * - React Router v6: Home, Job details, Saved
 * - TailwindCSS utility classes for styling
 * - Local fake data + localStorage for "Saved" jobs
 * - No edits to your other files required
 */

const fakeJobs = [
  {
    id: '1',
    title: 'Frontend Developer',
    company: 'Nordic Tech AB',
    location: 'Stockholm, SE',
    type: 'Full-time',
    tags: ['React', 'TypeScript', 'UI'],
    description:
      'Build and optimize user interfaces in a modern React stack with TypeScript.',
  },
  {
    id: '2',
    title: 'Backend Engineer',
    company: 'CloudWorks',
    location: 'Göteborg, SE',
    type: 'Hybrid',
    tags: ['Node.js', 'Postgres', 'API'],
    description:
      'Design scalable APIs and data flows. Experience with SQL and Node required.',
  },
  {
    id: '3',
    title: 'Fullstack Developer',
    company: 'Startify',
    location: 'Remote (SE)',
    type: 'Remote',
    tags: ['React', 'Node.js', 'Tailwind'],
    description:
      'Own features end-to-end, from UI to backend. Remote-first culture.',
  },
  {
    id: '4',
    title: 'Data Engineer',
    company: 'Insight Oy',
    location: 'Malmö, SE',
    type: 'Contract',
    tags: ['Python', 'ETL', 'Airflow'],
    description:
      'Build robust pipelines, optimize ETL, and collaborate with analytics.',
  },
  {
    id: '5',
    title: 'Mobile Developer',
    company: 'AppForge',
    location: 'Uppsala, SE',
    type: 'Full-time',
    tags: ['React Native', 'iOS', 'Android'],
    description:
      'Deliver high-quality mobile apps with React Native across iOS and Android.',
  },
  {
    id: '6',
    title: 'DevOps Engineer',
    company: 'Skyscale',
    location: 'Remote (SE)',
    type: 'Remote',
    tags: ['AWS', 'CI/CD', 'Terraform'],
    description:
      'Improve deployment pipelines, observability, and infrastructure as code.',
  },
];

function useSavedJobs() {
  const [savedIds, setSavedIds] = useState(() => {
    try {
      const raw = localStorage.getItem('savedJobs');
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem('savedJobs', JSON.stringify(savedIds));
  }, [savedIds]);

  const isSaved = (id) => savedIds.includes(id);

  const toggleSave = (id) => {
    setSavedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  return { savedIds, isSaved, toggleSave };
}

function Navbar() {
  return (
    <nav className="border-b bg-white">
      <div className="container mx-auto flex items-center justify-between px-4 py-3">
        <Link to="/" className="text-xl font-semibold text-slate-800">
          JobbSök
        </Link>
        <div className="flex items-center gap-4">
          <Link to="/" className="text-slate-600 hover:text-slate-900">
            Hem
          </Link>
          <Link to="/saved" className="text-slate-600 hover:text-slate-900">
            Sparade
          </Link>
        </div>
      </div>
    </nav>
  );
}

function JobCard({ job, onSave, saved }) {
  const navigate = useNavigate();
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">{job.title}</h3>
          <p className="text-slate-600">
            {job.company} • {job.location} • {job.type}
          </p>
        </div>
        <button
          onClick={() => onSave(job.id)}
          className={`rounded-md px-3 py-1 text-sm ${saved
              ? 'bg-emerald-100 text-emerald-700'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          aria-pressed={saved}
        >
          {saved ? 'Sparad' : 'Spara'}
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {job.tags.map((t) => (
          <span
            key={t}
            className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700"
          >
            {t}
          </span>
        ))}
      </div>
      <p className="mt-3 line-clamp-2 text-slate-700">{job.description}</p>
      <div className="mt-4">
        <button
          onClick={() => navigate(`/job/${job.id}`)}
          className="rounded-md bg-slate-800 px-3 py-1.5 text-sm text-white hover:bg-slate-900"
        >
          Läs mer
        </button>
      </div>
    </div>
  );
}

function JobSearch() {
  const [q, setQ] = useState('');
  const [location, setLocation] = useState('');
  const [type, setType] = useState('');
  const { isSaved, toggleSave } = useSavedJobs();

  const results = useMemo(() => {
    return fakeJobs.filter((j) => {
      const matchQ =
        !q ||
        j.title.toLowerCase().includes(q.toLowerCase()) ||
        j.company.toLowerCase().includes(q.toLowerCase()) ||
        j.tags.join(' ').toLowerCase().includes(q.toLowerCase());
      const matchLoc =
        !location || j.location.toLowerCase().includes(location.toLowerCase());
      const matchType = !type || j.type.toLowerCase() === type.toLowerCase();
      return matchQ && matchLoc && matchType;
    });
  }, [q, location, type]);

  return (
    <div className="container mx-auto max-w-5xl px-4 py-6">
      <div className="rounded-lg border bg-white p-4 shadow-sm">
        <div className="grid gap-3 sm:grid-cols-3">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Sök titel, företag eller taggar"
            className="w-full rounded-md border px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
          />
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Plats (t.ex. Stockholm)"
            className="w-full rounded-md border px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
          />
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="w-full rounded-md border px-3 py-2 outline-none focus:ring-2 focus:ring-slate-300"
          >
            <option value="">Alla anställningstyper</option>
            <option>Full-time</option>
            <option>Remote</option>
            <option>Hybrid</option>
            <option>Contract</option>
          </select>
        </div>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {results.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            saved={isSaved(job.id)}
            onSave={toggleSave}
          />
        ))}
        {results.length === 0 && (
          <p className="text-center text-slate-600">
            Inga jobb matchar din sökning.
          </p>
        )}
      </div>
    </div>
  );
}

function JobDetailPage() {
  const { id } = useParams();
  const { isSaved, toggleSave } = useSavedJobs();
  const job = fakeJobs.find((j) => j.id === id);

  if (!job) {
    return (
      <div className="container mx-auto max-w-3xl px-4 py-6">
        <p className="text-slate-700">Jobbet kunde inte hittas.</p>
        <Link to="/" className="text-slate-800 underline">
          Tillbaka
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-3xl px-4 py-6">
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">{job.title}</h1>
            <p className="text-slate-600">
              {job.company} • {job.location} • {job.type}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {job.tags.map((t) => (
                <span
                  key={t}
                  className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
          <button
            onClick={() => toggleSave(job.id)}
            className={`rounded-md px-3 py-1.5 text-sm ${isSaved(job.id)
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
          >
            {isSaved(job.id) ? 'Sparad' : 'Spara'}
          </button>
        </div>
        <p className="mt-6 whitespace-pre-line leading-relaxed text-slate-700">
          {job.description}
        </p>
      </div>
    </div>
  );
}

function SavedPage() {
  const { savedIds } = useSavedJobs();
  const saved = fakeJobs.filter((j) => savedIds.includes(j.id));
  return (
    <div className="container mx-auto max-w-5xl px-4 py-6">
      <h2 className="mb-4 text-xl font-semibold text-slate-800">Sparade jobb</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {saved.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            saved={true}
            onSave={() => { }}
          />
        ))}
        {saved.length === 0 && (
          <p className="text-slate-600">Du har inga sparade jobb ännu.</p>
        )}
      </div>
    </div>
  );
}

function HomePage() {
  return <JobSearch />;
}

function NotFoundPage() {
  return (
    <div className="container mx-auto max-w-3xl px-4 py-6">
      <p className="text-slate-700">Sidan kunde inte hittas.</p>
      <Link to="/" className="text-slate-800 underline">
        Tillbaka
      </Link>
    </div>
  );
}

export default function JobSearchApp() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/job/:id" element={<JobDetailPage />} />
          <Route path="/saved" element={<SavedPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

