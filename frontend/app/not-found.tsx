'use client'

import Link from 'next/link'

export default function NotFound() {
    return (
        <div className="min-h-screen flex items-center justify-center p-8">
            <div className="text-center max-w-lg">
                {/* 404 Icon */}
                <div className="w-32 h-32 rounded-full bg-gradient-to-br from-primary-500/10 to-accent-500/10 flex items-center justify-center mx-auto mb-8">
                    <svg
                        className="w-16 h-16 text-primary-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1.5}
                            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>
                </div>

                {/* Error Message */}
                <h1 className="text-6xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-4">
                    404
                </h1>
                <h2 className="text-2xl font-semibold text-surface-200 mb-4">
                    Page Not Found
                </h2>
                <p className="text-surface-400 mb-8">
                    The page you're looking for doesn't exist or has been moved.
                    Don't worry, let's get you back on track.
                </p>

                {/* Navigation Options */}
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                    <Link href="/" className="btn-primary w-full sm:w-auto">
                        <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                        </svg>
                        Go to Dashboard
                    </Link>
                    <button
                        onClick={() => window.history.back()}
                        className="btn-secondary w-full sm:w-auto"
                    >
                        <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                        Go Back
                    </button>
                </div>

                {/* Help Links */}
                <div className="mt-12 pt-8 border-t border-surface-800">
                    <p className="text-surface-500 text-sm mb-4">Looking for something specific?</p>
                    <div className="flex flex-wrap items-center justify-center gap-4 text-sm">
                        <Link href="/" className="text-primary-400 hover:text-primary-300 transition-colors">
                            Dashboard
                        </Link>
                        <span className="text-surface-700">•</span>
                        <Link href="/templates" className="text-primary-400 hover:text-primary-300 transition-colors">
                            Templates
                        </Link>
                        <span className="text-surface-700">•</span>
                        <Link href="/characters" className="text-primary-400 hover:text-primary-300 transition-colors">
                            Characters
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    )
}
