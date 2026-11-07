import React from 'react';
import { Link } from 'react-router-dom';
import { MapPin, ThumbsUp, Eye, Brain, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Issue, SEVERITY_COLORS, CATEGORY_LABELS, STATUS_LABELS, SeverityLevel } from '../types';

interface Props { issue: Issue; compact?: boolean }

export default function IssueCard({ issue, compact = false }: Props) {
  const sevColor = SEVERITY_COLORS[issue.severity as SeverityLevel] ?? '#6b7280';

  return (
    <div className="card overflow-hidden hover:border-nexus-300 group">
      <div className="flex">
        {/* Severity color bar */}
        <div className="w-1 flex-shrink-0" style={{ backgroundColor: sevColor }} />

        <div className="flex-1 p-4">
          <div className="flex items-start justify-between gap-2 mb-2">
            <Link
              to={`/issue/${issue.id}`}
              className="font-semibold text-gray-900 group-hover:text-nexus-700 transition-colors line-clamp-2 text-sm"
            >
              {issue.title}
            </Link>
            {issue.is_duplicate && (
              <span className="flex-shrink-0 text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                DUP
              </span>
            )}
          </div>

          <div className="flex flex-wrap gap-1.5 mb-3">
            <span className={`text-xs px-2 py-0.5 rounded border capitalize severity-${issue.severity}`}>
              {issue.severity}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded status-${issue.status}`}>
              {STATUS_LABELS[issue.status]}
            </span>
            <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded capitalize">
              {CATEGORY_LABELS[issue.category] ?? issue.category}
            </span>
          </div>

          {!compact && issue.description && (
            <p className="text-xs text-gray-500 line-clamp-2 mb-3">{issue.description}</p>
          )}

          {/* AI badge */}
          {issue.ai_detected_label && (
            <div className="flex items-center gap-1.5 mb-3 text-xs text-blue-600 bg-blue-50 rounded-lg px-2 py-1.5">
              <Brain size={13} />
              <span>AI: {issue.ai_detected_label}</span>
              {issue.ai_confidence && (
                <span className="ml-auto text-blue-400">
                  {(issue.ai_confidence * 100).toFixed(0)}%
                </span>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between text-xs text-gray-400">
            <div className="flex items-center gap-3">
              {issue.city && (
                <span className="flex items-center gap-1">
                  <MapPin size={12} /> {issue.city}
                </span>
              )}
              <span className="flex items-center gap-1">
                <ThumbsUp size={12} /> {issue.upvotes}
              </span>
              <span className="flex items-center gap-1">
                <Eye size={12} /> {issue.view_count}
              </span>
            </div>
            <div className="flex items-center gap-1">
              {issue.status === 'resolved' || issue.status === 'verified_resolved'
                ? <CheckCircle2 size={13} className="text-green-500" />
                : <AlertTriangle size={13} style={{ color: sevColor }} />
              }
              <span>{new Date(issue.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
