import api from './api';

export interface SavedPlace {
  id: number;
  name: string;
  address?: string | null;
  latitude: number;
  longitude: number;
  category: string;
  google_place_id?: string | null;
  source: string;
}

export const placesService = {
  async list(): Promise<SavedPlace[]> {
    const { data } = await api.get<SavedPlace[]>('/places');
    return data;
  },
  async create(place: Omit<SavedPlace, 'id'>): Promise<SavedPlace> {
    const { data } = await api.post<SavedPlace>('/places', place);
    return data;
  },
  async remove(id: number): Promise<void> {
    await api.delete(`/places/${id}`);
  },
  async route(origin: { latitude: number; longitude: number }, destination: { latitude: number; longitude: number }, travelMode: string) {
    const { data } = await api.post('/maps/route', {
      origin,
      destination,
      travel_mode: travelMode,
    });
    return data as {
      distance_meters?: number;
      duration?: string;
      encoded_polyline?: string;
      note?: string;
      source?: string;
    };
  },
};
