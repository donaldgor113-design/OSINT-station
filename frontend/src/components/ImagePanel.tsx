import { useRef, useState, useEffect, useCallback } from "react";
import { analyzeImage, listEntities } from "../api";
import { useWorkspaceStore } from "../store/workspaceState";
import type { UniversalEntity, ImageAnalysis } from "../types";
import { DetailBlock } from "./EntityDetailCard";

interface Props {
  onLocate: (lat: number, lng: number) => void;
}

export default function ImagePanel({ onLocate }: Props) {
  const currentId = useWorkspaceStore((s) => s.currentId);
  const [result, setResult] = useState<ImageAnalysis | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  const [mediaEntities, setMediaEntities] = useState<UniversalEntity[]>([]);
  const [selectedMedia, setSelectedMedia] = useState<UniversalEntity | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [gpsFilter, setGpsFilter] = useState<string>("all");
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [lightbox, setLightbox] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<"newest" | "oldest">("newest");

  useEffect(() => {
    if (currentId == null) {
      setMediaEntities([]);
      setSelectedMedia(null);
      return;
    }
    listEntities(currentId).then((entities) => {
      setMediaEntities(entities.filter((e) => e.entity_type === "media" || e.properties?.document?.url?.match(/\.(jpg|jpeg|png|gif|webp|mp4|pdf)$/i)));
    });
  }, [currentId]);

  const filteredMedia = mediaEntities.filter((m) => {
    const props = m.properties;
    if (typeFilter !== "all") {
      const mime = (props as Record<string, Record<string, string>>)?.media?.mime_type || "";
      if (typeFilter === "photo" && !mime.startsWith("image/")) return false;
      if (typeFilter === "video" && !mime.startsWith("video/")) return false;
      if (typeFilter === "pdf" && mime !== "application/pdf") return false;
    }
    if (gpsFilter === "has" && !(props as Record<string, Record<string, unknown>>)?.media?.exif?.gps) return false;
    if (gpsFilter === "none" && (props as Record<string, Record<string, unknown>>)?.media?.exif?.gps) return false;
    if (sourceFilter !== "all") {
      const sources = (props as Record<string, Record<string, Array<{ name: string }>>>)?.metadata?.sources || [];
      if (!sources.some((s) => s.name === sourceFilter)) return false;
    }
    return true;
  }).sort((a, b) => {
    const dateA = (a.properties as Record<string, Record<string, string>>)?.temporal?.created || "";
    const dateB = (b.properties as Record<string, Record<string, string>>)?.temporal?.created || "";
    return sortOrder === "newest" ? dateB.localeCompare(dateA) : dateA.localeCompare(dateB);
  });

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    setLoading(true);
    setError(null);
    try {
      setResult(await analyzeImage(file));
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  const handleSelect = useCallback((entity: UniversalEntity) => {
    setSelectedMedia(entity);
  }, []);

  const sources = Array.from(new Set(mediaEntities.flatMap((m) => ((m.properties as Record<string, Record<string, Array<{ name: string }>>>)?.metadata?.sources || []).map((s) => s.name))));

  const selectedProps = selectedMedia?.properties as Record<string, Record<string, unknown>> | undefined;

  return (
    <div className="image-panel-master">
      <div className="image-panel-left">
        <input ref={fileRef} type="file" accept="image/*" onChange={(e) => handleFile(e.target.files?.[0])} hidden />
        <button className="primary" onClick={() => fileRef.current?.click()}>Завантажити зображення</button>
        {loading && <div className="muted">Аналізуємо...</div>}
        {error && <div className="error">Помилка: {error}</div>}

        <div className="media-filters">
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="filter-select">
            <option value="all">Усі типи</option>
            <option value="photo">Фото</option>
            <option value="video">Відео</option>
            <option value="pdf">PDF</option>
          </select>
          <select value={gpsFilter} onChange={(e) => setGpsFilter(e.target.value)} className="filter-select">
            <option value="all">Усі (GPS)</option>
            <option value="has">З GPS</option>
            <option value="none">Без GPS</option>
          </select>
          <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)} className="filter-select">
            <option value="all">Усі джерела</option>
            {sources.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value as "newest" | "oldest")} className="filter-select">
            <option value="newest">Новіші</option>
            <option value="oldest">Старіші</option>
          </select>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="filter-input" />
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="filter-input" />
        </div>

        <div className="media-gallery">
          {filteredMedia.length === 0 && <div className="empty">Медіа не знайдено.</div>}
          {filteredMedia.map((m) => {
            const media = (m.properties as Record<string, Record<string, unknown>>)?.media;
            const thumb = (media as Record<string, string>)?.thumbnail_url || (m.properties as Record<string, Record<string, string>>)?.document?.url;
            const hasGps = !!(media as Record<string, Record<string, number[]>>)?.exif?.gps;
            const hasOcr = !!(media as Record<string, string>)?.extracted_text;
            const hasDupes = ((m.properties as Record<string, Array<unknown>>)?.dupes || []).length > 0;
            return (
              <div key={m.entity_id} className="media-card" onClick={() => handleSelect(m)}>
                {thumb && <img src={thumb} alt="" className="media-thumb" onClick={(e) => { e.stopPropagation(); setLightbox(thumb); }} />}
                <div className="media-card-badges">
                  {hasGps && <span className="badge badge-gps">GPS</span>}
                  {hasOcr && <span className="badge badge-ocr">OCR</span>}
                  {hasDupes && <span className="badge badge-dup">Дублі</span>}
                </div>
                <div className="media-card-caption">{m.entity_name}</div>
              </div>
            );
          })}
        </div>

        {result && (
          <div className="image-result">
            {preview && <img className="image-preview" src={preview} alt="preview" />}
            <dl className="image-meta">
              <dt>GPS</dt><dd>{result.gps ? `${result.gps.lat}, ${result.gps.lng}` : "—"}</dd>
              <dt>Адреса</dt><dd>{result.address?.address || "—"}</dd>
              <dt>Пристрій</dt><dd>{result.device || "—"}</dd>
              <dt>Дата зйомки</dt><dd>{result.datetime || "—"}</dd>
              <dt>Роздільність</dt><dd>{result.width}×{result.height}</dd>
              <dt>SHA-256</dt><dd className="mono">{result.sha256}</dd>
            </dl>
            <p className="ai-desc">{result.ai_description}</p>
            {result.checks.length > 0 && (
              <div className="checks">
                <h4>Перевірки без AI:</h4>
                <ul>{result.checks.map((c, i) => <li key={i} className={`check-${c.level}`}>{c.text}</li>)}</ul>
              </div>
            )}
            {result.gps && <button className="primary" onClick={() => onLocate(result.gps!.lat, result.gps!.lng)}>Показати на карті</button>}
          </div>
        )}
      </div>

      {selectedMedia && (
        <div className="image-detail-card">
          <div className="detail-header">
            <span className="entity-type">Медіа</span>
            <h2>{selectedMedia.entity_name}</h2>
          </div>

          <div className="image-detail-view">
            {(selectedProps?.media as Record<string, string>)?.url && (
              <img src={(selectedProps?.media as Record<string, string>)?.url} alt="" className="image-detail-img" />
            )}
          </div>

          <DetailBlock title="Файл">
            <div className="entity-row">MIME: {(selectedProps?.media as Record<string, string>)?.mime_type || "—"}</div>
            <div className="entity-row">Розмір: {(selectedProps?.media as Record<string, string>)?.resolution || "—"}</div>
            <div className="entity-row">SHA-256: {(selectedProps?.media as Record<string, string>)?.sha256 || "—"}</div>
          </DetailBlock>

          <DetailBlock title="EXIF">
            <div className="entity-row">Пристрій: {(selectedProps?.media as Record<string, Record<string, string>>)?.exif?.device || "—"}</div>
            <div className="entity-row">Дата зйомки: {(selectedProps?.media as Record<string, Record<string, string>>)?.exif?.datetime || "—"}</div>
          </DetailBlock>

          <DetailBlock title="Перевірки">
            <div className="muted">Перевірки з'являться після аналізу.</div>
          </DetailBlock>

          <DetailBlock title="Розпізнаний текст (OCR)">
            <div className="muted">{((selectedProps?.media as Record<string, string>)?.extracted_text) || "OCR не виконувався"}</div>
          </DetailBlock>

          <DetailBlock title="Зв'язані сутності">
            <div className="muted">Зв'язки з'являться після пошуку.</div>
          </DetailBlock>

          <div className="detail-actions">
            <button className="btn-secondary">Reverse image search</button>
            <button className="btn-secondary">Показати на карті</button>
          </div>
        </div>
      )}

      {lightbox && (
        <div className="lightbox" onClick={() => setLightbox(null)}>
          <button className="lightbox-close" onClick={() => setLightbox(null)}>✕</button>
          <img src={lightbox} alt="" onClick={(e) => e.stopPropagation()} />
        </div>
      )}
    </div>
  );
}
