'use client'

import { useEffect, useState, useRef } from 'react'

interface ProgressViewProps {
    projectId: number
    onComplete?: () => void
}

interface ProgressData {
    phase: string
    chapter: number
    beat?: number
    total_beats?: number
    message?: string
}

export default function ProgressView({ projectId, onComplete }: ProgressViewProps) {
    const [connected, setConnected] = useState(false)
    const [progress, setProgress] = useState<ProgressData | null>(null)
    const [logs, setLogs] = useState<string[]>([])
    const wsRef = useRef<WebSocket | null>(null)
    const logsEndRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        // Connect to WebSocket
        const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}`)

        ws.onopen = () => {
            setConnected(true)
            addLog('Connected to generation server')
        }

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data)
            handleMessage(data)
        }

        ws.onclose = () => {
            setConnected(false)
            addLog('Disconnected from server')
        }

        ws.onerror = () => {
            addLog('Connection error')
        }

        wsRef.current = ws

        return () => {
            ws.close()
        }
    }, [projectId])

    useEffect(() => {
        // Auto-scroll logs
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [logs])

    function addLog(message: string) {
        const timestamp = new Date().toLocaleTimeString()
        setLogs(prev => [...prev.slice(-100), `[${timestamp}] ${message}`])
    }

    function handleMessage(data: any) {
        switch (data.type) {
            case 'progress':
                setProgress(data.data)
                addLog(`Chapter ${data.data.chapter}: ${data.data.message || data.data.phase}`)
                break

            case 'chapter_complete':
                addLog(`✓ Chapter ${data.data.chapter} complete (${data.data.word_count} words)`)
                break

            case 'error':
                addLog(`✗ Error: ${data.data.error}`)
                break

            case 'complete':
                addLog(`✓ Generation complete! ${data.data.total_words} words across ${data.data.total_chapters} chapters`)
                onComplete?.()
                break

            case 'heartbeat':
                // Ignore heartbeats
                break

            default:
                addLog(`Received: ${data.type}`)
        }
    }

    return (
        <div className="glass-card">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <h3 className="card-title">Generation Progress</h3>
                <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                    <span className="text-sm text-surface-400">
                        {connected ? 'Connected' : 'Disconnected'}
                    </span>
                </div>
            </div>

            {/* Progress Display */}
            {progress && (
                <div className="mb-6 space-y-4">
                    <div className="flex items-center justify-between">
                        <span className="text-surface-300">Phase</span>
                        <span className="font-medium text-primary-400">{progress.phase}</span>
                    </div>

                    {progress.chapter && (
                        <>
                            <div className="flex items-center justify-between">
                                <span className="text-surface-300">Chapter</span>
                                <span className="font-medium">{progress.chapter}</span>
                            </div>

                            {progress.beat !== undefined && progress.total_beats && (
                                <>
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-surface-400">Beat Progress</span>
                                        <span className="text-surface-400">
                                            {progress.beat} / {progress.total_beats}
                                        </span>
                                    </div>
                                    <div className="progress-bar">
                                        <div
                                            className="progress-fill"
                                            style={{ width: `${(progress.beat / progress.total_beats) * 100}%` }}
                                        ></div>
                                    </div>
                                </>
                            )}
                        </>
                    )}
                </div>
            )}

            {/* Activity Log */}
            <div className="border-t border-surface-800 pt-4">
                <h4 className="text-sm font-medium text-surface-400 mb-3">Activity Log</h4>
                <div className="bg-surface-950 rounded-lg p-3 h-48 overflow-y-auto font-mono text-xs">
                    {logs.length === 0 ? (
                        <p className="text-surface-600">Waiting for activity...</p>
                    ) : (
                        logs.map((log, i) => (
                            <p key={i} className="text-surface-400 mb-1">{log}</p>
                        ))
                    )}
                    <div ref={logsEndRef}></div>
                </div>
            </div>

            {/* Animated Writing Indicator */}
            {connected && progress?.phase === 'beat_writing' && (
                <div className="mt-6 flex items-center gap-3 text-surface-400">
                    <div className="flex gap-1">
                        <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                        <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                        <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </div>
                    <span className="text-sm">AI is writing...</span>
                </div>
            )}
        </div>
    )
}
