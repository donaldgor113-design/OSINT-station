import { useEffect, useState } from "react";
import { analyzeEntities, getAiProviders, listEntities } from "../api";
import { useWorkspaceStore } from "../store/workspaceState";
import type { AiProvider, AnalyzeResponse, UniversalEntity } from "../types";

export default function AnalyzePanel() {
  const currentId = useWorkspaceStore((s) => s.currentId);

  const [entities, setEntities] = useState<UniversalEntity[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [providers, setProviders] = useState<AiProvider[]>([]);
  const [provider, setProvider] = useState("mock");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAiProviders()
      .then(setProviders)
      .catch((e: unknown) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (currentId == null) {
      setEntities([]);
      setSelected(new Set());
      return;
    }
    listEntities(currentId)
      .then((list) => {
        setEntities(list);
        setSelected(new Set(list.map((e) => e.entity_id)));
      })
      .catch((e: unknown) => setError(String(e)));
  }, [currentId]);

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected((prev) =>
      prev.size === entities.length
        ? new Set()
        : new Set(entities.map((e) => e.entity_id))
    );
  }

  async function run() {
    if (currentId == null) return;
    setLoading(true);
    setError(null);
    try {
      const ids = Array.from(selected);
      setResult(await analyzeEntities(currentId, ids, provider));
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="analyze-panel">
      <div className="ai-provider-row">
        <label className="ws-label" htmlFor="ai-provider">
          AI-модель:
        </label>
        <select
          id="ai-provider"
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
        >
          {providers.map((p) => (
            <option key={p.name} value={p.name} disabled={!p.configured}>
              {p.label}
              {p.local ? " (локально)" : ""}
              {!p.configured ? " — не налаштовано" : ""}
            </option>
          ))}
        </select>
      </div>

      <div className="select-entities">
        <div className="select-header">
          <span>
            Сутності для аналізу ({selected.size}/{entities.length})
          </span>
          <button onClick={toggleAll}>Вибрати всі / зняти</button>
        </div>
        {entities.length === 0 ? (
          <div className="empty">У цьому дослідженні поки немає сутностей.</div>
        ) : (
          <ul className="entity-select-list">
            {entities.map((e) => (
              <li key={e.entity_id}>
                <label>
                  <input
                    type="checkbox"
                    checked={selected.has(e.entity_id)}
                    onChange={() => toggle(e.entity_id)}
                  />
                  <span className="etype">{e.entity_type}</span> {e.entity_name}
                </label>
              </li>
            ))}
          </ul>
        )}
      </div>

      <button className="primary" onClick={run} disabled={loading || currentId == null}>
        {loading ? "Аналізую…" : "Проаналізувати"}
      </button>

      {error && <div className="error">Помилка: {error}</div>}

      {result && (
        <div className="analyze-results">
          <section>
            <h3>Зведення</h3>
            <p>{result.summary}</p>
          </section>
          <section>
            <h3>Кросс-перевірка</h3>
            <p>{result.cross_check}</p>
          </section>
          {result.anomalies.length > 0 && (
            <section>
              <h3>Аномалії</h3>
              <ul>
                {result.anomalies.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
