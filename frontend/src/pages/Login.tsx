import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Brain, Mail, Lock, User, Phone, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { useAuthStore } from '../hooks/useAuthStore';

type Mode = 'login' | 'register';

export default function Login() {
  const [mode, setMode] = useState<Mode>('login');
  const [showPass, setShowPass] = useState(false);
  const [remember, setRemember] = useState(true);
  const [form, setForm] = useState({
    username: '', email: '', password: '', full_name: '', phone: '',
  });
  const { login, register, isLoading, error } = useAuthStore();
  const navigate = useNavigate();

  const handle = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (mode === 'login') {
        await login(form.email, form.password, remember);
        navigate('/dashboard');
      } else {
        const created = await register({
          username: form.username,
          email: form.email,
          password: form.password,
          full_name: form.full_name || undefined,
          phone: form.phone || undefined,
        });
        navigate('/verify-email', { state: { token: created.dev_verification_token } });
      }
    } catch {
      // error shown from store
    }
  };

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 bg-nexus-600 text-white rounded-2xl px-5 py-3 mb-4">
            <Brain size={28} />
            <span className="font-bold text-2xl tracking-tight">NEXUS AI</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900">
            {mode === 'login' ? 'Welcome back' : 'Create your account'}
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            {mode === 'login'
              ? 'Sign in to report and track urban issues'
              : 'Join the intelligence map for your city'}
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-700">
            <AlertCircle size={16} /> {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handle} className="card p-6 space-y-4">
          {mode === 'register' && (
            <>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Username</label>
                <div className="relative">
                  <User size={16} className="absolute left-3 top-3 text-gray-400" />
                  <input
                    className="input-field pl-9"
                    placeholder="johndoe"
                    value={form.username}
                    onChange={(e) => set('username', e.target.value)}
                    required minLength={3} maxLength={50}
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Full Name (optional)</label>
                <input
                  className="input-field"
                  placeholder="John Doe"
                  value={form.full_name}
                  onChange={(e) => set('full_name', e.target.value)}
                />
              </div>
            </>
          )}

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Email</label>
            <div className="relative">
              <Mail size={16} className="absolute left-3 top-3 text-gray-400" />
              <input
                className="input-field pl-9"
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={(e) => set('email', e.target.value)}
                required
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Password</label>
            <div className="relative">
              <Lock size={16} className="absolute left-3 top-3 text-gray-400" />
              <input
                className="input-field pl-9 pr-10"
                type={showPass ? 'text' : 'password'}
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => set('password', e.target.value)}
                required minLength={8}
              />
              <button
                type="button"
                onClick={() => setShowPass(!showPass)}
                className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
              >
                {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {mode === 'register' && (
              <p className="text-xs text-gray-400 mt-1">At least 8 characters, including a letter and a number</p>
            )}
            {mode === 'login' && (
              <div className="mt-2 flex items-center justify-between text-xs">
                <label className="flex items-center gap-2 text-gray-600">
                  <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
                  Remember me
                </label>
                <Link to="/forgot-password" className="text-nexus-600">Forgot password?</Link>
              </div>
            )}
          </div>

          {mode === 'register' && (
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                Phone <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <div className="relative">
                <Phone size={16} className="absolute left-3 top-3 text-gray-400" />
                <input
                  className="input-field pl-9"
                  placeholder="+91 98765 43210"
                  value={form.phone}
                  onChange={(e) => set('phone', e.target.value)}
                  maxLength={15}
                />
              </div>
            </div>
          )}

          <button type="submit" disabled={isLoading} className="btn-primary w-full py-2.5">
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                {mode === 'login' ? 'Signing in...' : 'Creating account...'}
              </span>
            ) : (
              mode === 'login' ? 'Sign In' : 'Create Account'
            )}
          </button>
        </form>

        {/* Toggle mode */}
        <p className="text-center text-sm text-gray-500 mt-4">
          {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}{' '}
          <button
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); }}
            className="text-nexus-600 font-medium hover:underline"
          >
            {mode === 'login' ? 'Register' : 'Sign In'}
          </button>
        </p>
      </div>
    </div>
  );
}
