import api from "./api";
import type { GeoPoint, HotspotCluster, WardReport } from "../types/location";

export const mapService = {
  async getPoints(params?: {
    city?: string; severity?: string; category?: string; limit?: number;
  }): Promise<GeoPoint[]> {
    const { data } = await api.get<GeoPoint[]>("/geographic/points", { params });
    return data;
  },

  async getHotspots(params?: { eps_km?: number; min_samples?: number }): Promise<HotspotCluster[]> {
    const { data } = await api.get<HotspotCluster[]>("/geographic/hotspots", { params });
    return data;
  },

  async getWards(city?: string): Promise<WardReport[]> {
    const { data } = await api.get<WardReport[]>("/geographic/wards", { params: { city } });
    return data;
  },

  async getNearby(lat: number, lon: number, radius_km: number): Promise<GeoPoint[]> {
    const { data } = await api.get<GeoPoint[]>("/geographic/nearby", {
      params: { lat, lon, radius_km },
    });
    return data;
  },

  async getSummary(city?: string): Promise<Record<string, unknown>> {
    const { data } = await api.get("/geographic/summary", { params: { city } });
    return data;
  },

  async reverseGeocode(lat: number, lon: number): Promise<Record<string, string>> {
    const { data } = await api.get("/geographic/geocode", { params: { lat, lon } });
    return data;
  },
};
