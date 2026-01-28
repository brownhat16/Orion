'use client'

import './globals.css'
import { Inter, Crimson_Text } from 'next/font/google'
import Image from 'next/image'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const inter = Inter({
    subsets: ['latin'],
    variable: '--font-sans',
})

const crimson = Crimson_Text({
    weight: ['400', '600'],
    subsets: ['latin'],
    variable: '--font-serif',
})

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const pathname = usePathname()

    return (
        <html lang="en" className={`${inter.variable} ${crimson.variable}`}>
            <head>
                <title>Orion - AI Novel Writing Engine</title>
                <meta name="description" content="Transform your ideas into complete novels with AI-powered storytelling" />
            </head>
            <body className="flex min-h-screen">
                {/* Animated Star Background */}
                <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
                    <div className="stars"></div>
                    <div className="stars2"></div>
                    <div className="stars3"></div>
                </div>

                {/* Sidebar */}
                <aside className="fixed left-0 top-0 h-full w-72 glass border-r border-white/10 z-50 flex flex-col">
                    {/* Logo */}
                    <div className="p-6 border-b border-white/10">
                        <Link href="/" className="flex items-center gap-3 group">
                            <div className="relative w-12 h-12 transition-transform group-hover:scale-110">
                                <Image
                                    src="/orion-logo.png"
                                    alt="Orion"
                                    fill
                                    className="object-contain"
                                    priority
                                />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                                    Orion
                                </h1>
                                <p className="text-xs text-surface-500">Novel Writing Engine</p>
                            </div>
                        </Link>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 p-4 space-y-2">
                        <Link href="/" className={`sidebar-item ${pathname === '/' ? 'active' : ''}`}>
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                            </svg>
                            <span>Dashboard</span>
                        </Link>

                        <Link href="/projects" className={`sidebar-item ${pathname?.startsWith('/projects') ? 'active' : ''}`}>
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                            </svg>
                            <span>My Novels</span>
                        </Link>

                        <Link href="/templates" className={`sidebar-item ${pathname === '/templates' ? 'active' : ''}`}>
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                            </svg>
                            <span>Templates</span>
                        </Link>

                        <div className="pt-6 pb-2">
                            <p className="px-4 text-xs font-semibold text-surface-600 uppercase tracking-wider">Tools</p>
                        </div>

                        <Link href="/characters" className={`sidebar-item ${pathname === '/characters' ? 'active' : ''}`}>
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                            <span>Characters</span>
                        </Link>

                        <Link href="/worldbuilding" className={`sidebar-item ${pathname === '/worldbuilding' ? 'active' : ''}`}>
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>World Building</span>
                        </Link>
                    </nav>

                    {/* Bottom Section */}
                    <div className="p-4 border-t border-white/10">
                        <div className="glass-card p-4 bg-gradient-to-br from-cyan-500/10 to-blue-500/10">
                            <div className="flex items-center gap-3 mb-3">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center">
                                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                    </svg>
                                </div>
                                <div>
                                    <p className="text-sm font-medium">Powered by</p>
                                    <p className="text-xs text-cyan-400">NVIDIA NIM</p>
                                </div>
                            </div>
                            <p className="text-xs text-surface-400">
                                Llama 3.1 405B for world-class novel generation
                            </p>
                        </div>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="flex-1 ml-72 relative z-10">
                    {children}
                </main>
            </body>
        </html>
    )
}
