import { useEffect, useState } from "react";
import {
  fetchNearestImage,
  hasMapillary,
  mapillaryViewerUrl,
  type MapillaryImage,
} from "../maps/mapillary";
import { getProvider } from "../maps/providers";
import { useMapStore } from "../store/mapState";
import PanelHeader from "./PanelHeader";

interface Props {
  providerId: string;
  onProviderChange: (id: string) => void;
  onPromote?: () => void;
  onMeta?: (meta: MapillaryImage | null) => void;
}

export default function ImageViewPanel({
  providerId,
  onProviderChange,
  onPromote,
  onMeta,
}: Props) {
  const center = useMapStore((s) => s.center);
  const [image, setImage] = useState<MapillaryImage | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (providerId === "mapillary" && hasMapillary()) {
      setLoading(true);
      fetchNearestImage(center.lng, center.lat).then((img) => {
        if (cancelled) return;
        setImage(img);
        onMeta?.(img);
        setLoading(false);
      });
    } else {
      setImage(null);
      onMeta?.(null);
      setLoading(false);
    }
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [providerId, center.lng, center.lat]);

  const provider = getProvider(providerId);

  return (
    <div className="map-panel">
      <PanelHeader
        providerId={providerId}
        onProviderChange={onProviderChange}
        onPromote={onPromote}
      />
      <div className="image-container">
        {providerId === "mapillary" && image ? (
          <a href={mapillaryViewerUrl(image.id)} target="_blank" rel="noreferrer">
            <img src={image.url} alt="Mapillary 360°" />
            <span className="open-link">Відкрити 360° ↗</span>
          </a>
        ) : (
          <div className="image-placeholder">
            {loading
              ? "Шукаємо фото…"
              : providerId === "mapillary"
                ? hasMapillary()
                  ? "Немає фото поблизу"
                  : "Додайте VITE_MAPILLARY_TOKEN"
                : provider.detail}
          </div>
        )}
      </div>
    </div>
  );
}
