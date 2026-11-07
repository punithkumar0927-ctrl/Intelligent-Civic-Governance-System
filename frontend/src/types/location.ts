export interface GeoPoint {
  id: number;
  lat: number;
  lon: number;
  severity: string;
  category: string;
  status: string;
  ward?: string;
}

export interface HotspotCluster {
  ward: string;
  count: number;
  avg_severity: number;
  top_category: string;
  lat: number;
  lon: number;
}

export interface WardReport {
  ward: string;
  city?: string;
  total_issues: number;
  resolved: number;
  resolution_rate: number;
  critical_count: number;
  avg_resolution_days: number;
}

export interface GeocodingResult {
  display_name: string;
  road?: string;
  suburb?: string;
  city?: string;
  state?: string;
  postcode?: string;
  ward?: string;
  latitude: number;
  longitude: number;
}

export interface NearbyAmenity {
  name: string;
  type: string;
  distance_m: number;
  lat: number;
  lon: number;
}

export interface HighRiskZoneInfo {
  is_high_risk: boolean;
  amenities: NearbyAmenity[];
  risk_label: string;
}
