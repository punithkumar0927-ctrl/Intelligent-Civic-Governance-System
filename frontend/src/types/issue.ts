/**
 * types/issue.ts – types aligned with backend schemas.schemas.py
 * Enum values use lowercase strings exactly as the backend IssueCategory /
 * IssueStatus / SeverityLevel enums emit them.
 */
import type { User } from "./index";

// ── Enums (match backend IssueCategory / IssueStatus / SeverityLevel) ─────────
export type Severity = "low" | "medium" | "high" | "critical";

export type IssueStatus =
  | "pending" | "under_review" | "in_progress"
  | "resolution_submitted" | "verified_resolved"
  | "resolved" | "rejected" | "duplicate";

export type IssueCategory =
  | "road_damage" | "pothole" | "garbage" | "streetlight"
  | "water_leak" | "drainage" | "sidewalk" | "traffic_sign"
  | "park" | "building" | "power_line" | "other";

// ── Core Issue (matches IssueOut) ─────────────────────────────────────────────
export interface Issue {
  id:                number;
  title:             string;
  description?:      string;
  category:          IssueCategory;
  status:            IssueStatus;
  severity:          Severity;
  severity_score:    number;
  latitude?:         number;
  longitude?:        number;
  ward?:             string;
  city?:             string;
  ai_detected_label?: string;
  ai_confidence?:    number;
  is_duplicate:      boolean;
  upvotes:           number;
  view_count:        number;
  reporter:          User;
  created_at:        string;
  updated_at?:       string;
}

export interface IssueList {
  items:    Issue[];
  total:    number;
  page:     number;
  per_page: number;
}

// ── Issue detail with relationships ───────────────────────────────────────────
export interface IssueDetail extends Issue {
  evidences:  Evidence[];
  resolution?: Resolution;
  location?:   IssueLocation;
}

// ── Evidence ──────────────────────────────────────────────────────────────────
export interface Evidence {
  id:              number;
  issue_id:        number;
  evidence_type:   "IMAGE_BEFORE" | "IMAGE_AFTER" | "IMAGE_OTHER" | "DOCUMENT";
  file_url:        string;
  thumbnail_url?:  string;
  caption?:        string;
  created_at:      string;
}

// ── Resolution / Repair verification ──────────────────────────────────────────
export interface Resolution {
  id:                   number;
  issue_id:             number;
  status:               string;
  resolved_probability?: number;
  ssim_score?:          number;
  edge_reduction_pct?:  number;
  officer_note?:        string;
  human_verified?:      boolean;
  verified_at?:         string;
}

// ── Geographic location enrichment ────────────────────────────────────────────
export interface IssueLocation {
  id:               number;
  issue_id:         number;
  latitude:         number;
  longitude:        number;
  road_name?:       string;
  place_name?:      string;
  landmark_type?:   string;
  landmark_name?:   string;
  risk_score?:      number;
  is_high_risk_zone?: boolean;
  geocoded?:        boolean;
}

// ── Form data sent when creating a new report ─────────────────────────────────
export interface IssueFormData {
  title:        string;
  description?: string;
  category:     IssueCategory;
  latitude?:    number;
  longitude?:   number;
  ward?:        string;
  city?:        string;
  state?:       string;
  address_raw?: string;
  image?:       File;   // primary photo → sent as "image_before" to backend
}

// ── Colour / label constants ──────────────────────────────────────────────────
export const SEVERITY_COLORS: Record<Severity, string> = {
  low:      "#22c55e",
  medium:   "#f59e0b",
  high:     "#ef4444",
  critical: "#7c3aed",
};

export const CATEGORY_LABELS: Record<IssueCategory, string> = {
  road_damage:  "Road Damage",
  pothole:      "Pothole",
  garbage:      "Garbage / Waste",
  streetlight:  "Streetlight Fault",
  water_leak:   "Water Pipe Leak",
  drainage:     "Drainage Blockage",
  sidewalk:     "Sidewalk / Footpath",
  traffic_sign: "Traffic Sign",
  park:         "Public Park",
  building:     "Municipal Building",
  power_line:   "Power Line",
  other:        "Other Civic Issue",
};

export const STATUS_LABELS: Record<IssueStatus, string> = {
  pending:      "Pending",
  under_review: "Under Review",
  in_progress:  "In Progress",
  resolution_submitted: "Resolution Submitted",
  verified_resolved: "Human Verified",
  resolved:     "Resolved",
  rejected:     "Rejected",
  duplicate:    "Duplicate",
};
