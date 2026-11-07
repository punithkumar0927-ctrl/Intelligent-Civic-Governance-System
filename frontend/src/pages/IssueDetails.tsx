import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft, Brain, MapPin, ThumbsUp, AlertTriangle,
  CheckCircle2, Clock, Calendar, Eye, Shield, Lightbulb
} from 'lucide-react';
import { reportApi } from '../services/api';
import { Issue, Evidence, SEVERITY_COLORS, CATEGORY_LABELS, STATUS_LABELS, SeverityLevel } from '../types';
import MapView from '../components/MapView';

export default function IssueDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const issueId = parseInt(id ?? '0');

  const { data: issue, isLoading, error } = useQuery({
    queryKey: ['issue', issueId],
    queryFn: () => reportApi.get(issueId),
    enabled: issueId > 0,
  });

  const { data: evidence } = useQuery({
    queryKey: ['evidence', issueId],
    queryFn: () => reportApi.getEvidence(issueId),
    enabled: issueId > 0,
  });

  const upvoteMut = useMutation({
    mutationFn: () => reportApi.upvote(issueId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['issue', issueId] }),
  });

  if (isLoading) return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-4">
      {[1,2,3,4].map(i => <div key={i} className="card h-24 animate-pulse bg-gray-100" />)}
    </div>
  );

  if (error || !issue) return (
    <div className="max-w-4xl mx-auto px-4 py-16 text-center">
      <AlertTriangle size={48} className="mx-auto text-gray-300 mb-4" />
      <p className="text-gray-500 mb-4">Issue not found or could not be loaded.</p>
      <Link to="/" className="btn-primary">Back to Dashboard</Link>
    </div>
  );

  const sevColor = SEVERITY_COLORS[issue.severity as SeverityLevel] ?? '#6b7280';
  const beforeImg = evidence?.find(e => e.evidence_type === 'image_before');
  const afterImg  = evidence?.find(e => e.evidence_type === 'image_after');

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">

      {/* Back nav */}
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900">
        <ArrowLeft size={16} /> Back
      </button>

      {/* Header */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row justify-between gap-4">
          <div>
            <div className="flex flex-wrap gap-2 mb-2">
              <span className={`text-xs px-2.5 py-1 rounded-full border capitalize severity-${issue.severity}`}>
                {issue.severity}
              </span>
              <span className={`text-xs px-2.5 py-1 rounded-full status-${issue.status}`}>
                {STATUS_LABELS[issue.status]}
              </span>
              <span className="text-xs px-2.5 py-1 rounded-full bg-gray-100 text-gray-600 capitalize">
                {CATEGORY_LABELS[issue.category] ?? issue.category}
              </span>
              {issue.is_duplicate && (
                <span className="text-xs px-2.5 py-1 rounded-full bg-purple-100 text-purple-700">
                  Duplicate Detected
                </span>
              )}
            </div>
            <h1 className="text-xl font-bold text-gray-900">{issue.title}</h1>
            {issue.description && (
              <p className="text-sm text-gray-600 mt-2 leading-relaxed">{issue.description}</p>
            )}
          </div>
          <div className="flex flex-col items-end gap-3 flex-shrink-0">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <Calendar size={13} />
              {new Date(issue.created_at).toLocaleDateString('en-IN', {
                day: 'numeric', month: 'long', year: 'numeric'
              })}
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <Eye size={13} /> {issue.view_count} views
            </div>
            <button
              onClick={() => upvoteMut.mutate()}
              disabled={upvoteMut.isPending}
              className="btn-secondary flex items-center gap-1.5 text-sm"
            >
              <ThumbsUp size={14} /> {issue.upvotes}
            </button>
          </div>
        </div>
      </div>

      {/* AI Analysis */}
      {issue.ai_detected_label && (
        <div className="card p-5 border-blue-200 bg-blue-50">
          <h2 className="font-semibold text-blue-900 flex items-center gap-2 mb-3">
            <Brain size={18} /> AI Analysis
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-blue-400 text-xs mb-1">Detected Label</div>
              <div className="font-medium capitalize text-blue-900">{issue.ai_detected_label}</div>
            </div>
            <div>
              <div className="text-blue-400 text-xs mb-1">Confidence</div>
              <div className="font-medium text-blue-900">
                {issue.ai_confidence ? `${(issue.ai_confidence * 100).toFixed(1)}%` : '—'}
              </div>
            </div>
            <div>
              <div className="text-blue-400 text-xs mb-1">Severity Score</div>
              <div className="font-medium text-blue-900">{(issue.severity_score * 100).toFixed(1)}%</div>
            </div>
            <div>
              <div className="text-blue-400 text-xs mb-1">Reporter</div>
              <div className="font-medium text-blue-900">@{issue.reporter.username}</div>
            </div>
          </div>
        </div>
      )}

      {/* Resolution badge */}
      {issue.status === 'resolved' && (
        <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-xl p-4">
          <CheckCircle2 size={22} className="text-green-500 flex-shrink-0" />
          <div>
            <div className="font-medium text-green-800">This issue has been resolved</div>
            {issue.reporter.full_name && (
              <div className="text-sm text-green-600">Closed by {issue.reporter.full_name}</div>
            )}
          </div>
        </div>
      )}

      {/* Before/After images */}
      {(beforeImg || afterImg) && (
        <div className="card p-5">
          <h2 className="font-semibold text-gray-800 mb-4">Evidence Photos</h2>
          <div className="grid grid-cols-2 gap-4">
            {beforeImg && (
              <div>
                <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                  <AlertTriangle size={12} /> Before
                </div>
                <img
                  src={`/uploads/${beforeImg.file_name}`}
                  alt="before"
                  className="w-full h-48 object-cover rounded-lg border"
                  onError={(e) => { (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect fill="%23f3f4f6" width="400" height="300"/><text fill="%239ca3af" font-size="14" x="50%" y="50%" text-anchor="middle">Image not available</text></svg>'; }}
                />
              </div>
            )}
            {afterImg && (
              <div>
                <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                  <CheckCircle2 size={12} /> After
                </div>
                <img
                  src={`/uploads/${afterImg.file_name}`}
                  alt="after"
                  className="w-full h-48 object-cover rounded-lg border"
                  onError={(e) => { (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect fill="%23f3f4f6" width="400" height="300"/><text fill="%239ca3af" font-size="14" x="50%" y="50%" text-anchor="middle">Image not available</text></svg>'; }}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Map */}
      {issue.latitude && issue.longitude && (
        <div className="card p-5">
          <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <MapPin size={18} className="text-nexus-600" /> Location
          </h2>
          <MapView
            points={[{
              id: issue.id, lat: issue.latitude, lon: issue.longitude,
              severity: issue.severity, category: issue.category, status: issue.status,
            }]}
            center={[issue.latitude, issue.longitude]}
            zoom={15}
            height="280px"
          />
          <div className="mt-3 text-sm text-gray-500 space-y-1">
            {issue.ward  && <div>Ward: {issue.ward}</div>}
            {issue.city  && <div>City: {issue.city}</div>}
            <div>Coords: {issue.latitude.toFixed(4)}, {issue.longitude.toFixed(4)}</div>
          </div>
        </div>
      )}
    </div>
  );
}
