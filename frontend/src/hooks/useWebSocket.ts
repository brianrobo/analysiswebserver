import { useEffect, useRef, useState, useCallback } from 'react'
import type { WsMessage, JobStatus } from '@/api/types'

interface WsState {
  progress: number
  status: JobStatus | null
  message: string
  isConnected: boolean
  error: string | null
}

export function useWebSocket(
  jobId: number | null,
  enabled: boolean = true,
  onCompleted?: () => void
) {
  const wsRef = useRef<WebSocket | null>(null)
  const [state, setState] = useState<WsState>({
    progress: 0,
    status: null,
    message: '',
    isConnected: false,
    error: null,
  })

  const connect = useCallback(() => {
    if (!jobId || !enabled) return
    const token = localStorage.getItem('access_token')
    if (!token) return

    if (wsRef.current) {
      wsRef.current.close()
    }

    // Direct WebSocket connection (not through Vite proxy - more reliable on Windows)
    const wsUrl = `ws://localhost:8000/ws/analysis/${jobId}?token=${token}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setState((prev) => ({ ...prev, isConnected: true, error: null }))
    }

    ws.onmessage = (event: MessageEvent) => {
      const msg: WsMessage = JSON.parse(event.data as string)

      switch (msg.type) {
        case 'connected':
          setState((prev) => ({
            ...prev,
            status: (msg.status as JobStatus) ?? prev.status,
            progress: msg.progress ?? prev.progress,
          }))
          break
        case 'progress':
          setState((prev) => ({
            ...prev,
            progress: msg.progress ?? prev.progress,
            status: (msg.status as JobStatus) ?? prev.status,
            message: msg.message ?? prev.message,
          }))
          break
        case 'completed':
          setState((prev) => ({
            ...prev,
            progress: 100,
            status: 'completed',
            message: '분석이 완료되었습니다.',
          }))
          onCompleted?.()
          break
        case 'error':
          setState((prev) => ({
            ...prev,
            status: 'failed',
            error: msg.error ?? '알 수 없는 오류가 발생했습니다.',
          }))
          break
        case 'ping':
          ws.send(JSON.stringify({ type: 'pong' }))
          break
      }
    }

    ws.onerror = () => {
      setState((prev) => ({
        ...prev,
        error: 'WebSocket 연결 오류가 발생했습니다.',
        isConnected: false,
      }))
    }

    ws.onclose = () => {
      setState((prev) => ({ ...prev, isConnected: false }))
    }
  }, [jobId, enabled, onCompleted])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [connect])

  return state
}
