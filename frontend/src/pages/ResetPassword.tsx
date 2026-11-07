import { FormEvent, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../services/api';

export default function ResetPassword() {
  const [params] = useSearchParams();
  const [token, setToken] = useState(params.get('token') || '');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    if (!/^(?=.*[A-Za-z])(?=.*\d).{8,}$/.test(password)) {
      setError('Use at least 8 characters, including a letter and a number.');
      return;
    }
    try {
      const { data } = await api.post('/auth/reset-password', { token, password });
      setMessage(data.detail);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'This reset link is invalid or expired.');
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <h1 className="text-2xl font-bold text-gray-900">Choose a new password</h1>
      <form onSubmit={submit} className="mt-6 space-y-4 rounded-2xl border border-gray-200 bg-white p-6">
        <label className="block text-sm font-medium text-gray-700">
          Reset token
          <input value={token} onChange={(event) => setToken(event.target.value)} required className="mt-1 w-full rounded-lg border px-3 py-2" />
        </label>
        <label className="block text-sm font-medium text-gray-700">
          New password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required className="mt-1 w-full rounded-lg border px-3 py-2" />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {message && <p className="text-sm text-emerald-700">{message}</p>}
        <button className="w-full rounded-xl bg-indigo-700 py-3 font-semibold text-white">Update password</button>
      </form>
      <p className="mt-4 text-center text-sm"><Link to="/login" className="text-indigo-700">Sign in</Link></p>
    </div>
  );
}
