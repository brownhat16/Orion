'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

interface Suggestion {
    id: number
    content: string
    reasoning: string
}

interface Chapter {
    id: number
    order: number
    title: string
}

interface StoryEditorProps {
    projectId: string
    chapters: Chapter[]
    onChapterCreated?: () => void
}

export default function StoryEditor({ projectId, chapters, onChapterCreated }: StoryEditorProps) {
    const [selectedChapter, setSelectedChapter] = useState<Chapter | null>(null)
    const [storyLines, setStoryLines] = useState<string[]>([])
    const [suggestions, setSuggestions] = useState<Suggestion[]>([])
    const [loading, setLoading] = useState(false)
    const [saving, setSaving] = useState(false)
    const [manualMode, setManualMode] = useState(false)
    const [manualInput, setManualInput] = useState('')
    const [hoveredSuggestion, setHoveredSuggestion] = useState<number | null>(null)
    const storyContainerRef = useRef<HTMLDivElement>(null)

    // Auto-select first chapter or show create option
    useEffect(() => {
        if (chapters.length > 0 && !selectedChapter) {
            setSelectedChapter(chapters[0])
        }
    }, [chapters, selectedChapter])

    // Load chapter content when selected
    useEffect(() => {
        if (selectedChapter) {
            loadChapterContent()
        }
    }, [selectedChapter])

    // Generate initial suggestions when chapter loads
    useEffect(() => {
        if (selectedChapter && storyLines.length === 0 && suggestions.length === 0) {
            generateSuggestions()
        }
    }, [selectedChapter, storyLines])

    // Keyboard shortcuts
    useEffect(() => {
        function handleKeyDown(e: KeyboardEvent) {
            // Don't trigger if typing in input
            if (manualMode || e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
                return
            }

            if (e.key === '1' && suggestions[0]) {
                acceptSuggestion(suggestions[0])
            } else if (e.key === '2' && suggestions[1]) {
                acceptSuggestion(suggestions[1])
            } else if (e.key === '3' && suggestions[2]) {
                acceptSuggestion(suggestions[2])
            } else if (e.key === 'r' || e.key === 'R') {
                generateSuggestions()
            } else if (e.key === 'e' || e.key === 'E') {
                setManualMode(true)
            }
        }

        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [suggestions, manualMode])

    async function loadChapterContent() {
        if (!selectedChapter) return

        try {
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/story-editor/${projectId}/chapter/${selectedChapter.id}/content`
            )
            if (res.ok) {
                const data = await res.json()
                setStoryLines(data.lines || [])
            }
        } catch (error) {
            console.error('Failed to load chapter content:', error)
        }
    }

    async function generateSuggestions() {
        if (!selectedChapter) return

        setLoading(true)
        setSuggestions([])

        try {
            const currentText = storyLines.join('\n\n')
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/story-editor/${projectId}/suggest`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        current_text: currentText,
                        chapter_id: selectedChapter.id,
                        num_suggestions: 3,
                    }),
                }
            )

            if (res.ok) {
                const data = await res.json()
                setSuggestions(data.suggestions)
            }
        } catch (error) {
            console.error('Failed to generate suggestions:', error)
        } finally {
            setLoading(false)
        }
    }

    async function acceptSuggestion(suggestion: Suggestion) {
        if (!selectedChapter) return

        setSaving(true)

        try {
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/story-editor/${projectId}/save-line`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        chapter_id: selectedChapter.id,
                        content: suggestion.content,
                    }),
                }
            )

            if (res.ok) {
                setStoryLines([...storyLines, suggestion.content])
                setSuggestions([])
                // Scroll to bottom
                setTimeout(() => {
                    storyContainerRef.current?.scrollTo({
                        top: storyContainerRef.current.scrollHeight,
                        behavior: 'smooth',
                    })
                }, 100)
                // Generate new suggestions
                setTimeout(generateSuggestions, 300)
            }
        } catch (error) {
            console.error('Failed to save line:', error)
        } finally {
            setSaving(false)
        }
    }

    async function submitManualInput() {
        if (!selectedChapter || !manualInput.trim()) return

        setSaving(true)

        try {
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/story-editor/${projectId}/save-line`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        chapter_id: selectedChapter.id,
                        content: manualInput.trim(),
                    }),
                }
            )

            if (res.ok) {
                setStoryLines([...storyLines, manualInput.trim()])
                setManualInput('')
                setManualMode(false)
                setSuggestions([])
                setTimeout(generateSuggestions, 300)
            }
        } catch (error) {
            console.error('Failed to save manual input:', error)
        } finally {
            setSaving(false)
        }
    }

    async function createNewChapter() {
        try {
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/story-editor/${projectId}/create-draft-chapter`,
                { method: 'POST' }
            )

            if (res.ok) {
                const data = await res.json()
                setSelectedChapter(data.chapter)
                setStoryLines([])
                setSuggestions([])
                onChapterCreated?.()
            }
        } catch (error) {
            console.error('Failed to create chapter:', error)
        }
    }

    if (!selectedChapter && chapters.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-16">
                <div className="text-center mb-8">
                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center">
                        <svg className="w-10 h-10 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                    </div>
                    <h3 className="text-xl font-semibold mb-2">Start Writing Your Story</h3>
                    <p className="text-surface-400 max-w-md">
                        Create your first chapter and write line by line with AI suggestions to guide you.
                    </p>
                </div>
                <button onClick={createNewChapter} className="btn-primary">
                    <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Create First Chapter
                </button>
            </div>
        )
    }

    return (
        <div className="story-editor">
            {/* Chapter Selector */}
            <div className="flex items-center gap-4 mb-6">
                <select
                    value={selectedChapter?.id || ''}
                    onChange={(e) => {
                        const chapter = chapters.find(c => c.id === Number(e.target.value))
                        if (chapter) setSelectedChapter(chapter)
                    }}
                    className="input w-auto min-w-[200px]"
                >
                    {chapters.map(chapter => (
                        <option key={chapter.id} value={chapter.id}>
                            Chapter {chapter.order}: {chapter.title}
                        </option>
                    ))}
                </select>
                <button onClick={createNewChapter} className="btn-secondary text-sm">
                    + New Chapter
                </button>
                <div className="flex-1" />
                <div className="text-sm text-surface-500">
                    {storyLines.length} paragraphs • {storyLines.join(' ').split(/\s+/).filter(Boolean).length} words
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Story Display */}
                <div className="lg:col-span-2">
                    <div className="card h-[600px] flex flex-col">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="card-title">Your Story</h3>
                            {storyLines.length > 0 && (
                                <span className="text-xs text-surface-500 bg-surface-800 px-2 py-1 rounded">
                                    Last saved just now
                                </span>
                            )}
                        </div>

                        <div
                            ref={storyContainerRef}
                            className="flex-1 overflow-y-auto pr-2 space-y-4 scrollbar-thin"
                        >
                            {storyLines.length === 0 ? (
                                <div className="h-full flex items-center justify-center">
                                    <p className="text-surface-500 italic">
                                        Your story will appear here...
                                    </p>
                                </div>
                            ) : (
                                storyLines.map((line, index) => (
                                    <p
                                        key={index}
                                        className="story-line text-surface-200 leading-relaxed"
                                    >
                                        {line}
                                    </p>
                                ))
                            )}

                            {/* Manual Input Area */}
                            {manualMode && (
                                <div className="mt-4 p-4 rounded-lg bg-surface-800/50 border border-primary-500/30">
                                    <textarea
                                        value={manualInput}
                                        onChange={(e) => setManualInput(e.target.value)}
                                        placeholder="Write your own paragraph..."
                                        className="textarea w-full h-24 mb-3"
                                        autoFocus
                                    />
                                    <div className="flex gap-2">
                                        <button
                                            onClick={submitManualInput}
                                            disabled={!manualInput.trim() || saving}
                                            className="btn-primary text-sm"
                                        >
                                            {saving ? 'Saving...' : 'Add to Story'}
                                        </button>
                                        <button
                                            onClick={() => {
                                                setManualMode(false)
                                                setManualInput('')
                                            }}
                                            className="btn-secondary text-sm"
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Suggestions Panel */}
                <div className="lg:col-span-1">
                    <div className="card h-[600px] flex flex-col">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="card-title">AI Suggestions</h3>
                            <button
                                onClick={generateSuggestions}
                                disabled={loading}
                                className="p-2 rounded-lg hover:bg-surface-700 transition-colors"
                                title="Regenerate (R)"
                            >
                                <svg
                                    className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`}
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto space-y-3">
                            {loading ? (
                                <div className="space-y-3">
                                    {[1, 2, 3].map(i => (
                                        <div key={i} className="suggestion-card-skeleton">
                                            <div className="skeleton h-4 w-1/4 mb-2"></div>
                                            <div className="skeleton h-3 w-full mb-1"></div>
                                            <div className="skeleton h-3 w-5/6 mb-1"></div>
                                            <div className="skeleton h-3 w-4/6"></div>
                                        </div>
                                    ))}
                                </div>
                            ) : suggestions.length > 0 ? (
                                suggestions.map((suggestion) => (
                                    <div
                                        key={suggestion.id}
                                        onClick={() => acceptSuggestion(suggestion)}
                                        onMouseEnter={() => setHoveredSuggestion(suggestion.id)}
                                        onMouseLeave={() => setHoveredSuggestion(null)}
                                        className={`suggestion-card cursor-pointer transition-all duration-200 ${hoveredSuggestion === suggestion.id ? 'suggestion-active' : ''
                                            }`}
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="suggestion-number">{suggestion.id}</span>
                                            <span className="text-xs text-surface-500">{suggestion.reasoning}</span>
                                        </div>
                                        <p className="text-sm text-surface-300 line-clamp-4">
                                            {suggestion.content}
                                        </p>
                                        {hoveredSuggestion === suggestion.id && (
                                            <div className="mt-3 pt-3 border-t border-surface-700 text-xs text-primary-400">
                                                Click or press {suggestion.id} to add
                                            </div>
                                        )}
                                    </div>
                                ))
                            ) : (
                                <div className="h-full flex items-center justify-center">
                                    <p className="text-surface-500 text-sm text-center">
                                        Click regenerate to get<br />AI suggestions
                                    </p>
                                </div>
                            )}
                        </div>

                        {/* Action Buttons */}
                        <div className="mt-4 pt-4 border-t border-surface-800">
                            <button
                                onClick={() => setManualMode(true)}
                                disabled={manualMode}
                                className="btn-secondary w-full text-sm"
                            >
                                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                </svg>
                                Write Manually (E)
                            </button>
                        </div>

                        {/* Keyboard Shortcuts */}
                        <div className="mt-3 text-xs text-surface-600 text-center">
                            <span className="keyboard-hint">1</span>
                            <span className="keyboard-hint">2</span>
                            <span className="keyboard-hint">3</span>
                            <span className="ml-2">select</span>
                            <span className="mx-2">•</span>
                            <span className="keyboard-hint">R</span>
                            <span className="ml-1">regenerate</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
