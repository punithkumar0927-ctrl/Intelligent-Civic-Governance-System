import { useState, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../hooks/useAuthStore";

export default function Register() {
  const { register, isLoading, error } = useAuthStore();
  const nav = useNavigate();
  const [form, setForm] = useState({
    username: "", email: "", password: "", confirm: "",
    full_name: "", phone: "", city: "", ward: "",
  });
  const [localError, setLocalError] = useState("");
  const [accepted, setAccepted] = useState(false);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError("");
    if (form.password !== form.confirm) {
      setLocalError("Passwords do not match");
      return;
    }
    if (!/^(?=.*[A-Za-z])(?=.*\d).{8,}$/.test(form.password)) {
      setLocalError("Password must be at least 8 characters and include a letter and a number");
      return;
    }
    if (!accepted) {
      setLocalError("Accept the terms and privacy notice to create an account");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      setLocalError("Invalid email address");
      return;
    }
    try {
      const created = await register({
        username: form.username,
        email: form.email,
        password: form.password,
        full_name: form.full_name || undefined,
        phone: form.phone || undefined,
      });
      nav("/verify-email", { state: { token: created.dev_verification_token } });
    } catch {
      // error is in store
    }
  };

  const err = localError || error;

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12 bg-gray-50">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-md border border-gray-200 p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Create Your Account</h1>
        <p className="text-gray-500 text-sm mb-6">
          Join NEXUS AI to report issues, track resolution, and help your community.
        </p>

        {err && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {err}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Username *" value={form.username} onChange={(v) => set("username", v)} />
            <Field label="Full Name" value={form.full_name} onChange={(v) => set("full_name", v)} />
          </div>
          <Field label="Email *" type="email" value={form.email} onChange={(v) => set("email", v)} />
          <div className="grid grid-cols-2 gap-4">
            <Field label="Password *" type="password" value={form.password} onChange={(v) => set("password", v)} />
            <Field label="Confirm Password *" type="password" value={form.confirm} onChange={(v) => set("confirm", v)} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Phone" value={form.phone} onChange={(v) => set("phone", v)} />
            <Field label="City" value={form.city} onChange={(v) => set("city", v)} />
          </div>
          <Field label="Ward / Locality" value={form.ward} onChange={(v) => set("ward", v)} />

          <label className="flex items-start gap-2 text-sm text-gray-600">
            <input type="checkbox" checked={accepted} onChange={(e) => setAccepted(e.target.checked)} className="mt-1" />
            I accept the privacy notice and agree not to submit false reports.
          </label>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-indigo-700 text-white font-bold py-3 rounded-xl hover:bg-indigo-600 disabled:opacity-50 transition"
          >
            {isLoading ? "Creating account..." : "Register"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-500">
          Already have an account?{" "}
          <Link to="/login" className="text-indigo-600 font-semibold hover:underline">Sign in</Link>
        </p>

        <div className="mt-6 pt-4 border-t border-gray-100 text-xs text-gray-400 space-y-1">
          <p>Your data is never sold or shared. Coordinates are rounded to ~111m for public display.</p>
          <p>By registering you agree to the community guidelines: no false reports, no person accusations.</p>
        </div>
      </div>
    </div>
  );
}

function Field({
  label, value, onChange, type = "text",
}: {
  label: string; value: string; onChange: (v: string) => void; type?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
      />
    </div>
  );
}
