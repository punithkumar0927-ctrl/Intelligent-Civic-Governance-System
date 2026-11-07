import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [devToken, setDevToken] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const { data } = await api.post('/auth/forgot-password', { email });
      setMessage(data.detail);
      setDevToken(data.dev_token || '');
    } catch {
      setError('The reset request could not be sent.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <h1 className="text-2xl font-bold text-gray-900">Reset your password</h1>
      <p className="mt-2 text-sm text-gray-500">
        Enter the email on your account. The response is the same whether or not that email is registered.
      </p>
      <form onSubmit={submit} className="mt-6 space-y-4 rounded-2xl border border-gray-200 bg-white p-6">
        <label className="block text-sm font-medium text-gray-700">
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
          />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {message && <p className="text-sm text-gray-700">{message}</p>}
        {devToken && (
          <p className="text-sm text-indigo-700">
            Development reset link:{' '}
            <Link className="underline" to={`/reset-password?token=${encodeURIComponent(devToken)}`}>
              set a new password
            </Link>
          </p>
        )}
        <button disabled={loading} className="w-full rounded-xl bg-indigo-700 py-3 font-semibold text-white">
          {loading ? 'Sending…' : 'Send reset link'}
        </button>
      </form>
      <p className="mt-4 text-center text-sm">
        <Link to="/login" className="text-indigo-700">Back to sign in</Link>
      </p>
    </div>
  );
}
