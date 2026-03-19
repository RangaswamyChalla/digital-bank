/**
 * useWebSocket Hook for Real-time Updates
 * Manages WebSocket connections for live data updates
 */

import { useEffect, useRef, useCallback } from 'react'

const useWebSocket = (url, options = {}, onMessage, onError, onClose) => {
  const { token = null } = typeof options === 'object' ? options : { token: options }
  const ws = useRef(null)
  const reconnectAttempts = useRef(0)
  const MAX_RECONNECT_ATTEMPTS = 5
  const RECONNECT_INTERVAL = 3000

  const buildUrl = useCallback(() => {
    // If token is provided, append as query param
    if (token) {
      const separator = url.includes('?') ? '&' : '?'
      return `${url}${separator}token=${encodeURIComponent(token)}`
    }
    return url
  }, [url, token])

  const connect = useCallback(() => {
    if (ws.current) return

    try {
      const wsUrl = buildUrl()
      ws.current = new WebSocket(wsUrl)

      ws.current.onopen = () => {
        console.log(`WebSocket connected: ${wsUrl}`)
        reconnectAttempts.current = 0
        // Send initial ping
        ws.current.send(JSON.stringify({ type: 'ping' }))
      }

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          onMessage?.(message)
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        onError?.(error)
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        ws.current = null
        onClose?.()

        // Attempt reconnect
        if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttempts.current++
          console.log(`Reconnecting... (${reconnectAttempts.current}/${MAX_RECONNECT_ATTEMPTS})`)
          setTimeout(() => connect(), RECONNECT_INTERVAL)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      onError?.(error)
    }
  }, [buildUrl, onMessage, onError, onClose])

  const send = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close()
      ws.current = null
    }
  }, [])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return { send, disconnect, isConnected: ws.current?.readyState === WebSocket.OPEN }
}

export default useWebSocket
