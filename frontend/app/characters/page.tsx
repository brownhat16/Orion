'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Character {
    id: number
    name: string
    role: string
    bio: string
    project_id: number
    project_title?: string
}

export default function CharactersPage() {
    const [characters, setCharacters] = useState<Character[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')

    useEffect(() => {
        fetchAllCharacters()
    }, [])

    async function fetchAllCharacters() {
        try {
            // Fetch all projects first, then get characters from each
            const projectsRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/projects/`)
            if (projectsRes.ok) {
                const projects = await projectsRes.json()
                const allCharacters: Character[] = []

                for (const project of projects) {
                    const charsRes = await fetch(
                        `${process.env.NEXT_PUBLIC_API_URL}/api/projects/${project.id}/characters`
                    )
                    if (charsRes.ok) {
                        const chars = await charsRes.json()
                        allCharacters.push(
                            ...chars.map((c: Character) => ({
                                ...c,
                                project_title: project.title,
                            }))
                        )
                    }
                }
                setCharacters(allCharacters)
            }
        } catch (error) {
            console.error('Failed to fetch characters:', error)
        } finally {
            setLoading(false)
        }
    }

    const filteredCharacters = characters.filter(
        (char) =>
            char.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            char.role.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="p-8">
            {/* Header */}
            <header className="mb-8">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-2">
                    Character Library
                </h1>
                <p className="text-surface-400">
                    View and manage all characters across your novels
                </p>
            </header>

            {/* Search */}
            <div className="mb-8">
                <div className="relative max-w-md">
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
                        placeholder="Search characters..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="input pl-10 w-full"
                    />
                </div>
            </div>

            {/* Characters Grid */}
            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="card">
                            <div className="skeleton h-16 w-16 rounded-full mb-4"></div>
                            <div className="skeleton h-6 w-3/4 mb-2"></div>
                            <div className="skeleton h-4 w-1/2"></div>
                        </div>
                    ))}
                </div>
            ) : filteredCharacters.length === 0 ? (
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
                                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                            />
                        </svg>
                    </div>
                    <h3 className="text-xl font-semibold mb-2">No Characters Yet</h3>
                    <p className="text-surface-400 mb-6 max-w-md mx-auto">
                        Characters are generated when you create an outline for your novel.
                        Start a new project and generate an outline to create characters.
                    </p>
                    <Link href="/" className="btn-primary">
                        Create a New Novel
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredCharacters.map((char) => (
                        <div key={`${char.project_id}-${char.id}`} className="card">
                            <div className="flex items-start gap-4">
                                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-2xl font-bold flex-shrink-0">
                                    {char.name[0]}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <h4 className="font-semibold text-lg truncate">{char.name}</h4>
                                    <p className="text-primary-400 text-sm mb-2">{char.role}</p>
                                    <p className="text-surface-400 text-sm line-clamp-2">{char.bio}</p>
                                    {char.project_title && (
                                        <Link
                                            href={`/projects/${char.project_id}`}
                                            className="text-xs text-surface-500 hover:text-primary-400 mt-2 block"
                                        >
                                            From: {char.project_title}
                                        </Link>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Back to Dashboard */}
            <div className="mt-12 text-center">
                <Link href="/" className="btn-secondary">
                    ← Back to Dashboard
                </Link>
            </div>
        </div>
    )
}
