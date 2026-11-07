import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { verificationService } from "../services/verificationService";
import BeforeAfterViewer from "../components/BeforeAfterViewer";
import { useAuthStore } from "../hooks/useAuthStore";

export default function RepairVerification() {
  const { user } = useAuthStore();
  const qc = useQueryClient();
  const [selectedIssue, setSelectedIssue] = useState<number | null>(null);
  const [afterFile, setAfterFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const fileRef = useRef<HTMLInputElement>(null);

  const isOfficer = user?.role === "officer" || user?.role === "admin";

  // Only fetch review queue for officers (endpoint requires officer/admin role)
  const { data: pending = [], isLoading } = useQuery({
    queryKey: ["verification-pending"],
    queryFn: () => verificationService.pendingReview(30),
    enabled: isOfficer,
  });

  const reviewMut = useMutation({
    mutationFn: ({ id, approve, note }: { id: number; approve: boolean; note?: string }) =>
      verificationService.review(id, approve, note),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["verification-pending"] }),
  });

  const submitMut = useMutation({
    mutationFn: ({ issueId, file }: { issueId: number; file: File }) =>
      verificationService.submitAfterPhoto(issueId, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["verification-pending"] });
      setAfterFile(null);
      setPreview("");
      setSelectedIssue(null);
    },
  });

  const onFileChange = (f: File | null) => {
    setAfterFile(f);
    if (f) {
      const url = URL.createObjectURL(f);
      setPreview(url);
    }
  };

  return (
    <div className="max-w-screen-xl mx-auto px-6 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Repair Verification</h1>
        <p className="text-gray-500 mt-1">
          AI-assisted before/after comparison to confirm that repairs were actually completed.
        </p>
      </div>

      {/* Submit after photo */}
      <section className="bg-white border border-gray-200 rounded-2xl p-6">
        <h2 className="font-semibold text-gray-800 mb-4">Upload After-Repair Photo</h2>
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Issue ID</label>
            <input
              type="number"
              value={selectedIssue ?? ""}
              onChange={(e) => setSelectedIssue(Number(e.target.value) || null)}
              placeholder="e.g. 42"
              className="w-32 px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">After Photo</label>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
              className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 file:mr-3 file:rounded file:border-0 file:bg-indigo-50 file:px-3 file:py-1 file:text-indigo-700"
            />
          </div>
          <button
            disabled={!selectedIssue || !afterFile || submitMut.isPending}
            onClick={() => selectedIssue && afterFile && submitMut.mutate({ issueId: selectedIssue, file: afterFile })}
            className="bg-indigo-700 text-white px-6 py-2 rounded-lg font-semibold text-sm disabled:opacity-40 hover:bg-indigo-600 transition"
          >
            {submitMut.isPending ? "Analyzing..." : "Run AI Comparison"}
          </button>
        </div>

        {submitMut.data && (
          <div className="mt-6 p-4 bg-gray-50 rounded-xl space-y-3">
            <p className="text-sm font-semibold text-gray-700">
              Result: <span className={
                submitMut.data.verification_status.includes("FIXED") ? "text-green-700" :
                submitMut.data.verification_status.includes("REVIEW") ? "text-amber-700" :
                "text-red-700"
              }>{submitMut.data.verification_status}</span>
            </p>
            {submitMut.data.ai_recommendation && (
              <p className="text-sm text-gray-600">{submitMut.data.ai_recommendation}</p>
            )}
            {preview && (
              <img src={preview} alt="Uploaded after photo"
                className="w-48 h-36 object-cover rounded-lg border" />
            )}
          </div>
        )}

        {submitMut.error instanceof Error && (
          <p className="mt-3 text-sm text-red-600">{submitMut.error.message}</p>
        )}
      </section>

      {/* Pending review queue (officer only) */}
      {isOfficer && (
        <section className="bg-white border border-gray-200 rounded-2xl p-6">
          <h2 className="font-semibold text-gray-800 mb-4">
            Human Review Queue
            <span className="ml-2 text-xs bg-amber-100 text-amber-800 rounded-full px-2 py-0.5">
              {pending.length} pending
            </span>
          </h2>

          {isLoading ? (
            <p className="text-gray-400 text-sm">Loading...</p>
          ) : pending.length === 0 ? (
            <p className="text-gray-400 text-sm">No items need manual review.</p>
          ) : (
            <div className="space-y-4">
              {pending.map((item) => (
                <ReviewCard key={item.resolution_id} item={item} onAction={
                  (approve, note) => reviewMut.mutate({ id: item.resolution_id, approve, note })
                } loading={reviewMut.isPending} />
              ))}
            </div>
          )}
        </section>
      )}

      {/* Verification metrics */}
      <VerificationSummary />
    </div>
  );
}

function ReviewCard({
  item, onAction, loading,
}: {
  item: Awaited<ReturnType<typeof verificationService.pendingReview>>[0];
  onAction: (approve: boolean, note?: string) => void;
  loading: boolean;
}) {
  const [note, setNote] = useState("");
  return (
    <div className="border border-gray-100 rounded-xl p-4 space-y-3">
      <div className="flex items-center gap-3 text-sm">
        <span className="font-bold text-indigo-700">#{item.issue_id}</span>
        <span className="text-gray-500">SSIM: {item.ssim_score?.toFixed(3)}</span>
        <span className="text-gray-500">Confidence: {Math.round((item.resolved_probability ?? 0) * 100)}%</span>
        <span className={`ml-auto text-xs font-bold ${
          item.verification_status.includes("REVIEW") ? "text-amber-600" : "text-red-600"
        }`}>{item.verification_status}</span>
      </div>
      {item.ai_recommendation && (
        <p className="text-xs text-gray-500 italic">{item.ai_recommendation}</p>
      )}
      <div className="flex gap-2 items-center">
        <input value={note} onChange={(e) => setNote(e.target.value)}
          placeholder="Officer note (optional)" className="flex-1 px-3 py-1.5 border border-gray-200 rounded text-sm" />
        <button disabled={loading} onClick={() => onAction(true, note)}
          className="bg-green-600 text-white px-3 py-1.5 rounded text-sm font-semibold hover:bg-green-500">
          Approve
        </button>
        <button disabled={loading} onClick={() => onAction(false, note)}
          className="bg-red-600 text-white px-3 py-1.5 rounded text-sm font-semibold hover:bg-red-500">
          Reject
        </button>
      </div>
    </div>
  );
}

function VerificationSummary() {
  const { data: summary } = useQuery({
    queryKey: ["verification-summary"],
    queryFn: verificationService.summary,
  });
  if (!summary) return null;
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {[
        { label: "Pending", value: summary.total_pending, color: "text-amber-600" },
        { label: "Verified", value: summary.total_verified, color: "text-green-600" },
        { label: "Rejected", value: summary.total_rejected, color: "text-red-600" },
        { label: "Avg Confidence", value: `${Math.round(summary.avg_confidence * 100)}%`, color: "text-indigo-600" },
        { label: "Verification Rate", value: `${summary.verification_rate}%`, color: "text-blue-600" },
      ].map((s) => (
        <div key={s.label} className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className={`text-2xl font-extrabold ${s.color}`}>{s.value}</p>
          <p className="text-xs text-gray-500 mt-1">{s.label}</p>
        </div>
      ))}
    </div>
  );
}
