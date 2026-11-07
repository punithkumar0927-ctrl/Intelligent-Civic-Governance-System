import { FormEvent, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import api from '../services/api';

export default function VerifyEmail() {
  const location = useLocation();
  const initial = (location.state as { token?: string } | null)?.token || '';
  const [token, setToken] = useState(initial);
  const [message, setMessage] = useState(initial ? 'A development verification token is ready below.' : 'Paste the token from your verification message.');
  const [error, setError] = useState('');

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    try {
      const { data } = await api.post('/auth/verify-email', { token });
      setMessage(data.detail);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Verification failed.');
    }
  };

  const resend = async () => {
    setError('');
    try {
      const { data } = await api.post('/auth/resend-verification');
      setMessage(data.detail);
      if (data.dev_token) setToken(data.dev_token);
    } catch {
      setError('Sign in first, then request a new verification message.');
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <h1 className="text-2xl font-bold text-gray-900">Verify your email</h1>
      <p className="mt-2 text-sm text-gray-600">{message}</p>
      <form onSubmit={submit} className="mt-6 space-y-4 rounded-2xl border border-gray-200 bg-white p-6">
        <label className="block text-sm font-medium text-gray-700">
          Verification token
          <textarea value={token} onChange={(event) => setToken(event.target.value)} required className="mt-1 w-full rounded-lg border px-3 py-2" rows={3} />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="w-full rounded-xl bg-indigo-700 py-3 font-semibold text-white">Verify</button>
        <button type="button" onClick={resend} className="w-full rounded-xl border py-3 text-sm font-semibold text-gray-700">
          Send a new verification message
        </button>
      </form>
      <p className="mt-4 text-center text-sm"><Link to="/dashboard" className="text-indigo-700">Continue to dashboard</Link></p>
    </div>
  );
}
