import type { MapillaryImage } from "../maps/mapillary";
import { getProvider } from "../maps/providers";
import { useMapStore } from "../store/mapState";

interface Props {
  providerId: string;
  imageMeta?: MapillaryImage | null;
}

export default function MetadataPanel({ providerId, imageMeta }: Props) {
  const center = useMapStore((s) => s.center);
  const zoom = useMapStore((s) => s.zoom);
  const timestamp = useMapStore((s) => s.timestamp);
  const provider = getProvider(providerId);

  if (provider.kind === "image") {
    const gps = imageMeta ? [imageMeta.lng, imageMeta.lat] : [center.lng, center.lat];
    return (
      <div className="metadata-panel">
        <h3>Метадані зображення</h3>
        <dl>
          <dt>Джерело</dt>
          <dd>{provider.label}</dd>
          <dt>GPS</dt>
          <dd>
            {gps[1].toFixed(5)}, {gps[0].toFixed(5)}
          </dd>
          <dt>Дата зйомки</dt>
          <dd>{imageMeta?.captured_at || timestamp || "—"}</dd>
          <dt>Роздільна здатність</dt>
          <dd>{imageMeta ? `${imageMeta.width}×${imageMeta.height}` : "—"}</dd>
          <dt>Пристрій</dt>
          <dd>—</dd>
          <dt>phash</dt>
          <dd>—</dd>
        </dl>
      </div>
    );
  }

  return (
    <div className="metadata-panel">
      <h3>Метадані карти</h3>
      <dl>
        <dt>Провайдер</dt>
        <dd>{provider.label}</dd>
        <dt>Центр</dt>
        <dd>
          {center.lat.toFixed(5)}, {center.lng.toFixed(5)}
        </dd>
        <dt>Зум</dt>
        <dd>{zoom.toFixed(1)}</dd>
        <dt>Таймлайн</dt>
        <dd>{timestamp ?? "—"}</dd>
      </dl>
    </div>
  );
}
