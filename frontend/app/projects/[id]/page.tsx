'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import StoryEditor from '@/components/StoryEditor'

interface Project {
    id: number
    title: string
    premise: string
    genre: string
    status: string
    current_chapter: number
    total_words: number
    total_tokens_used: number
    outline: any
}

interface Chapter {
    id: number
    order: number
    title: string
    summary: string
    status: string
    word_count: number
}

interface Character {
    id: number
    name: string
    role: string
    bio: string
    appearance?: string
    personality?: string
}

export default function ProjectPage() {
    const params = useParams()
    const router = useRouter()
    const projectId = params.id as string

    const [project, setProject] = useState<Project | null>(null)
    const [chapters, setChapters] = useState<Chapter[]>([])
    const [characters, setCharacters] = useState<Character[]>([])
    const [loading, setLoading] = useState(true)
    const [activeTab, setActiveTab] = useState<'overview' | 'outline' | 'characters' | 'manuscript' | 'editor'>('overview')
    const [generating, setGenerating] = useState(false)
    const [showEditModal, setShowEditModal] = useState(false)

    useEffect(() => {
        fetchProject()
    }, [projectId])

    async function fetchProject() {
        try {
            const [projRes, chapRes, charRes] = await Promise.all([
                fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/projects/${projectId}`),
                fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/projects/${projectId}/chapters`),
                fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/projects/${projectId}/characters`),
            ])

            if (projRes.ok) setProject(await projRes.json())
            if (chapRes.ok) setChapters(await chapRes.json())
            if (charRes.ok) setCharacters(await charRes.json())
        } catch (error) {
            console.error('Failed to fetch project:', error)
        } finally {
            setLoading(false)
        }
    }

    async function generateOutline() {
        setGenerating(true)
        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/generation/${projectId}/generate-outline`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ num_chapters: 20 }),
            })
            // Poll for updates
            setTimeout(fetchProject, 5000)
        } catch (error) {
            console.error('Failed to start generation:', error)
        } finally {
            setGenerating(false)
        }
    }

    async function approveOutline() {
        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/projects/${projectId}/approve-outline`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ approved: true }),
            })
            fetchProject()
        } catch (error) {
            console.error('Failed to approve outline:', error)
        }
    }

    async function startGeneration() {
        setGenerating(true)
        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/generation/${projectId}/generate-chapters`, {
                method: 'POST',
            })
        } catch (error) {
            console.error('Failed to start generation:', error)
        } finally {
            setGenerating(false)
        }
    }

    if (loading) {
        return (
            <div className="p-8">
                <div className="skeleton h-10 w-1/3 mb-4"></div>
                <div className="skeleton h-6 w-1/4 mb-8"></div>
                <div className="skeleton h-64 w-full"></div>
            </div>
        )
    }

    if (!project) {
        return (
            <div className="p-8 text-center">
                <h1 className="text-2xl font-bold text-surface-100">Project not found</h1>
                <button onClick={() => router.push('/')} className="btn-primary mt-4">
                    Back to Dashboard
                </button>
            </div>
        )
    }

    return (
        <div className="p-8">
            {/* Header */}
            <header className="mb-8">
                <div className="flex items-start justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <h1 className="text-3xl font-bold">{project.title}</h1>
                            <span className={`status-${project.status}`}>{project.status.replace('_', ' ')}</span>
                            <button
                                onClick={() => setShowEditModal(true)}
                                className="p-1 text-surface-400 hover:text-primary-400 transition-colors"
                                title="Edit Project Details"
                            >
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                </svg>
                            </button>
                        </div>
                        <p className="text-surface-400">{project.genre}</p>
                    </div>

                    <div className="flex gap-3">
                        {project.status === 'draft' && (
                            <button onClick={generateOutline} disabled={generating} className="btn-primary">
                                {generating ? 'Generating...' : 'Generate Outline'}
                            </button>
                        )}
                        {project.status === 'outline_pending_approval' && (
                            <button onClick={approveOutline} className="btn-primary">
                                Approve Outline
                            </button>
                        )}
                        {project.status === 'outline_approved' && (
                            <button onClick={startGeneration} disabled={generating} className="btn-primary">
                                {generating ? 'Starting...' : 'Start Writing'}
                            </button>
                        )}
                    </div>
                </div>
            </header>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-4 mb-8">
                <div className="glass-card p-4">
                    <p className="text-surface-400 text-sm">Chapters</p>
                    <p className="text-2xl font-bold">{chapters.length}</p>
                </div>
                <div className="glass-card p-4">
                    <p className="text-surface-400 text-sm">Characters</p>
                    <p className="text-2xl font-bold">{characters.length}</p>
                </div>
                <div className="glass-card p-4">
                    <p className="text-surface-400 text-sm">Words</p>
                    <p className="text-2xl font-bold">{project.total_words.toLocaleString()}</p>
                </div>
                <div className="glass-card p-4">
                    <p className="text-surface-400 text-sm">Est. Cost</p>
                    <p className="text-2xl font-bold">${((project.total_tokens_used || 0) / 1000000 * 10).toFixed(2)}</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-surface-800 mb-6">
                <nav className="flex gap-1 -mb-px">
                    {(['overview', 'outline', 'characters', 'editor', 'manuscript'] as const).map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === tab
                                ? 'border-primary-500 text-primary-400'
                                : 'border-transparent text-surface-400 hover:text-surface-200'
                                }`}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    ))}
                </nav>
            </div>

            {/* Tab Content */}
            <div className="animate-in">
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        <div className="card">
                            <h3 className="card-title mb-4">Premise</h3>
                            <p className="text-surface-300 leading-relaxed">{project.premise}</p>
                        </div>

                        {project.outline && (
                            <div className="card">
                                <h3 className="card-title mb-4">Synopsis</h3>
                                <p className="text-surface-300 leading-relaxed">{project.outline.synopsis}</p>
                            </div>
                        )}

                        {project.status === 'generating' && (
                            <div className="card">
                                <h3 className="card-title mb-4">Generation Progress</h3>
                                <div className="space-y-4">
                                    <div className="flex justify-between text-sm mb-2">
                                        <span>Chapter {project.current_chapter} of {chapters.length}</span>
                                        <span>{Math.round((project.current_chapter / chapters.length) * 100)}%</span>
                                    </div>
                                    <div className="progress-bar">
                                        <div
                                            className="progress-fill"
                                            style={{ width: `${(project.current_chapter / chapters.length) * 100}%` }}
                                        ></div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'outline' && (
                    <div className="space-y-4">
                        {chapters.length === 0 ? (
                            <div className="card text-center py-12">
                                <p className="text-surface-400">No outline generated yet</p>
                            </div>
                        ) : (
                            chapters.map(chapter => (
                                <div key={chapter.id} className="card">
                                    <div className="flex items-start justify-between mb-3">
                                        <div>
                                            <span className="text-sm text-surface-500">Chapter {chapter.order}</span>
                                            <h4 className="font-semibold">{chapter.title}</h4>
                                        </div>
                                        <span className={`status-${chapter.status}`}>{chapter.status}</span>
                                    </div>
                                    <p className="text-surface-400 text-sm">{chapter.summary}</p>
                                    {chapter.word_count > 0 && (
                                        <p className="text-surface-500 text-xs mt-2">{chapter.word_count.toLocaleString()} words</p>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                )}

                {activeTab === 'characters' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {characters.length === 0 ? (
                            <div className="card text-center py-12 col-span-2">
                                <p className="text-surface-400">No characters generated yet</p>
                            </div>
                        ) : (
                            characters.map(char => (
                                <div key={char.id} className="card">
                                    <div className="flex items-start gap-4">
                                        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-2xl font-bold">
                                            {char.name[0]}
                                        </div>
                                        <div className="flex-1">
                                            <h4 className="font-semibold text-lg">{char.name}</h4>
                                            <p className="text-primary-400 text-sm mb-2">{char.role}</p>
                                            <p className="text-surface-400 text-sm">{char.bio}</p>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}

                {activeTab === 'editor' && (
                    <StoryEditor
                        projectId={projectId}
                        chapters={chapters}
                        onChapterCreated={fetchProject}
                    />
                )}

                {activeTab === 'manuscript' && (
                    <div className="space-y-8">
                        {chapters.filter(c => c.status === 'completed').length === 0 ? (
                            <div className="card text-center py-12">
                                <p className="text-surface-400">No chapters written yet</p>
                            </div>
                        ) : (
                            chapters
                                .filter(c => c.status === 'completed')
                                .map(chapter => (
                                    <article key={chapter.id} className="card">
                                        <h2 className="text-2xl font-serif font-semibold mb-6">
                                            Chapter {chapter.order}: {chapter.title}
                                        </h2>
                                        <div className="prose-content">
                                            {/* Would fetch full chapter content here */}
                                            <p className="text-surface-400 italic">
                                                Click to view full chapter ({chapter.word_count.toLocaleString()} words)
                                            </p>
                                        </div>
                                    </article>
                                ))
                        )}
                    </div>
                )}
                {/* Edit Project Modal */}
                {showEditModal && project && (
                    <EditProjectModal
                        project={project}
                        onClose={() => setShowEditModal(false)}
                        onUpdated={(updatedProject) => {
                            setProject(updatedProject)
                            setShowEditModal(false)
                        }}
                    />
                )}
            </div>
        </div>
    )
}

function EditProjectModal({ project, onClose, onUpdated }: { project: Project; onClose: () => void; onUpdated: (p: Project) => void }) {
    const [title, setTitle] = useState(project.title)
    const [genre, setGenre] = useState(project.genre)
    const [premise, setPremise] = useState(project.premise)
    const [saving, setSaving] = useState(false)

    async function handleUpdate(e: React.FormEvent) {
        e.preventDefault()
        setSaving(true)

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/projects/${project.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, genre, premise }),
            })

            if (res.ok) {
                const updated = await res.json()
                onUpdated(updated)
            }
        } catch (error) {
            console.error('Failed to update project:', error)
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose}></div>

            <div className="relative glass-card w-full max-w-xl animate-in">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold">Edit Project Details</h2>
                    <button onClick={onClose} className="text-surface-400 hover:text-surface-100">
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <form onSubmit={handleUpdate} className="space-y-6">
                    <div>
                        <label className="label">Title</label>
                        <input
                            type="text"
                            className="input"
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
                            value={genre}
                            onChange={e => setGenre(e.target.value)}
                            required
                        />
                    </div>

                    <div>
                        <label className="label">Premise</label>
                        <textarea
                            className="textarea h-32"
                            value={premise}
                            onChange={e => setPremise(e.target.value)}
                            required
                        />
                    </div>

                    <div className="flex gap-4 pt-4">
                        <button type="button" onClick={onClose} className="btn-secondary flex-1">
                            Cancel
                        </button>
                        <button type="submit" disabled={saving} className="btn-primary flex-1">
                            {saving ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
