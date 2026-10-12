import { useRef, useState } from "react";
import { analyzeImage } from "../api";
import type { ImageAnalysis } from "../types";

interface Props {
  onLocate: (lat: number, lng: number) => void;
}

export default function ImagePanel({ onLocate }: Props) {
  const [result, setResult] = useState<ImageAnalysis | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

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

  return (
    <div className="image-panel">
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        onChange={(e) => handleFile(e.target.files?.[0])}
        hidden
      />
      <button className="primary" onClick={() => fileRef.current?.click()}>
        Завантажити зображення
      </button>

      {loading && <div className="muted">Аналізуємо…</div>}
      {error && <div className="error">Помилка: {error}</div>}

      {result && (
        <div className="image-result">
          {preview && <img className="image-preview" src={preview} alt="preview" />}

          <dl className="image-meta">
            <dt>GPS</dt>
            <dd>{result.gps ? `${result.gps.lat}, ${result.gps.lng}` : "—"}</dd>
            <dt>Адреса</dt>
            <dd>{result.address?.address || "—"}</dd>
            <dt>Пристрій</dt>
            <dd>{result.device || "—"}</dd>
            <dt>Дата зйомки</dt>
            <dd>{result.datetime || "—"}</dd>
            <dt>Роздільність</dt>
            <dd>
              {result.width}×{result.height}
            </dd>
            <dt>SHA-256</dt>
            <dd className="mono">{result.sha256}</dd>
          </dl>

          <p className="ai-desc">{result.ai_description}</p>

          <div className={`consistency consistency-${result.consistency.status}`}>
            <strong>
              {result.consistency.status === "ok"
                ? "✓ Перевірено"
                : result.consistency.status === "mismatch"
                  ? "⚠️ Розбіжність"
                  : "Не перевірено"}
            </strong>
            <span>{result.consistency.detail}</span>
          </div>

          {result.checks.length > 0 && (
            <div className="checks">
              <h4>Перевірки без AI:</h4>
              <ul>
                {result.checks.map((c, i) => (
                  <li key={i} className={`check-${c.level}`}>
                    {c.text}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.vision && (
            <div className={`consistency consistency-${result.vision.status}`}>
              <strong>Візуальна перевірка (AI):</strong>
              <span>{result.vision.detail}</span>
            </div>
          )}

          {result.gps && (
            <button
              className="primary"
              onClick={() => onLocate(result.gps!.lat, result.gps!.lng)}
            >
              Показати на карті
            </button>
          )}
        </div>
      )}
    </div>
  );
}
