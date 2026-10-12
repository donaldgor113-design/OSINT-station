import { create } from "zustand";

export interface LatLng {
  lat: number;
  lng: number;
}

interface MapState {
  center: LatLng;
  zoom: number;
  timestamp: string | null;
  focus: LatLng | null;
  setCenter: (center: LatLng) => void;
  setZoom: (zoom: number) => void;
  setTimestamp: (timestamp: string | null) => void;
  setFocus: (focus: LatLng | null) => void;
}

// Shared point of state for every map panel (spec §5.2).
export const useMapStore = create<MapState>((set) => ({
  center: { lat: 50.4501, lng: 30.5234 }, // Kyiv
  zoom: 11,
  timestamp: "2026-01-01",
  focus: null,
  setCenter: (center) => set({ center }),
  setZoom: (zoom) => set({ zoom }),
  setTimestamp: (timestamp) => set({ timestamp }),
  setFocus: (focus) => set({ focus }),
}));
