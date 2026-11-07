import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reportService } from "../services/reportService";
import type { IssueFormData } from "../types/issue";

/**
 * useReports – returns a paginated IssueList (items[], total, page, per_page).
 * Access via: const { data: { items = [], total } = { items: [], total: 0 } } = useReports(params)
 */

export const useReports = (params?: {
  status?: string; severity?: string; category?: string; city?: string;
}) =>
  useQuery({
    queryKey: ["reports", params],
    queryFn: () => reportService.list(params),
    staleTime: 30_000,
  });
  // .data is IssueList = {items, total, page, per_page}

export const useReport = (id: number) =>
  useQuery({
    queryKey: ["report", id],
    queryFn: () => reportService.get(id),
    enabled: id > 0,
  });

export const useCreateReport = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: IssueFormData) => reportService.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      qc.invalidateQueries({ queryKey: ["geo-points"] });
      qc.invalidateQueries({ queryKey: ["hotspots"] });
    },
  });
};

export const useUpdateStatus = (id: number) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ status, note }: { status: string; note?: string }) =>
      reportService.changeStatus(id, status, note),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["report", id] });
      qc.invalidateQueries({ queryKey: ["reports"] });
    },
  });
};

export const useGeoPoints = (params?: { city?: string; severity?: string; category?: string }) =>
  useQuery({
    queryKey: ["geo-points", params],
    queryFn: async () => {
      const { mapService } = await import("../services/mapService");
      return mapService.getPoints(params);
    },
    staleTime: 60_000,
  });

export const useHotspots = (params?: { eps_km?: number; min_samples?: number }) =>
  useQuery({
    queryKey: ["hotspots", params],
    queryFn: async () => {
      const { mapService } = await import("../services/mapService");
      return mapService.getHotspots(params);
    },
    staleTime: 120_000,
  });
