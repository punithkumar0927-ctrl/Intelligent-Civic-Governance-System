import api from "./api";
import type { Issue, IssueList, IssueFormData } from "../types/issue";

export const reportService = {
  /**
   * GET /api/reports
   * Returns a paginated IssueList matching backend IssueListOut.
   */
  async list(params?: {
    status?: string; severity?: string; category?: string;
    city?: string; page?: number; per_page?: number;
  }): Promise<IssueList> {
    const { data } = await api.get<IssueList>("/reports", { params });
    return data;
  },

  /** GET /api/reports/{id} — returns basic Issue fields (no nested relationships). */
  async get(id: number): Promise<Issue> {
    const { data } = await api.get<Issue>(`/reports/${id}`);
    return data;
  },

  /**
   * POST /api/reports  (multipart/form-data)
   * Field names must match backend `create_report()` Form() parameters exactly.
   */
  async create(form: IssueFormData): Promise<Issue> {
    const fd = new FormData();
    fd.append("title", form.title);
    if (form.description) fd.append("description", form.description);
    fd.append("category", form.category);
    if (form.latitude  !== undefined) fd.append("latitude",  String(form.latitude));
    if (form.longitude !== undefined) fd.append("longitude", String(form.longitude));
    if (form.ward)        fd.append("ward",        form.ward);
    if (form.city)        fd.append("city",        form.city);
    if (form.state)       fd.append("state",       form.state);
    if (form.address_raw) fd.append("address_raw", form.address_raw);
    // Backend field name is "image_before" (not "image")
    if (form.image) fd.append("image_before", form.image);

    const { data } = await api.post<Issue>("/reports", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  /** PATCH /api/reports/{id} */
  async update(id: number, payload: Partial<IssueFormData>): Promise<Issue> {
    const { data } = await api.patch<Issue>(`/reports/${id}`, payload);
    return data;
  },

  /** PATCH /api/reports/{id}/status */
  async changeStatus(id: number, status: string, note?: string): Promise<Issue> {
    const { data } = await api.patch<Issue>(`/reports/${id}/status`, { status, note });
    return data;
  },

  /** POST /api/reports/{id}/evidence */
  async uploadEvidence(id: number, file: File, evidenceType = "IMAGE_OTHER"): Promise<void> {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("evidence_type", evidenceType);
    await api.post(`/reports/${id}/evidence`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};
