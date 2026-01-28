'use client'

import Link from 'next/link'

export default function TemplatesPage() {
    const templates = [
        {
            id: 1,
            title: 'Fantasy Epic',
            description: 'Create an epic fantasy saga with magic systems, complex world-building, and heroic quests.',
            genre: 'Fantasy',
            chapters: 25,
            icon: '🏰',
        },
        {
            id: 2,
            title: 'Mystery Thriller',
            description: 'Craft a gripping mystery with plot twists, red herrings, and a satisfying revelation.',
            genre: 'Mystery',
            chapters: 20,
            icon: '🔍',
        },
        {
            id: 3,
            title: 'Romance Novel',
            description: 'Write a heartwarming romance with compelling characters and emotional depth.',
            genre: 'Romance',
            chapters: 18,
            icon: '💕',
        },
        {
            id: 4,
            title: 'Sci-Fi Adventure',
            description: 'Explore futuristic worlds with advanced technology and cosmic adventures.',
            genre: 'Science Fiction',
            chapters: 22,
            icon: '🚀',
        },
        {
            id: 5,
            title: 'Historical Fiction',
            description: 'Transport readers to another era with rich historical detail and authentic characters.',
            genre: 'Historical',
            chapters: 24,
            icon: '📜',
        },
        {
            id: 6,
            title: 'Horror Suspense',
            description: 'Build terrifying tension with atmospheric dread and shocking moments.',
            genre: 'Horror',
            chapters: 16,
            icon: '👻',
        },
    ]

    return (
        <div className="p-8">
            {/* Header */}
            <header className="mb-12">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-2">
                    Story Templates
                </h1>
                <p className="text-surface-400">
                    Choose a template to jumpstart your novel with pre-built structure and genre conventions
                </p>
            </header>

            {/* Coming Soon Banner */}
            <div className="glass-card p-6 mb-8 border border-primary-500/30 bg-primary-500/5">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-primary-500/20 flex items-center justify-center">
                        <svg className="w-6 h-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <div>
                        <h3 className="font-semibold text-primary-400">Coming Soon</h3>
                        <p className="text-surface-400 text-sm">
                            Templates are being refined for the best writing experience. Check back soon!
                        </p>
                    </div>
                </div>
            </div>

            {/* Template Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {templates.map((template) => (
                    <div
                        key={template.id}
                        className="card opacity-60 hover:opacity-80 transition-opacity cursor-not-allowed"
                    >
                        <div className="flex items-start gap-4 mb-4">
                            <div className="w-14 h-14 rounded-xl bg-surface-800 flex items-center justify-center text-3xl">
                                {template.icon}
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold text-lg">{template.title}</h3>
                                <span className="text-xs text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded-full">
                                    {template.genre}
                                </span>
                            </div>
                        </div>
                        <p className="text-surface-400 text-sm mb-4">{template.description}</p>
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-surface-500">{template.chapters} chapters</span>
                            <span className="text-surface-600">Coming Soon</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* Back to Dashboard */}
            <div className="mt-12 text-center">
                <Link href="/" className="btn-secondary">
                    ← Back to Dashboard
                </Link>
            </div>
        </div>
    )
}
