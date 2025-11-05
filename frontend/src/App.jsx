import React, { createContext, useContext, useState } from 'react'
import { Briefcase, Search, MapPin, DollarSign, Calendar, Building2, BookmarkPlus, ExternalLink } from 'lucide-react'

// Theme Context
const ThemeContext = createContext()

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within ThemeProvider')
  return context
}

// Theme Provider Component
export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState('light')

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'))
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      <div className={theme}>{children}</div>
    </ThemeContext.Provider>
  )
}

// Professional Job Search Components

export const Button = ({ children, variant = 'default', size = 'md', icon, className = '', ...props }) => {
  const variants = {
    default: 'bg-indigo-600 hover:bg-indigo-700 text-white dark:bg-indigo-500 dark:hover:bg-indigo-600 shadow-sm',
    secondary: 'bg-slate-100 hover:bg-slate-200 text-slate-900 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-100',
    outline: 'border border-slate-300 text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800',
    ghost: 'hover:bg-slate-100 text-slate-700 dark:hover:bg-slate-800 dark:text-slate-300',
    success: 'bg-emerald-600 hover:bg-emerald-700 text-white dark:bg-emerald-500 dark:hover:bg-emerald-600 shadow-sm',
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  }

  return (
    <button
      className={`${variants[variant]} ${sizes[size]} rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900 inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      {...props}
    >
      {icon && icon}
      {children}
    </button>
  )
}

export const Card = ({ children, className = '', hover = false }) => {
  return (
    <div
      className={`bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 transition-all duration-200 ${hover ? 'hover:shadow-lg hover:border-indigo-200 dark:hover:border-indigo-700 cursor-pointer' : 'shadow-sm'} ${className}`}
    >
      {children}
    </div>
  )
}

export const Input = ({ icon, className = '', ...props }) => {
  return (
    <div className="relative">
      {icon && <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">{icon}</div>}
      <input
        className={`w-full ${icon ? 'pl-10' : 'pl-4'} pr-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 ${className}`}
        {...props}
      />
    </div>
  )
}

export const Badge = ({ children, variant = 'default' }) => {
  const variants = {
    default: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300',
    success: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
    warning: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    info: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    neutral: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
  }

  return <span className={`${variants[variant]} px-3 py-1 rounded-full text-xs font-medium inline-block`}>{children}</span>
}

export const JobCard = ({ title, company, location, salary, type, posted, tags, saved = false, onSave, onApply }) => {
  return (
    <Card hover>
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-1 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">{title}</h3>
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400 mb-3">
            <Building2 size={16} />
            <span className="font-medium">{company}</span>
          </div>
        </div>
        <button onClick={onSave} className="text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
          <BookmarkPlus size={20} className={saved ? 'fill-current text-indigo-600' : ''} />
        </button>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
          <MapPin size={16} />
          <span>{location}</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
          <DollarSign size={16} />
          <span className="font-medium text-slate-900 dark:text-slate-100">{salary}</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
          <Calendar size={16} />
          <span>{posted}</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        <Badge variant="info">{type}</Badge>
        {tags.map((tag, i) => (
          <Badge key={i} variant="neutral">
            {tag}
          </Badge>
        ))}
      </div>

      <div className="flex gap-2 pt-4 border-t border-slate-200 dark:border-slate-700">
        <Button size="sm" variant="outline" className="flex-1">
          View Details
        </Button>
        <Button size="sm" className="flex-1" onClick={onApply}>
          Apply Now
        </Button>
      </div>
    </Card>
  )
}

// Demo Application
function JobSearchDemo() {
  const { theme, toggleTheme } = useTheme()
  const [searchQuery, setSearchQuery] = useState('')

  const sampleJobs = [
    {
      title: 'Senior Frontend Developer',
      company: 'TechCorp Inc.',
      location: 'Remote (US)',
      salary: '$120k - $160k',
      type: 'Full-time',
      posted: '2 days ago',
      tags: ['React', 'TypeScript', 'Tailwind'],
    },
    {
      title: 'Product Designer',
      company: 'Design Studio',
      location: 'New York, NY',
      salary: '$100k - $140k',
      type: 'Full-time',
      posted: '1 week ago',
      tags: ['Figma', 'UI/UX', 'Design Systems'],
    },
    {
      title: 'Full Stack Engineer',
      company: 'StartupXYZ',
      location: 'San Francisco, CA',
      salary: '$130k - $180k',
      type: 'Full-time',
      posted: '3 days ago',
      tags: ['Node.js', 'React', 'PostgreSQL'],
    },
  ]

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
      {/* Header */}
      <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Briefcase className="text-indigo-600 dark:text-indigo-400" size={28} />
              <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">JobBoard</h1>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm">
                My Applications
              </Button>
              <Button variant="ghost" size="sm">
                Saved Jobs
              </Button>
              <Button onClick={toggleTheme} variant="outline" size="sm">
                {theme === 'light' ? '🌙' : '☀️'}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Section */}
        <div className="mb-8">
          <Card>
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Find Your Next Opportunity</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input icon={<Search size={18} />} placeholder="Job title or keyword" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
                <Input icon={<MapPin size={18} />} placeholder="Location" />
                <Button icon={<Search size={18} />} size="md" className="w-full">
                  Search Jobs
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="text-sm text-slate-600 dark:text-slate-400">Popular:</span>
                <Badge variant="neutral">Remote</Badge>
                <Badge variant="neutral">Frontend</Badge>
                <Badge variant="neutral">Full-time</Badge>
                <Badge variant="neutral">Senior Level</Badge>
              </div>
            </div>
          </Card>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <div className="text-center">
              <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400 mb-1">1,247</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Active Jobs</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400 mb-1">89</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Companies Hiring</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-1">12</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">New Today</div>
            </div>
          </Card>
        </div>

        {/* Job Listings */}
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Recommended Jobs</h2>
            <select className="px-4 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
              <option>Most Recent</option>
              <option>Best Match</option>
              <option>Highest Salary</option>
            </select>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {sampleJobs.map((job, i) => (
              <JobCard key={i} {...job} />
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}

// Wrap the app with ThemeProvider
export default function App() {
  return (
    <ThemeProvider>
      <JobSearchDemo />
    </ThemeProvider>
  )
}
