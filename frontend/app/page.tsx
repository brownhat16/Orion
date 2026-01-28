'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Project {
    id: number
    title: string
    genre: string
    status: string
    total_words: number
}

export default function Dashboard() {
    const [projects, setProjects] = useState<Project[]>([])
    const [loading, setLoading] = useState(true)
    const [showNewModal, setShowNewModal] = useState(false)

    useEffect(() => {
        fetchProjects()
    }, [])

    async function fetchProjects() {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/projects`)
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

    return (
        <div className="p-8">
            {/* Header */}
            <header className="mb-12">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
                            Welcome Back
                        </h1>
                        <p className="text-surface-400 mt-2">
                            Continue working on your novels or start a new masterpiece
                        </p>
                    </div>
                    <button
                        onClick={() => setShowNewModal(true)}
                        className="btn-primary flex items-center gap-2"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        New Novel
                    </button>
                </div>
            </header>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                <div className="card">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-primary-500/20 flex items-center justify-center">
                            <svg className="w-6 h-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                            </svg>
                        </div>
                        <div>
                            <p className="text-surface-400 text-sm">Total Projects</p>
                            <p className="text-2xl font-bold">{projects.length}</p>
                        </div>
                    </div>
                </div>

                <div className="card">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-accent-500/20 flex items-center justify-center">
                            <svg className="w-6 h-6 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                            </svg>
                        </div>
                        <div>
                            <p className="text-surface-400 text-sm">Words Written</p>
                            <p className="text-2xl font-bold">
                                {projects.reduce((acc, p) => acc + p.total_words, 0).toLocaleString()}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="card">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                            <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <div>
                            <p className="text-surface-400 text-sm">Completed</p>
                            <p className="text-2xl font-bold">
                                {projects.filter(p => p.status === 'completed').length}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Projects List */}
            <section>
                <h2 className="text-2xl font-semibold mb-6">Your Projects</h2>

                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="card">
                                <div className="skeleton h-6 w-3/4 mb-4"></div>
                                <div className="skeleton h-4 w-1/2 mb-2"></div>
                                <div className="skeleton h-4 w-1/4"></div>
                            </div>
                        ))}
                    </div>
                ) : projects.length === 0 ? (
                    <div className="card text-center py-16">
                        <div className="w-20 h-20 rounded-full bg-surface-800 flex items-center justify-center mx-auto mb-6">
                            <svg className="w-10 h-10 text-surface-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                            </svg>
                        </div>
                        <h3 className="text-xl font-semibold mb-2">No Projects Yet</h3>
                        <p className="text-surface-400 mb-6">Start your first novel and let AI help you bring your story to life</p>
                        <button
                            onClick={() => setShowNewModal(true)}
                            className="btn-primary"
                        >
                            Create Your First Novel
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {projects.map(project => (
                            <Link href={`/projects/${project.id}`} key={project.id}>
                                <div className="card cursor-pointer group">
                                    <div className="flex items-start justify-between mb-4">
                                        <h3 className="text-lg font-semibold group-hover:text-primary-400 transition-colors">
                                            {project.title}
                                        </h3>
                                        <span className={`status-${project.status}`}>
                                            {project.status}
                                        </span>
                                    </div>
                                    <p className="text-surface-400 text-sm mb-4">{project.genre}</p>
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-surface-500">
                                            {project.total_words.toLocaleString()} words
                                        </span>
                                        <svg className="w-5 h-5 text-surface-600 group-hover:text-primary-400 group-hover:translate-x-1 transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                        </svg>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </section>

            {/* New Project Modal */}
            {showNewModal && (
                <NewProjectModal onClose={() => setShowNewModal(false)} onCreated={fetchProjects} />
            )}
        </div>
    )
}

function NewProjectModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
    const [title, setTitle] = useState('')
    const [premise, setPremise] = useState('')
    const [genre, setGenre] = useState('')
    const [creating, setCreating] = useState(false)

    async function handleCreate(e: React.FormEvent) {
        e.preventDefault()
        setCreating(true)

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/projects`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, premise, genre }),
            })

            if (res.ok) {
                onCreated()
                onClose()
            }
        } catch (error) {
            console.error('Failed to create project:', error)
        } finally {
            setCreating(false)
        }
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose}></div>

            <div className="relative glass-card w-full max-w-xl animate-in">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold">Create New Novel</h2>
                    <button onClick={onClose} className="text-surface-400 hover:text-surface-100">
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <form onSubmit={handleCreate} className="space-y-6">
                    <div>
                        <label className="label">Title</label>
                        <input
                            type="text"
                            className="input"
                            placeholder="The Last Detective"
                            value={title}
                            onChange={e => setTitle(e.target.value)}
                            required
                        />
                    </div>

                    <div>
                        <label className="label">Genre</label>
                        <input
                            type="text"
                            className="input"
                            placeholder="Cyberpunk Thriller, Fantasy Romance, etc."
                            value={genre}
                            onChange={e => setGenre(e.target.value)}
                            required
                        />
                    </div>

                    <div>
                        <label className="label">Premise</label>
                        <textarea
                            className="textarea h-32"
                            placeholder="In a rain-soaked Neo-Tokyo, a burned-out detective takes on one last case that will uncover secrets about her own past..."
                            value={premise}
                            onChange={e => setPremise(e.target.value)}
                            required
                        />
                        <p className="text-xs text-surface-500 mt-2">
                            Describe your story idea in 2-3 sentences. Be specific about characters, setting, and conflict.
                        </p>
                    </div>

                    <div className="flex gap-4 pt-4">
                        <button type="button" onClick={onClose} className="btn-secondary flex-1">
                            Cancel
                        </button>
                        <button type="submit" disabled={creating} className="btn-primary flex-1">
                            {creating ? (
                                <span className="flex items-center justify-center gap-2">
                                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Creating...
                                </span>
                            ) : (
                                'Create Project'
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
