"use client"

import { createClient } from "@/lib/supabase/client"
import type { User } from "@/types"
import { useRouter } from "next/navigation"
import { useEffect, useState, useRef, useCallback } from "react"

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const supabaseRef = useRef<ReturnType<typeof createClient>>(undefined)

  const getClient = useCallback(() => {
    if (!supabaseRef.current) {
      supabaseRef.current = createClient()
    }
    return supabaseRef.current
  }, [])

  useEffect(() => {
    const supabase = getClient()
    if (!supabase) {
      setLoading(false)
      return
    }

    const getUser = async () => {
      const { data: { user: authUser } } = await supabase.auth.getUser()
      if (authUser) {
        const { data: profile } = await supabase
          .from("profiles")
          .select("*")
          .eq("id", authUser.id)
          .single()
        setUser({
          id: authUser.id,
          email: authUser.email ?? "",
          name: profile?.name ?? authUser.user_metadata?.full_name ?? null,
          avatar_url: profile?.avatar_url ?? authUser.user_metadata?.avatar_url ?? null,
          plan: profile?.plan ?? "free",
          created_at: authUser.created_at,
        })
      }
      setLoading(false)
    }
    getUser()

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        if (session?.user) {
          const { data: profile } = await supabase
            .from("profiles")
            .select("*")
            .eq("id", session.user.id)
            .single()
          setUser({
            id: session.user.id,
            email: session.user.email ?? "",
            name: profile?.name ?? session.user.user_metadata?.full_name ?? null,
            avatar_url: profile?.avatar_url ?? session.user.user_metadata?.avatar_url ?? null,
            plan: profile?.plan ?? "free",
            created_at: session.user.created_at,
          })
        } else {
          setUser(null)
        }
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [getClient])

  const requireClient = () => {
    const supabase = getClient()
    if (!supabase) throw new Error("Supabase not configured. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to your .env.local")
    return supabase
  }

  const signIn = async (email: string, password: string) => {
    const supabase = requireClient()
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
    router.push("/dashboard")
  }

  const signUp = async (email: string, password: string, name: string) => {
    const supabase = requireClient()
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: name } },
    })
    if (error) throw error
  }

  const signOut = async () => {
    const supabase = getClient()
    if (supabase) await supabase.auth.signOut()
    setUser(null)
    router.push("/")
  }

  const signInWithGoogle = async () => {
    const supabase = requireClient()
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    })
    if (error) throw error
  }

  const signInWithGitHub = async () => {
    const supabase = requireClient()
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "github",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    })
    if (error) throw error
  }

  return {
    user,
    loading,
    signIn,
    signUp,
    signOut,
    signInWithGoogle,
    signInWithGitHub,
  }
}
