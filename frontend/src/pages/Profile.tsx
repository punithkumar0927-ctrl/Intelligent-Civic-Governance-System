import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import { useAuthStore } from '../hooks/useAuthStore';
import api from '../services/api';

export default function Profile() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [phone, setPhone] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const save = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    try {
      const { data } = await api.patch('/auth/me', { full_name: fullName, phone: phone || undefined });
      localStorage.setItem('nexus_user', JSON.stringify(data));
      setMessage('Profile saved.');
    } catch {
      setError('Profile could not be saved.');
    }
  };

  const changePassword = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    try {
      const { data } = await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setMessage(data.detail);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Password was not changed.');
    }
  };

  const removeAccount = async () => {
    if (!window.confirm('Deactivate this account and remove the stored name, phone, and email?')) return;
    await api.delete('/auth/me');
    await logout();
    navigate('/');
  };

  return (
    <AppLayout>
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Account</p>
        <h1 className="mt-1 text-2xl font-semibold text-white">My profile</h1>
      </header>
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 text-sm text-slate-300">
        <p>Email: {user?.email}</p>
        <p className="mt-1">Role: {user?.role}</p>
        <p className="mt-1">Joined: {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</p>
      </section>
      {message && <p className="text-sm text-emerald-300">{message}</p>}
      {error && <p className="text-sm text-rose-300">{error}</p>}
      <form onSubmit={save} className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <h2 className="font-medium text-white">Profile</h2>
        <input value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Full name" className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="Phone" className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <button className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950">Save</button>
      </form>
      <form onSubmit={changePassword} className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <h2 className="font-medium text-white">Password</h2>
        <input type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} placeholder="Current password" className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <input type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} placeholder="New password" className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" />
        <button className="rounded-xl border border-slate-600 px-4 py-2 text-sm">Change password</button>
      </form>
      <button onClick={removeAccount} className="text-sm text-rose-300">Request account deletion</button>
    </AppLayout>
  );
}
