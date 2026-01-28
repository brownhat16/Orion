'use client'

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import { useEffect, useState } from 'react'

interface OutlineEditorProps {
    initialContent?: string
    onSave?: (content: string) => void
    placeholder?: string
    editable?: boolean
}

export default function OutlineEditor({
    initialContent = '',
    onSave,
    placeholder = 'Start writing your outline...',
    editable = true,
}: OutlineEditorProps) {
    const [hasChanges, setHasChanges] = useState(false)

    const editor = useEditor({
        extensions: [
            StarterKit.configure({
                heading: {
                    levels: [1, 2, 3],
                },
            }),
            Placeholder.configure({
                placeholder,
            }),
        ],
        content: initialContent,
        editable,
        onUpdate: ({ editor }) => {
            setHasChanges(true)
        },
    })

    useEffect(() => {
        if (editor && initialContent) {
            editor.commands.setContent(initialContent)
        }
    }, [editor, initialContent])

    function handleSave() {
        if (editor && onSave) {
            onSave(editor.getHTML())
            setHasChanges(false)
        }
    }

    if (!editor) {
        return <div className="tiptap-editor skeleton h-[400px]"></div>
    }

    return (
        <div className="space-y-4">
            {/* Toolbar */}
            {editable && (
                <div className="glass-card p-2 flex items-center gap-1 flex-wrap">
                    <ToolbarButton
                        active={editor.isActive('bold')}
                        onClick={() => editor.chain().focus().toggleBold().run()}
                        title="Bold"
                    >
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M15.6 10.79c.97-.67 1.65-1.77 1.65-2.79 0-2.26-1.75-4-4-4H7v14h7.04c2.09 0 3.71-1.7 3.71-3.79 0-1.52-.86-2.82-2.15-3.42zM10 6.5h3c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5h-3v-3zm3.5 9H10v-3h3.5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5z" />
                        </svg>
                    </ToolbarButton>

                    <ToolbarButton
                        active={editor.isActive('italic')}
                        onClick={() => editor.chain().focus().toggleItalic().run()}
                        title="Italic"
                    >
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M10 4v3h2.21l-3.42 8H6v3h8v-3h-2.21l3.42-8H18V4z" />
                        </svg>
                    </ToolbarButton>

                    <div className="w-px h-6 bg-surface-700 mx-2"></div>

                    <ToolbarButton
                        active={editor.isActive('heading', { level: 1 })}
                        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
                        title="Heading 1"
                    >
                        H1
                    </ToolbarButton>

                    <ToolbarButton
                        active={editor.isActive('heading', { level: 2 })}
                        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
                        title="Heading 2"
                    >
                        H2
                    </ToolbarButton>

                    <ToolbarButton
                        active={editor.isActive('heading', { level: 3 })}
                        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
                        title="Heading 3"
                    >
                        H3
                    </ToolbarButton>

                    <div className="w-px h-6 bg-surface-700 mx-2"></div>

                    <ToolbarButton
                        active={editor.isActive('bulletList')}
                        onClick={() => editor.chain().focus().toggleBulletList().run()}
                        title="Bullet List"
                    >
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M4 10.5c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5 1.5-.67 1.5-1.5-.67-1.5-1.5-1.5zm0-6c-.83 0-1.5.67-1.5 1.5S3.17 7.5 4 7.5 5.5 6.83 5.5 6 4.83 4.5 4 4.5zm0 12c-.83 0-1.5.68-1.5 1.5s.68 1.5 1.5 1.5 1.5-.68 1.5-1.5-.67-1.5-1.5-1.5zM7 19h14v-2H7v2zm0-6h14v-2H7v2zm0-8v2h14V5H7z" />
                        </svg>
                    </ToolbarButton>

                    <ToolbarButton
                        active={editor.isActive('orderedList')}
                        onClick={() => editor.chain().focus().toggleOrderedList().run()}
                        title="Numbered List"
                    >
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M2 17h2v.5H3v1h1v.5H2v1h3v-4H2v1zm1-9h1V4H2v1h1v3zm-1 3h1.8L2 13.1v.9h3v-1H3.2L5 10.9V10H2v1zm5-6v2h14V5H7zm0 14h14v-2H7v2zm0-6h14v-2H7v2z" />
                        </svg>
                    </ToolbarButton>

                    <div className="w-px h-6 bg-surface-700 mx-2"></div>

                    <ToolbarButton
                        active={editor.isActive('blockquote')}
                        onClick={() => editor.chain().focus().toggleBlockquote().run()}
                        title="Quote"
                    >
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M6 17h3l2-4V7H5v6h3zm8 0h3l2-4V7h-6v6h3z" />
                        </svg>
                    </ToolbarButton>

                    <div className="flex-1"></div>

                    {onSave && (
                        <button
                            onClick={handleSave}
                            disabled={!hasChanges}
                            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${hasChanges
                                    ? 'bg-primary-500 text-white hover:bg-primary-600'
                                    : 'bg-surface-700 text-surface-500 cursor-not-allowed'
                                }`}
                        >
                            Save
                        </button>
                    )}
                </div>
            )}

            {/* Editor */}
            <div className="tiptap-editor">
                <EditorContent editor={editor} />
            </div>
        </div>
    )
}

function ToolbarButton({
    active,
    onClick,
    title,
    children,
}: {
    active: boolean
    onClick: () => void
    title: string
    children: React.ReactNode
}) {
    return (
        <button
            onClick={onClick}
            title={title}
            className={`p-2 rounded-lg transition-colors ${active
                    ? 'bg-primary-500/20 text-primary-400'
                    : 'text-surface-400 hover:bg-surface-700 hover:text-surface-200'
                }`}
        >
            {children}
        </button>
    )
}
