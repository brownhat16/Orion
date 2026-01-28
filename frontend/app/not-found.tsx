import Link from 'next/link'

export default function NotFound() {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen p-4 text-center">
            <h1 className="text-6xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-4">
                404
            </h1>
            <h2 className="text-2xl font-semibold mb-4 text-surface-200">Page Not Found</h2>
            <p className="text-surface-400 mb-8 max-w-md">
                The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
            </p>
            <Link href="/" className="btn-primary">
                Return to Dashboard
            </Link>
        </div>
    )
}
