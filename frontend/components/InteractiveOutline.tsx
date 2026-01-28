'use client'

import { useState } from 'react'
import { useToast } from '@/context/ToastContext'

interface Chapter {
    id: number
    order: number
    title: string
    summary: string
    status: string
    word_count: number
}

interface InteractiveOutlineProps {
    projectId: string
    chapters: Chapter[]
    onUpdate: () => void
}

export default function InteractiveOutline({ projectId, chapters, onUpdate }: InteractiveOutlineProps) {
    const [editingChapter, setEditingChapter] = useState<Chapter | null>(null)
    const [isCreating, setIsCreating] = useState(false)
    const [loading, setLoading] = useState(false)
    const { success, error, info } = useToast()

    async function handleRefine(chapterId: number) {
        info('AI Refinement coming soon!')
    }

    async function handleDelete(chapterId: number) {
        if (!confirm('Are you sure you want to delete this chapter?')) return

        setLoading(true)
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chapters/${chapterId}`, {
                method: 'DELETE',
            })
            if (res.ok) {
                success('Chapter deleted successfully')
                onUpdate()
            } else {
                error('Failed to delete chapter')
            }
        } catch (err) {
            console.error('Failed to delete chapter:', err)
            error('An error occurred while deleting the chapter')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold">Project Outline</h2>
                <button
                    onClick={() => setIsCreating(true)}
                    className="btn-primary flex items-center gap-2"
                >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add Chapter
                </button>
            </div>

            {isCreating && (
                <ChapterForm
                    projectId={projectId}
                    onClose={() => setIsCreating(false)}
                    onSaved={() => {
                        setIsCreating(false)
                        onUpdate()
                    }}
                />
            )}

            {chapters.length === 0 ? (
                <div className="card text-center py-12">
                    <p className="text-surface-400">No chapters yet. Add one to start outlining!</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {chapters.map((chapter) => (
                        <div key={chapter.id} className="card group">
                            {editingChapter?.id === chapter.id ? (
                                <ChapterForm
                                    projectId={projectId}
                                    chapter={chapter}
                                    onClose={() => setEditingChapter(null)}
                                    onSaved={() => {
                                        setEditingChapter(null)
                                        onUpdate()
                                    }}
                                />
                            ) : (
                                <div>
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex items-center gap-3">
                                            <span className="w-8 h-8 rounded-full bg-surface-800 flex items-center justify-center text-sm font-bold text-surface-400">
                                                {chapter.order}
                                            </span>
                                            <h3 className="font-semibold text-lg">{chapter.title}</h3>
                                            <span className={`status-${chapter.status} text-xs`}>
                                                {chapter.status}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={() => setEditingChapter(chapter)}
                                                className="p-2 text-surface-400 hover:text-primary-400 transition-colors"
                                                title="Edit"
                                            >
                                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                                </svg>
                                            </button>
                                            <button
                                                onClick={() => handleDelete(chapter.id)}
                                                className="p-2 text-surface-400 hover:text-red-400 transition-colors"
                                                title="Delete"
                                            >
                                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                    <p className="text-surface-300 ml-11">{chapter.summary}</p>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

function ChapterForm({
    projectId,
    chapter,
    onClose,
    onSaved
}: {
    projectId: string
    chapter?: Chapter
    onClose: () => void
    onSaved: () => void
}) {
    const [title, setTitle] = useState(chapter?.title || '')
    const [summary, setSummary] = useState(chapter?.summary || '')
    const [saving, setSaving] = useState(false)
    const { success, error } = useToast()

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        setSaving(true)

        try {
            const url = chapter
                ? `${process.env.NEXT_PUBLIC_API_URL}/api/chapters/${chapter.id}`
                : `${process.env.NEXT_PUBLIC_API_URL}/api/chapters/`

            const method = chapter ? 'PATCH' : 'POST'

            const body = {
                title,
                summary,
                project_id: parseInt(projectId),
                ...(chapter ? {} : { order: null }) // Create appends to end
            }

            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            })

            if (res.ok) {
                success(chapter ? 'Chapter updated' : 'Chapter created')
                onSaved()
            } else {
                error('Failed to save chapter')
            }
        } catch (error) {
            console.error('Failed to save chapter:', error)
        } finally {
            setSaving(false)
        }
    }

    return (
        <form onSubmit={handleSubmit} className="bg-surface-800/50 p-4 rounded-lg border border-surface-700 animate-in mb-4">
            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-surface-400 mb-1">
                        Chapter Title
                    </label>
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="input"
                        placeholder="e.g. The Call to Adventure"
                        required
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-surface-400 mb-1">
                        Plot Summary
                    </label>
                    <textarea
                        value={summary}
                        onChange={(e) => setSummary(e.target.value)}
                        className="textarea"
                        rows={3}
                        placeholder="What happens in this chapter?"
                        required
                    />
                </div>
                <div className="flex justify-end gap-3">
                    <button
                        type="button"
                        onClick={onClose}
                        className="btn-secondary text-sm"
                        disabled={saving}
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        className="btn-primary text-sm"
                        disabled={saving}
                    >
                        {saving ? 'Saving...' : (chapter ? 'Update Chapter' : 'Create Chapter')}
                    </button>
                </div>
            </div>
        </form>
    )
}
