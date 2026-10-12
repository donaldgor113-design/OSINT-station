import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { getStyle } from "../maps/providers";
import { useMapStore } from "../store/mapState";
import PanelHeader from "./PanelHeader";

interface Props {
  providerId: string;
  onProviderChange: (id: string) => void;
  onPromote?: () => void;
}

export default function MapPanel({ providerId, onProviderChange, onPromote }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const programmatic = useRef(false);
  const markerRef = useRef<maplibregl.Marker | null>(null);

  const center = useMapStore((s) => s.center);
  const zoom = useMapStore((s) => s.zoom);
  const focus = useMapStore((s) => s.focus);
  const setCenter = useMapStore((s) => s.setCenter);
  const setZoom = useMapStore((s) => s.setZoom);

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: getStyle(providerId),
      center: [center.lng, center.lat],
      zoom,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-left");

    map.on("move", () => {
      if (programmatic.current) return;
      const c = map.getCenter();
      setCenter({ lat: c.lat, lng: c.lng });
      setZoom(map.getZoom());
    });

    mapRef.current = map;
    return () => map.remove();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const c = map.getCenter();
    if (
      Math.abs(c.lng - center.lng) < 1e-9 &&
      Math.abs(c.lat - center.lat) < 1e-9 &&
      Math.abs(map.getZoom() - zoom) < 1e-9
    ) {
      return;
    }

    programmatic.current = true;
    map.jumpTo({ center: [center.lng, center.lat], zoom });
    map.once("moveend", () => {
      programmatic.current = false;
    });
  }, [center.lat, center.lng, zoom]);

  useEffect(() => {
    mapRef.current?.setStyle(getStyle(providerId));
  }, [providerId]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (markerRef.current) {
      markerRef.current.remove();
      markerRef.current = null;
    }
    if (focus) {
      markerRef.current = new maplibregl.Marker({ color: "#e5484d" })
        .setLngLat([focus.lng, focus.lat])
        .addTo(map);
    }
  }, [focus]);

  return (
    <div className="map-panel">
      <PanelHeader
        providerId={providerId}
        onProviderChange={onProviderChange}
        onPromote={onPromote}
      />
      <div ref={containerRef} className="map-container" />
    </div>
  );
}
