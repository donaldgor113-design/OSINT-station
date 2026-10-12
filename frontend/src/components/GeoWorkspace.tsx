import { useEffect, useState } from "react";
import { geocode, listEntities } from "../api";
import type { MapillaryImage } from "../maps/mapillary";
import { getProvider } from "../maps/providers";
import { useMapStore } from "../store/mapState";
import { useWorkspaceStore } from "../store/workspaceState";
import type { UniversalEntity } from "../types";
import ImageViewPanel from "./ImageViewPanel";
import MapPanel from "./MapPanel";
import MetadataPanel from "./MetadataPanel";
import TimelineSlider from "./TimelineSlider";

const DEFAULT_SLOTS = ["osm", "dark", "mapillary", "satellite"];

export default function GeoWorkspace() {
  const [slots, setSlots] = useState<string[]>(DEFAULT_SLOTS);
  const [address, setAddress] = useState("");
  const [jumping, setJumping] = useState(false);
  const [imageMeta, setImageMeta] = useState<MapillaryImage | null>(null);
  const [locations, setLocations] = useState<UniversalEntity[]>([]);

  const currentId = useWorkspaceStore((s) => s.currentId);
  const center = useMapStore((s) => s.center);
  const zoom = useMapStore((s) => s.zoom);
  const setCenter = useMapStore((s) => s.setCenter);
  const setZoom = useMapStore((s) => s.setZoom);
  const setFocus = useMapStore((s) => s.setFocus);

  useEffect(() => {
    if (currentId == null) {
      setLocations([]);
      return;
    }
    listEntities(currentId)
      .then((list) =>
        setLocations(list.filter((e) => !!e.properties?.geo?.address))
      )
      .catch(() => setLocations([]));
  }, [currentId]);

  const mainId = slots[0];
  const minis = slots.slice(1);

  function focusLocation(lat: number, lng: number) {
    setCenter({ lat, lng });
    setZoom(15);
    setFocus({ lat, lng });
  }

  function changeProvider(index: number, id: string) {
    setSlots((prev) => prev.map((p, i) => (i === index ? id : p)));
  }

  function promote(index: number) {
    setSlots((prev) => {
      const next = [...prev];
      [next[0], next[index]] = [next[index], next[0]];
      return next;
    });
  }

  async function go() {
    const q = address.trim();
    if (!q) return;
    setJumping(true);
    try {
      const results = await geocode(q);
      const first = results[0];
      if (first) {
        setCenter({ lat: first.lat, lng: first.lng });
        setZoom(15);
        setFocus({ lat: first.lat, lng: first.lng });
      }
    } catch {
      /* ignore geocoding errors */
    } finally {
      setJumping(false);
    }
  }

  function renderPanel(providerId: string, index: number, isMain: boolean) {
    const provider = getProvider(providerId);
    const shared = {
      providerId,
      onProviderChange: (id: string) => changeProvider(index, id),
      onPromote: isMain ? undefined : () => promote(index),
    };
    if (provider.kind === "map") {
      return <MapPanel {...shared} />;
    }
    return <ImageViewPanel {...shared} onMeta={isMain ? setImageMeta : undefined} />;
  }

  return (
    <div className="geo-workspace">
      <div className="control-bar">
        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Координати або адреса (напр. Київ)…"
          onKeyDown={(e) => e.key === "Enter" && go()}
        />
        <button onClick={go} disabled={jumping}>
          {jumping ? "…" : "Перейти"}
        </button>
        <span className="readout">
          lat {center.lat.toFixed(4)}, lng {center.lng.toFixed(4)} · zoom {zoom.toFixed(1)}
        </span>
      </div>

      <div className="geo-layout">
        <div className="geo-main">{renderPanel(mainId, 0, true)}</div>
        <div className="geo-side">
          {locations.length > 0 && (
            <div className="locations-block">
              <h4>Адреси в розслідуванні</h4>
              <ul>
                {locations.map((e) => {
                  const coords = e.properties?.geo?.coordinates;
                  const label = e.properties?.geo?.address || e.entity_name;
                  return (
                    <li key={e.entity_id}>
                      <button
                        onClick={() => coords && focusLocation(coords[1], coords[0])}
                      >
                        {label}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
          <MetadataPanel providerId={mainId} imageMeta={imageMeta} />
          <div className="geo-minis">
            {minis.map((pid, i) => (
              <div key={i} className="geo-mini">
                {renderPanel(pid, i + 1, false)}
              </div>
            ))}
          </div>
        </div>
      </div>

      <TimelineSlider />
    </div>
  );
}
