'use client'

import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
    children: ReactNode
}

interface State {
    hasError: boolean
    error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    }

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error }
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo)
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div className="flex flex-col items-center justify-center min-h-screen p-4 text-center bg-surface-900 text-surface-50">
                    <div className="p-8 bg-surface-800 rounded-xl shadow-2xl max-w-md w-full border border-surface-700">
                        <h2 className="text-2xl font-bold text-red-400 mb-4">Something went wrong</h2>
                        <p className="text-surface-300 mb-6">
                            We're sorry, but an unexpected error occurred. Please try refreshing the page.
                        </p>
                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <pre className="text-xs bg-surface-950 p-4 rounded text-left overflow-auto mb-6 text-red-300 max-h-40">
                                {this.state.error.toString()}
                            </pre>
                        )}
                        <button
                            onClick={() => window.location.reload()}
                            className="btn-primary w-full"
                        >
                            Refresh Page
                        </button>
                    </div>
                </div>
            )
        }

        return this.props.children
    }
}
