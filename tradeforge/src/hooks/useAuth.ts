"use client"

import { useState, useEffect, useCallback, useRef, type ReactNode } from "react"
import { api, setTokens, clearTokens, getRefreshToken } from "@/lib/api"

export type AuthUser = {
  id: number
  email: string
  name: string
  plan: string
}

type AuthState = {
  user: AuthUser | null
  loading: boolean
}

const LS_KEY = "fingraph_access_token"

function readToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem(LS_KEY)
}

const AuthContext = React.createContext<{
  user: AuthUser | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, name: string) => Promise<void>
  signOut: () => void
  refreshAccessToken: () => Promise<void>
} | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, loading: true })
  const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const fetchMe = useCallback(async (token: string | null) => {
    if (!token) {
      setState({ user: null, loading: false })
      return null
    }
    try {
      const res = await api.get<{ authenticated: boolean; id: number; email: string; name: string; plan: string }>(
        "/api/v1/auth/me",
        { token },
      )
      if (res.authenticated) {
        const user: AuthUser = { id: res.id, email: res.email, name: res.name, plan: res.plan }
        setState({ user, loading: false })
        return user
      }
      setState({ user: null, loading: false })
      return null
    } catch {
      setState({ user: null, loading: false })
      return null
    }
  }, [])

  useEffect(() => {
    const token = readToken()
    if (token) {
      fetchMe(token)
    } else {
      setState((s) => ({ ...s, loading: false }))
    }
  }, [fetchMe])

  const refreshAccessToken = useCallback(async () => {
    const rt = getRefreshToken()
    if (!rt) return
    try {
      const res = await api.post<{ data: { access_token: string; refresh_token: string } }>(
        "/api/v1/auth/refresh",
        { refresh_token: rt },
        { token: undefined },
      )
      setTokens(res.data.access_token, res.data.refresh_token)
      if (refreshTimer.current) clearTimeout(refreshTimer.current)
      refreshTimer.current = setTimeout(refreshAccessToken, 12 * 60 * 1000)
    } catch {
      clearTokens()
      setState({ user: null, loading: false })
    }
  }, [])

  useEffect(() => {
    if (state.user) {
      refreshTimer.current = setTimeout(refreshAccessToken, 12 * 60 * 1000)
    }
    return () => {
      if (refreshTimer.current) clearTimeout(refreshTimer.current)
    }
  }, [state.user, refreshAccessToken])

  const signIn = useCallback(async (email: string, password: string) => {
    const res = await api.post<{
      data: { access_token: string; refresh_token: string; user: { id: number; email: string; name: string; plan: string } }
    }>("/api/v1/auth/login", { email, password })
    setTokens(res.data.access_token, res.data.refresh_token)
    const user: AuthUser = {
      id: res.data.user.id,
      email: res.data.user.email,
      name: res.data.user.name,
      plan: res.data.user.plan,
    }
    setState({ user, loading: false })
  }, [])

  const signUp = useCallback(async (email: string, password: string, name: string) => {
    const res = await api.post<{
      data: { access_token: string; refresh_token: string; user: { id: number; email: string; name: string; plan: string } }
    }>("/api/v1/auth/signup", { email, password, name })
    setTokens(res.data.access_token, res.data.refresh_token)
    const user: AuthUser = {
      id: res.data.user.id,
      email: res.data.user.email,
      name: res.data.user.name,
      plan: res.data.user.plan,
    }
    setState({ user, loading: false })
  }, [])

  const signOut = useCallback(() => {
    clearTokens()
    setState({ user: null, loading: false })
  }, [])

  return React.createElement(AuthContext.Provider, {
    value: { user: state.user, loading: state.loading, signIn, signUp, signOut, refreshAccessToken },
  }, children)
}

export function useAuth() {
  const ctx = React.useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}

import React from "react"
