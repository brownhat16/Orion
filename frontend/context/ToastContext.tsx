'use client'

import React, { createContext, useContext, useState, ReactNode } from 'react'
import Toast, { ToastMessage, ToastType } from '@/components/Toast'

interface ToastContextType {
    showToast: (message: string, type?: ToastType, duration?: number) => void
    success: (message: string, duration?: number) => void
    error: (message: string, duration?: number) => void
    info: (message: string, duration?: number) => void
    warning: (message: string, duration?: number) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<ToastMessage[]>([])

    function showToast(message: string, type: ToastType = 'info', duration = 3000) {
        const id = Math.random().toString(36).substr(2, 9)
        setToasts((prev) => [...prev, { id, message, type, duration }])
    }

    function removeToast(id: string) {
        setToasts((prev) => prev.filter((t) => t.id !== id))
    }

    const contextValue = {
        showToast,
        success: (msg: string, dur?: number) => showToast(msg, 'success', dur),
        error: (msg: string, dur?: number) => showToast(msg, 'error', dur),
        info: (msg: string, dur?: number) => showToast(msg, 'info', dur),
        warning: (msg: string, dur?: number) => showToast(msg, 'warning', dur),
    }

    return (
        <ToastContext.Provider value={contextValue}>
            {children}
            <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end pointer-events-none">
                {toasts.map((toast) => (
                    <Toast key={toast.id} toast={toast} onClose={removeToast} />
                ))}
            </div>
        </ToastContext.Provider>
    )
}

export function useToast() {
    const context = useContext(ToastContext)
    if (context === undefined) {
        throw new Error('useToast must be used within a ToastProvider')
    }
    return context
}
