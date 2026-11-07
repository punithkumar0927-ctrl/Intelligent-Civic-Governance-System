import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapPin, Send, Brain, AlertCircle } from 'lucide-react';
import { reportApi } from '../services/api';
import { IssueCategory, CATEGORY_LABELS } from '../types';
import UploadPanel from '../components/UploadPanel';

export default function ReportIssue() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [imageBefore, setImageBefore] = useState<File | null>(null);
  const [imageAfter, setImageAfter] = useState<File | null>(null);
  const [gettingLocation, setGettingLocation] = useState(false);

  const [form, setForm] = useState({
    title: '',
    description: '',
    category: 'pothole' as IssueCategory,
    latitude: '' as string,
    longitude: '' as string,
    ward: '',
    city: '',
    state: '',
    address_raw: '',
  });

  const setField = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const getCurrentLocation = () => {
    if (!navigator.geolocation) { setError('Geolocation not supported'); return; }
    setGettingLocation(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm((f) => ({
          ...f,
          latitude: pos.coords.latitude.toFixed(5),
          longitude: pos.coords.longitude.toFixed(5),
        }));
        setGettingLocation(false);
      },
      (err) => { setError('Location access denied: ' + err.message); setGettingLocation(false); },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!form.title.trim() || form.title.length < 5) {
      setError('Title must be at least 5 characters'); return;
    }
    setLoading(true);
    try {
      const issue = await reportApi.create(
        {
          ...form,
          latitude: form.latitude ? parseFloat(form.latitude) : undefined,
          longitude: form.longitude ? parseFloat(form.longitude) : undefined,
        },
        imageBefore ?? undefined,
        imageAfter ?? undefined,
      );
      navigate(`/issue/${issue.id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? 'Failed to submit report';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <MapPin size={24} className="text-nexus-600" /> Report an Issue
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Photo + description are analyzed by AI to detect category, severity, and duplicates automatically.
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-700">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">

        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Issue Title * <span className="text-gray-400 font-normal">(short, clear summary)</span>
          </label>
          <input
            className="input-field"
            placeholder="e.g. Large pothole near school gate on MG Road"
            value={form.title}
            onChange={(e) => setField('title', e.target.value)}
            maxLength={200}
            required
          />
          <div className="text-xs text-gray-400 mt-1">{form.title.length}/200</div>
        </div>

        {/* Category */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
          <select
            className="input-field"
            value={form.category}
            onChange={(e) => setField('category', e.target.value)}
          >
            {Object.entries(CATEGORY_LABELS).map(([v, l]) => (
              <option key={v} value={v}>{l}</option>
            ))}
          </select>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description <span className="text-gray-400 font-normal">(detail helps AI accuracy)</span>
          </label>
          <textarea
            className="input-field h-28 resize-none"
            placeholder="Describe the issue: how big, where exactly, how long it's been there, any danger to people/vehicles..."
            value={form.description}
            onChange={(e) => setField('description', e.target.value)}
            maxLength={2000}
          />
          <div className="text-xs text-gray-400 mt-1">{form.description.length}/2000</div>
        </div>

        {/* Location */}
        <div className="card p-4 space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <MapPin size={16} className="text-nexus-600" /> Location
            </label>
            <button
              type="button"
              onClick={getCurrentLocation}
              disabled={gettingLocation}
              className="text-xs btn-secondary py-1 px-2 text-nexus-600 border-nexus-200"
            >
              {gettingLocation ? 'Getting...' : '📍 Use my GPS'}
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <input
              className="input-field text-sm"
              placeholder="Latitude"
              value={form.latitude}
              onChange={(e) => setField('latitude', e.target.value)}
              type="number"
              step="0.00001"
            />
            <input
              className="input-field text-sm"
              placeholder="Longitude"
              value={form.longitude}
              onChange={(e) => setField('longitude', e.target.value)}
              type="number"
              step="0.00001"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <input className="input-field text-sm" placeholder="Ward / Area"
              value={form.ward} onChange={(e) => setField('ward', e.target.value)} />
            <input className="input-field text-sm" placeholder="City"
              value={form.city} onChange={(e) => setField('city', e.target.value)} />
            <input className="input-field text-sm" placeholder="State"
              value={form.state} onChange={(e) => setField('state', e.target.value)} />
          </div>

          <input
            className="input-field text-sm"
            placeholder="Full street address (optional)"
            value={form.address_raw}
            onChange={(e) => setField('address_raw', e.target.value)}
          />
        </div>

        {/* Images */}
        <div className="card p-4 space-y-4">
          <div className="text-sm font-medium text-gray-700 flex items-center gap-2">
            <Brain size={16} className="text-nexus-600" /> Evidence Photos (AI analyzed)
          </div>
          <UploadPanel label="Before / Current Photo" onFileSelect={setImageBefore} value={imageBefore} />
          <UploadPanel label="After Photo (if resolved — for verification)" onFileSelect={setImageAfter} value={imageAfter} />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="btn-primary w-full flex items-center justify-center gap-2 py-3"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
              Analyzing with AI...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Send size={18} /> Submit Report
            </span>
          )}
        </button>
      </form>
    </div>
  );
}
