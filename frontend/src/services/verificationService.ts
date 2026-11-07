import api from "./api";

/** Matches backend verification_schema.VerificationResult. */
export interface VerificationResult {
  resolution_id:        number;
  issue_id:             number;
  ssim_score?:          number;
  edge_density_before?: number;
  edge_density_after?:  number;
  edge_reduction?:      number;
  brightness_delta?:    number;
  resolved_probability?: number;
  ai_recommendation?:   string;
  verification_status:  string;
  human_verified:       boolean;
  officer_note?:        string;
  verified_at?:         string;
  created_at:           string;
}

/** Matches backend verification_schema.BeforeAfterPair. */
export interface BeforeAfterPair {
  resolution_id:        number;
  issue_id:             number;
  title:                string;
  category:             string;
  severity:             string;
  before_image_url?:    string;
  after_image_url?:     string;
  resolved_probability?: number;
  ssim_score?:          number;
  ai_recommendation?:   string;
  verification_status:  string;
}

export interface VerificationSummary {
  total_pending:     number;
  total_verified:    number;
  total_rejected:    number;
  avg_confidence:    number;
  verification_rate: number;
}

export const verificationService = {
  /**
   * POST /api/verification/issue/{issue_id}
   * Backend expects form field name "after_image" (UploadFile).
   */
  async submitAfterPhoto(issueId: number, file: File): Promise<VerificationResult> {
    const fd = new FormData();
    fd.append("after_image", file);   // ← must match backend parameter name
    const { data } = await api.post<VerificationResult>(
      `/verification/issue/${issueId}`, fd,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return data;
  },

  /**
   * PATCH /api/verification/{resolution_id}
   * Sends a VerificationUpdate body: { verification_status, officer_note, human_verified }.
   * @param approve  true → CONFIRMED_FIXED, false → REJECTED
   */
  async review(resolutionId: number, approve: boolean, note?: string): Promise<VerificationResult> {
    const { data } = await api.patch<VerificationResult>(`/verification/${resolutionId}`, {
      verification_status: approve ? "confirmed_fixed" : "rejected",
      human_verified:      true,
      officer_note:        note || undefined,
    });
    return data;
  },

  /** GET /api/verification/pending-review — returns BeforeAfterPair list. */
  async pendingReview(limit = 20): Promise<BeforeAfterPair[]> {
    const { data } = await api.get<BeforeAfterPair[]>("/verification/pending-review", {
      params: { limit },
    });
    return data;
  },

  /** GET /api/verification/summary. */
  async summary(): Promise<VerificationSummary> {
    const { data } = await api.get<VerificationSummary>("/verification/summary");
    return data;
  },

  /** GET /api/verification/issue/{issue_id} — all verification records for an issue. */
  async forIssue(issueId: number): Promise<VerificationResult[]> {
    const { data } = await api.get<VerificationResult[]>(`/verification/issue/${issueId}`);
    return data;
  },
};
