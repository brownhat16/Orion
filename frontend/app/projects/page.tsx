'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Project {
    id: number
    title: string
    genre: string
    status: string
    total_words: number
    premise?: string
}

export default function ProjectsPage() {
    const [projects, setProjects] = useState<Project[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [statusFilter, setStatusFilter] = useState<string>('all')

    useEffect(() => {
        fetchProjects()
    }, [])

    async function fetchProjects() {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/projects/`)
            if (res.ok) {
                const data = await res.json()
                setProjects(data)
            }
        } catch (error) {
            console.error('Failed to fetch projects:', error)
        } finally {
            setLoading(false)
        }
    }

    const filteredProjects = projects.filter((project) => {
        const matchesSearch =
            project.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            project.genre.toLowerCase().includes(searchQuery.toLowerCase())
        const matchesStatus = statusFilter === 'all' || project.status === statusFilter
        return matchesSearch && matchesStatus
    })

    const statuses = ['all', ...new Set(projects.map((p) => p.status))]

    return (
        <div className="p-8">
            {/* Header */}
            <header className="mb-8">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
                            My Novels
                        </h1>
                        <p className="text-surface-400 mt-2">
                            Manage all your novel projects in one place
                        </p>
                    </div>
                    <Link href="/" className="btn-primary flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        New Novel
                    </Link>
                </div>
            </header>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <div className="relative flex-1 max-w-md">
                    <svg
                        className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1.5}
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                    </svg>
                    <input
                        type="text"
                        placeholder="Search by title or genre..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="input pl-10 w-full"
                    />
                </div>
                <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="input w-auto"
                >
                    {statuses.map((s) => (
                        <option key={s} value={s}>
                            {s === 'all' ? 'All Statuses' : s.replace('_', ' ')}
                        </option>
                    ))}
                </select>
            </div>

            {/* Projects Grid */}
            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="card">
                            <div className="skeleton h-6 w-3/4 mb-4"></div>
                            <div className="skeleton h-4 w-1/2 mb-2"></div>
                            <div className="skeleton h-4 w-1/4"></div>
                        </div>
                    ))}
                </div>
            ) : filteredProjects.length === 0 ? (
                <div className="card text-center py-16">
                    <div className="w-20 h-20 rounded-full bg-surface-800 flex items-center justify-center mx-auto mb-6">
                        <svg
                            className="w-10 h-10 text-surface-500"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={1.5}
                                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                            />
                        </svg>
                    </div>
                    {searchQuery || statusFilter !== 'all' ? (
                        <>
                            <h3 className="text-xl font-semibold mb-2">No Matching Projects</h3>
                            <p className="text-surface-400 mb-6">
                                Try adjusting your search or filter criteria
                            </p>
                            <button
                                onClick={() => {
                                    setSearchQuery('')
                                    setStatusFilter('all')
                                }}
                                className="btn-secondary"
                            >
                                Clear Filters
                            </button>
                        </>
                    ) : (
                        <>
                            <h3 className="text-xl font-semibold mb-2">No Projects Yet</h3>
                            <p className="text-surface-400 mb-6">
                                Start your first novel and let AI help you bring your story to life
                            </p>
                            <Link href="/" className="btn-primary">
                                Create Your First Novel
                            </Link>
                        </>
                    )}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredProjects.map((project) => (
                        <Link href={`/projects/${project.id}`} key={project.id}>
                            <div className="card cursor-pointer group h-full">
                                <div className="flex items-start justify-between mb-4">
                                    <h3 className="text-lg font-semibold group-hover:text-primary-400 transition-colors">
                                        {project.title}
                                    </h3>
                                    <span className={`status-${project.status}`}>
                                        {project.status.replace('_', ' ')}
                                    </span>
                                </div>
                                <p className="text-surface-400 text-sm mb-4">{project.genre}</p>
                                <div className="flex items-center justify-between text-sm mt-auto">
                                    <span className="text-surface-500">
                                        {project.total_words.toLocaleString()} words
                                    </span>
                                    <svg
                                        className="w-5 h-5 text-surface-600 group-hover:text-primary-400 group-hover:translate-x-1 transition-all"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M9 5l7 7-7 7"
                                        />
                                    </svg>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    )
}
