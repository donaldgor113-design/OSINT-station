import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const STYLE = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
} as maplibregl.StyleSpecification;

export default function MiniMap({ lng, lat }: { lng: number; lat: number }) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const map = new maplibregl.Map({
      container: ref.current,
      style: STYLE,
      center: [lng, lat],
      zoom: 14,
      interactive: false,
    });
    new maplibregl.Marker().setLngLat([lng, lat]).addTo(map);
    return () => map.remove();
  }, [lng, lat]);

  return <div ref={ref} className="mini-map" />;
}
