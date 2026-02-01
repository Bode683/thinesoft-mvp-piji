'use client'

import React from 'react'

interface TranslationErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface TranslationErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

/**
 * Error boundary to catch translation-related errors
 * Prevents the entire app from crashing if translations fail to load
 */
export class TranslationErrorBoundary extends React.Component<
  TranslationErrorBoundaryProps,
  TranslationErrorBoundaryState
> {
  constructor(props: TranslationErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): TranslationErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Translation Error Boundary caught an error:', error, errorInfo)
    }

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      // Render custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default fallback UI
      return (
        <div
          style={{
            padding: '20px',
            margin: '20px',
            border: '1px solid #ff6b6b',
            borderRadius: '8px',
            backgroundColor: '#ffe0e0',
            color: '#c92a2a',
          }}
        >
          <h2 style={{ margin: '0 0 10px 0', fontSize: '18px' }}>Translation Error</h2>
          <p style={{ margin: '0', fontSize: '14px' }}>
            {process.env.NODE_ENV === 'development'
              ? `Failed to load translations: ${this.state.error?.message}`
              : 'Failed to load translations. Please refresh the page.'}
          </p>
          {process.env.NODE_ENV === 'development' && (
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              style={{
                marginTop: '10px',
                padding: '8px 16px',
                backgroundColor: '#c92a2a',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Try Again
            </button>
          )}
        </div>
      )
    }

    return this.props.children
  }
}
