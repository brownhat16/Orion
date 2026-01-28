'use client'

import { useState } from 'react'
import { useToast } from '@/context/ToastContext'

interface Character {
    id: number
    name: string
    role: string
    bio: string
    appearance?: string
    personality?: string
}

interface CharacterManagerProps {
    projectId: string
    characters: Character[]
    onUpdate: () => void
}

export default function CharacterManager({ projectId, characters, onUpdate }: CharacterManagerProps) {
    const [editingCharacter, setEditingCharacter] = useState<Character | null>(null)
    const [isCreating, setIsCreating] = useState(false)
    const [loading, setLoading] = useState(false)
    const { success, error } = useToast()

    async function handleDelete(characterId: number) {
        if (!confirm('Are you sure you want to delete this character?')) return

        setLoading(true)
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/characters/${characterId}`, {
                method: 'DELETE',
            })
            if (res.ok) {
                success('Character deleted')
                onUpdate()
            } else {
                error('Failed to delete character')
            }
        } catch (err) {
            console.error('Failed to delete character:', err)
            error('Error deleting character')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold">Cast of Characters</h2>
                <button
                    onClick={() => setIsCreating(true)}
                    className="btn-primary flex items-center gap-2"
                >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add Character
                </button>
            </div>

            {isCreating && (
                <CharacterForm
                    projectId={projectId}
                    onClose={() => setIsCreating(false)}
                    onSaved={() => {
                        setIsCreating(false)
                        onUpdate()
                    }}
                />
            )}

            {characters.length === 0 ? (
                <div className="card text-center py-12">
                    <div className="w-16 h-16 rounded-full bg-surface-800 flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-surface-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                    </div>
                    <p className="text-surface-400">No characters yet. Create one or generate from outline!</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {characters.map((character) => (
                        <div key={character.id} className="card group hover:border-primary-500/30 transition-colors">
                            {editingCharacter?.id === character.id ? (
                                <CharacterForm
                                    projectId={projectId}
                                    character={character}
                                    onClose={() => setEditingCharacter(null)}
                                    onSaved={() => {
                                        setEditingCharacter(null)
                                        onUpdate()
                                    }}
                                />
                            ) : (
                                <div className="flex items-start gap-4">
                                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-2xl font-bold flex-shrink-0">
                                        {character.name[0]}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between">
                                            <div>
                                                <h3 className="font-semibold text-lg truncate">{character.name}</h3>
                                                <p className="text-primary-400 text-sm mb-2">{character.role}</p>
                                            </div>
                                            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={() => setEditingCharacter(character)}
                                                    className="p-1 text-surface-400 hover:text-primary-400"
                                                    title="Edit"
                                                >
                                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                                    </svg>
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(character.id)}
                                                    className="p-1 text-surface-400 hover:text-red-400"
                                                    title="Delete"
                                                >
                                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>
                                        <p className="text-surface-400 text-sm line-clamp-3 mb-2">{character.bio}</p>

                                        {character.appearance && (
                                            <div className="mb-1">
                                                <span className="text-xs font-semibold text-surface-500 uppercase tracking-wider">Appearance</span>
                                                <p className="text-xs text-surface-400 truncate">{character.appearance}</p>
                                            </div>
                                        )}

                                        {character.personality && (
                                            <div>
                                                <span className="text-xs font-semibold text-surface-500 uppercase tracking-wider">Personality</span>
                                                <p className="text-xs text-surface-400 truncate">{character.personality}</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

function CharacterForm({
    projectId,
    character,
    onClose,
    onSaved
}: {
    projectId: string
    character?: Character
    onClose: () => void
    onSaved: () => void
}) {
    const [name, setName] = useState(character?.name || '')
    const [role, setRole] = useState(character?.role || '')
    const [bio, setBio] = useState(character?.bio || '')
    const [appearance, setAppearance] = useState(character?.appearance || '')
    const [personality, setPersonality] = useState(character?.personality || '')
    const [saving, setSaving] = useState(false)
    const { success, error } = useToast()

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        setSaving(true)

        try {
            const url = character
                ? `${process.env.NEXT_PUBLIC_API_URL}/api/characters/${character.id}`
                : `${process.env.NEXT_PUBLIC_API_URL}/api/characters/`

            const method = character ? 'PATCH' : 'POST'

            const body = {
                name,
                role,
                bio,
                appearance,
                personality,
                project_id: parseInt(projectId),
            }

            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            })

            if (res.ok) {
                success(character ? 'Character updated' : 'Character added')
                onSaved()
            } else {
                error('Failed to save character')
            }
        } catch (error) {
            console.error('Failed to save character:', error)
        } finally {
            setSaving(false)
        }
    }

    return (
        <form onSubmit={handleSubmit} className="bg-surface-800/50 p-4 rounded-lg border border-surface-700 animate-in mb-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                    <label className="label">Name</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="input"
                        placeholder="Character Name"
                        required
                    />
                </div>
                <div>
                    <label className="label">Role</label>
                    <input
                        type="text"
                        value={role}
                        onChange={(e) => setRole(e.target.value)}
                        className="input"
                        placeholder="Protagonist, Antagonist, etc."
                        required
                    />
                </div>
            </div>

            <div className="space-y-4">
                <div>
                    <label className="label">Bio / Backstory</label>
                    <textarea
                        value={bio}
                        onChange={(e) => setBio(e.target.value)}
                        className="textarea"
                        rows={3}
                        placeholder="Key background information..."
                        required
                    />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="label">Appearance</label>
                        <textarea
                            value={appearance}
                            onChange={(e) => setAppearance(e.target.value)}
                            className="textarea"
                            rows={2}
                            placeholder="Physical description..."
                        />
                    </div>
                    <div>
                        <label className="label">Personality</label>
                        <textarea
                            value={personality}
                            onChange={(e) => setPersonality(e.target.value)}
                            className="textarea"
                            rows={2}
                            placeholder="Traits, quirks, flaws..."
                        />
                    </div>
                </div>

                <div className="flex justify-end gap-3 pt-2">
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
                        {saving ? 'Saving...' : (character ? 'Update Character' : 'Create Character')}
                    </button>
                </div>
            </div>
        </form>
    )
}
