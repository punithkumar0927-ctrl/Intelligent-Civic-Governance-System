export type IssueCategory =
  | 'road_damage' | 'pothole' | 'garbage' | 'streetlight'
  | 'water_leak' | 'drainage' | 'sidewalk' | 'traffic_sign'
  | 'park' | 'building' | 'power_line' | 'other';

export type IssueStatus =
  | 'pending' | 'under_review' | 'in_progress'
  | 'resolution_submitted' | 'verified_resolved'
  | 'resolved' | 'rejected' | 'duplicate';

export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: 'citizen' | 'officer' | 'admin' | 'gp_official' | 'taluk_official' | 'zilla_official';
  created_at: string;
}

export interface Issue {
  id: number;
  title: string;
  description?: string;
  category: IssueCategory;
  status: IssueStatus;
  severity: SeverityLevel;
  severity_score: number;
  latitude?: number;
  longitude?: number;
  ward?: string;
  city?: string;
  ai_detected_label?: string;
  ai_confidence?: number;
  is_duplicate: boolean;
  upvotes: number;
  view_count: number;
  reporter: User;
  created_at: string;
  updated_at?: string;
}

export interface IssueList {
  items: Issue[];
  total: number;
  page: number;
  per_page: number;
}

export interface Evidence {
  id: number;
  issue_id: number;
  evidence_type: string;
  file_name: string;
  file_url?: string;
  yolo_label?: string;
  yolo_confidence?: number;
  verified: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_issues: number;
  active_issues: number;
  high_severity_issues: number;
  resolved_issues: number;
  verified_resolutions: number;
  duplicate_reports: number;
  ai_detection_accuracy: number | null;
  demo_data: boolean;
  pending_issues: number;
  critical_issues: number;
  avg_resolution_days: number;
  resolution_rate: number;
  by_category: { category: string; count: number }[];
  by_status: { status: string; count: number }[];
  by_severity: { severity: string; count: number }[];
  geo_points: {
    id: number; lat: number; lon: number;
    severity: string; category: string; status: string;
  }[];
}

export interface AIAnalysisResult {
  issue_id: number;
  detected_label?: string;
  confidence?: number;
  severity_score: number;
  severity_level: SeverityLevel;
  duplicate_detected: boolean;
  duplicate_of_id?: number;
  recommendation?: string;
  analysis_complete: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export interface ReportFormData {
  title: string;
  description?: string;
  category: IssueCategory;
  latitude?: number;
  longitude?: number;
  ward?: string;
  city?: string;
  state?: string;
  address_raw?: string;
}

export const CATEGORY_LABELS: Record<IssueCategory, string> = {
  road_damage: 'Road Damage',
  pothole: 'Pothole',
  garbage: 'Garbage / Waste',
  streetlight: 'Streetlight',
  water_leak: 'Water Leak',
  drainage: 'Drainage / Sewage',
  sidewalk: 'Sidewalk',
  traffic_sign: 'Traffic Sign',
  park: 'Public Park',
  building: 'Building Defect',
  power_line: 'Power Line',
  other: 'Other Issue',
};

export const SEVERITY_COLORS: Record<SeverityLevel, string> = {
  low: '#22c55e',
  medium: '#eab308',
  high: '#f97316',
  critical: '#ef4444',
};

export const STATUS_LABELS: Record<IssueStatus, string> = {
  pending: 'Pending',
  under_review: 'Under Review',
  in_progress: 'In Progress',
  resolution_submitted: 'Resolution Submitted',
  verified_resolved: 'Human Verified',
  resolved: 'Resolved',
  rejected: 'Rejected',
  duplicate: 'Duplicate',
};
