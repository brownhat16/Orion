'use client'

import Link from 'next/link'

export default function WorldBuildingPage() {
    const features = [
        {
            icon: '🗺️',
            title: 'Maps & Locations',
            description: 'Create interactive maps with locations, regions, and points of interest.',
        },
        {
            icon: '⏳',
            title: 'Timelines',
            description: 'Build historical timelines and track events across your story world.',
        },
        {
            icon: '🔮',
            title: 'Magic Systems',
            description: 'Define rules, limitations, and costs for magic or technology systems.',
        },
        {
            icon: '👥',
            title: 'Factions & Organizations',
            description: 'Create groups, their goals, hierarchies, and relationships.',
        },
        {
            icon: '📖',
            title: 'Lore & History',
            description: 'Document myths, legends, and historical events that shape your world.',
        },
        {
            icon: '🔗',
            title: 'Relationship Maps',
            description: 'Visualize connections between characters, places, and events.',
        },
    ]

    return (
        <div className="p-8">
            {/* Header */}
            <header className="mb-12">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-2">
                    World Building
                </h1>
                <p className="text-surface-400">
                    Create rich, immersive worlds with interconnected lore, locations, and systems
                </p>
            </header>

            {/* Coming Soon Banner */}
            <div className="glass-card p-8 mb-12 border border-accent-500/30 bg-accent-500/5 text-center">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center mx-auto mb-6">
                    <svg className="w-10 h-10 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <h2 className="text-2xl font-bold mb-3">World Building Tools Coming Soon</h2>
                <p className="text-surface-400 max-w-lg mx-auto mb-6">
                    We're building powerful tools to help you create deep, consistent worlds for your stories.
                    This feature is currently in development.
                </p>
                <div className="flex items-center justify-center gap-4">
                    <Link href="/" className="btn-primary">
                        Return to Dashboard
                    </Link>
                </div>
            </div>

            {/* Feature Preview */}
            <h3 className="text-xl font-semibold mb-6">Planned Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {features.map((feature, i) => (
                    <div
                        key={i}
                        className="card opacity-60"
                    >
                        <div className="text-4xl mb-4">{feature.icon}</div>
                        <h4 className="font-semibold mb-2">{feature.title}</h4>
                        <p className="text-surface-400 text-sm">{feature.description}</p>
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
