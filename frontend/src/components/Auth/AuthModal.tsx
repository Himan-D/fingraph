import { useState } from 'react'
import { X, Mail, Lock, User, Loader2 } from 'lucide-react'
import { authAPI } from '../../services/api'

interface AuthModalProps {
  mode: 'login' | 'signup'
  onClose: () => void
  onSuccess: (data: { access_token: string; refresh_token: string; user: { id: number; email: string; name: string; plan: string } }) => void
}

export default function AuthModal({ mode, onClose, onSuccess }: AuthModalProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = mode === 'login'
        ? await authAPI.login(email, password)
        : await authAPI.signup(email, password, name)

      if (res.data.success) {
        localStorage.setItem('access_token', res.data.data.access_token)
        localStorage.setItem('refresh_token', res.data.data.refresh_token)
        onSuccess(res.data.data)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center backdrop-blur-sm">
      <div className="bg-terminal-card border border-terminal-border rounded-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold">
            {mode === 'login' ? 'Welcome back' : 'Create account'}
          </h2>
          <button onClick={onClose} className="p-1 hover:bg-terminal-border rounded">
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'signup' && (
            <div className="relative">
              <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-terminal-muted" />
              <input
                type="text"
                placeholder="Full name"
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-terminal-bg border border-terminal-border rounded-lg text-sm focus:border-terminal-accent outline-none"
                required
              />
            </div>
          )}

          <div className="relative">
            <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-terminal-muted" />
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-terminal-bg border border-terminal-border rounded-lg text-sm focus:border-terminal-accent outline-none"
              required
            />
          </div>

          <div className="relative">
            <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-terminal-muted" />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-terminal-bg border border-terminal-border rounded-lg text-sm focus:border-terminal-accent outline-none"
              required
              minLength={6}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-terminal-accent text-white rounded-lg hover:bg-terminal-accent/90 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                {mode === 'login' ? 'Signing in...' : 'Creating account...'}
              </>
            ) : (
              mode === 'login' ? 'Sign in' : 'Create account'
            )}
          </button>
        </form>

        <p className="text-sm text-terminal-muted text-center mt-4">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button className="text-terminal-accent hover:underline">
            {mode === 'login' ? 'Sign up' : 'Sign in'}
          </button>
        </p>
      </div>
    </div>
  )
}
