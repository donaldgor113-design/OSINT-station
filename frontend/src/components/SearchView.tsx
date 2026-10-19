import { useState, useCallback, useEffect } from "react";
import { searchEntities, listEntities } from "../api";
import { useWorkspaceStore } from "../store/workspaceState";
import type { SearchResponse, UniversalEntity } from "../types";
import EntityCard from "./EntityCard";
import SearchBar from "./SearchBar";

type SearchMode = "auto" | "company" | "person" | "domain" | "ip" | "media";
type ResultsView = "card" | "list";

interface SearchHistoryItem {
  query: string;
  mode: SearchMode;
  timestamp: string;
  resultCount: number;
}

interface SavedSearch {
  id: string;
  query: string;
  mode: SearchMode;
  createdAt: string;
  lastRunAt?: string;
  lastResultCount?: number;
}

export default function SearchView() {
  const currentId = useWorkspaceStore((s) => s.currentId);
  const [mode, setMode] = useState<SearchMode>("auto");
  const [results, setResults] = useState<UniversalEntity[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [viewMode, setViewMode] = useState<ResultsView>("list");
  const [history, setHistory] = useState<SearchHistoryItem[]>(() => {
    try {
      const saved = localStorage.getItem("search_history");
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>(() => {
    try {
      const saved = localStorage.getItem("saved_searches");
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });
  const [facets, setFacets] = useState<Record<string, string[]>>({});
  const [showHistory, setShowHistory] = useState(true);
  const [cascade, setCascade] = useState<SearchResponse | null>(null);

  useEffect(() => {
    localStorage.setItem("search_history", JSON.stringify(history.slice(0, 50)));
  }, [history]);

  useEffect(() => {
    localStorage.setItem("saved_searches", JSON.stringify(savedSearches));
  }, [savedSearches]);

  const handleSearch = useCallback(async (q: string) => {
    if (currentId == null || !q.trim()) return;
    setQuery(q.trim());
    setLoading(true);
    setError(null);
    try {
      const res = await searchEntities(q.trim(), currentId);
      setResults(res.results);
      setCascade(res);
      setHistory((prev) => [{
        query: q.trim(),
        mode,
        timestamp: new Date().toISOString(),
        resultCount: res.results.length,
      }, ...prev].slice(0, 50));
      if (res.results.length === 1 && res.results[0].entity_type === "company") {
        setViewMode("card");
      } else {
        setViewMode("list");
      }
      const newFacets: Record<string, Record<string, number>> = {
        type: {}, source: {}, risk: {}, geo: {}
      };
      for (const r of res.results) {
        newFacets.type[r.entity_type] = (newFacets.type[r.entity_type] || 0) + 1;
        const src = r.properties?.metadata?.sources?.[0]?.name || "unknown";
        newFacets.source[src] = (newFacets.source[src] || 0) + 1;
        const risk = r.properties?.metadata?.risk_level || "low";
        newFacets.risk[risk] = (newFacets.risk[risk] || 0) + 1;
        const hasGeo = r.properties?.geo?.coordinates?.[0] !== 0;
        newFacets.geo[hasGeo ? "yes" : "no"] = (newFacets.geo[hasGeo ? "yes" : "no"] || 0) + 1;
      }
      const facetObj: Record<string, string[]> = {};
      for (const [key, vals] of Object.entries(newFacets)) {
        facetObj[key] = Object.entries(vals).map(([v, c]) => `${v} (${c})`);
      }
      setFacets(facetObj);
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [currentId, mode]);

  const handleHistoryClick = (item: SearchHistoryItem) => {
    setMode(item.mode);
    handleSearch(item.query);
  };

  const handleSaveSearch = () => {
    if (!query) return;
    setSavedSearches((prev) => [{
      id: Date.now().toString(),
      query,
      mode,
      createdAt: new Date().toISOString(),
    }, ...prev]);
  };

  const handleRunSaved = (saved: SavedSearch) => {
    setMode(saved.mode);
    handleSearch(saved.query);
  };

  const toggleFacet = (key: string, value: string) => {
    setFacets((prev) => {
      const current = prev[key] || [];
      const clean = value.replace(/ \(\d+\)$/, "");
      const isActive = current.some((v) => v.startsWith(clean));
      const updated = isActive
        ? current.filter((v) => !v.startsWith(clean))
        : [...current, value];
      return { ...prev, [key]: updated };
    });
  };

  const filteredResults = results.filter((r) => {
    for (const [key, values] of Object.entries(facets)) {
      if (values.length === 0) continue;
      if (key === "type") {
        const clean = values.map((v) => v.replace(/ \(\d+\)$/, ""));
        if (!clean.includes(r.entity_type)) return false;
      }
      if (key === "source") {
        const clean = values.map((v) => v.replace(/ \(\d+\)$/, ""));
        const src = r.properties?.metadata?.sources?.[0]?.name || "unknown";
        if (!clean.includes(src)) return false;
      }
      if (key === "risk") {
        const clean = values.map((v) => v.replace(/ \(\d+\)$/, ""));
        const risk = r.properties?.metadata?.risk_level || "low";
        if (!clean.includes(risk)) return false;
      }
      if (key === "geo") {
        const clean = values.map((v) => v.replace(/ \(\d+\)$/, ""));
        const hasGeo = r.properties?.geo?.coordinates?.[0] !== 0 ? "yes" : "no";
        if (!clean.includes(hasGeo)) return false;
      }
    }
    return true;
  });

  const modeLabels: Record<SearchMode, string> = {
    auto: "Авто",
    company: "Компанія",
    person: "Особа",
    domain: "Домен",
    ip: "IP",
    media: "Медіа",
  };

  return (
    <div className="search-view">
      <div className="search-toolbar">
        <div className="search-mode-toggle">
          {(Object.keys(modeLabels) as SearchMode[]).map((m) => (
            <button
              key={m}
              className={`search-mode-btn ${mode === m ? "active" : ""}`}
              onClick={() => setMode(m)}
            >
              {modeLabels[m]}
            </button>
          ))}
        </div>
        <div className="search-mode-toggle">
          <button className={`search-mode-btn ${viewMode === "card" ? "active" : ""}`} onClick={() => setViewMode("card")}>Картка</button>
          <button className={`search-mode-btn ${viewMode === "list" ? "active" : ""}`} onClick={() => setViewMode("list")}>Список</button>
        </div>
      </div>

      <SearchBar onSearch={handleSearch} loading={loading} />

      {cascade && (
        <div className="cascade-panel">
          <div className="cascade-header">
            <span>Тип: <strong>{cascade.query_type}</strong></span>
            <span>Намір: <strong>{cascade.intent}</strong></span>
            <span>Впевненість: <strong>{(cascade.confidence ?? 0).toFixed(2)}</strong></span>
            <span>Зупинка: <strong>{cascade.stopped_at ?? "—"}</strong></span>
          </div>
          {cascade.tiers && cascade.tiers.length > 0 && (
            <div className="cascade-tiers">
              {cascade.tiers.map((t) => (
                <div
                  key={t.name}
                  className={`cascade-tier ${t.skipped ? "skipped" : ""} ${t.error ? "error" : ""}`}
                >
                  <span className="cascade-tier-name">{t.name}</span>
                  <span className="cascade-tier-count">{t.entities_count} сутн.</span>
                  <span className="cascade-tier-conf">{t.confidence.toFixed(2)}</span>
                  <span className="cascade-tier-time">{t.duration_ms} мс</span>
                  {t.skipped && t.skip_reason && (
                    <span className="cascade-tier-reason">{t.skip_reason}</span>
                  )}
                  {t.error && <span className="cascade-tier-reason error">{t.error}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="search-body">
        {showHistory && (
          <div className="search-history-panel">
            <div className="search-history-header">
              <span>Історія</span>
              <button className="icon-btn" onClick={() => setShowHistory(false)}>✕</button>
            </div>
            <div className="search-history-list">
              {history.map((h, i) => (
                <div key={i} className="search-history-item" onClick={() => handleHistoryClick(h)}>
                  <div className="search-history-query">{h.query}</div>
                  <div className="search-history-meta">
                    {modeLabels[h.mode]} · {h.resultCount} рез. · {new Date(h.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
              {history.length === 0 && <div className="muted" style={{ padding: 8 }}>Історія порожня</div>}
            </div>
            <div style={{ padding: 8, borderTop: "1px solid var(--border)" }}>
              <button className="btn-secondary" style={{ width: "100%", marginBottom: 4 }} onClick={() => setHistory([])}>Очистити</button>
              <button className="btn-secondary" style={{ width: "100%" }} onClick={handleSaveSearch}>Зберегти як шаблон</button>
            </div>
            {savedSearches.length > 0 && (
              <div style={{ padding: 8, borderTop: "1px solid var(--border)" }}>
                <div className="muted" style={{ fontSize: 11, marginBottom: 4 }}>Збережені:</div>
                {savedSearches.slice(0, 5).map((s) => (
                  <div key={s.id} className="search-history-item" onClick={() => handleRunSaved(s)}>
                    <div className="search-history-query">{s.query}</div>
                    <div className="search-history-meta">{new Date(s.createdAt).toLocaleDateString()}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="search-results-area">
          {facets && Object.keys(facets).some((k) => facets[k].length > 0) && (
            <div className="facet-chips">
              {Object.entries(facets).flatMap(([key, values]) =>
                values.map((v) => (
                  <span key={`${key}-${v}`} className="facet-chip" onClick={() => toggleFacet(key, v)}>
                    {v} ×
                  </span>
                ))
              )}
            </div>
          )}

          {viewMode === "list" && Object.values(facets).some((v) => v.length > 0) && (
            <div className="search-facets">
              <h4>Тип</h4>
              <div className="facet-group">
                {(facets.type || []).map((v) => (
                  <label key={v} className="facet-item">
                    <input type="checkbox" checked readOnly onClick={() => toggleFacet("type", v)} />
                    <span>{v}</span>
                  </label>
                ))}
              </div>
              <h4>Джерело</h4>
              <div className="facet-group">
                {(facets.source || []).map((v) => (
                  <label key={v} className="facet-item">
                    <input type="checkbox" checked readOnly onClick={() => toggleFacet("source", v)} />
                    <span>{v}</span>
                  </label>
                ))}
              </div>
              <h4>Довіра</h4>
              <div className="facet-group">
                {(facets.risk || []).map((v) => (
                  <label key={v} className="facet-item">
                    <input type="checkbox" checked readOnly onClick={() => toggleFacet("risk", v)} />
                    <span>{v}</span>
                  </label>
                ))}
              </div>
              <h4>Гео</h4>
              <div className="facet-group">
                {(facets.geo || []).map((v) => (
                  <label key={v} className="facet-item">
                    <input type="checkbox" checked readOnly onClick={() => toggleFacet("geo", v)} />
                    <span>{v}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className={`search-results ${viewMode === "list" ? "with-facets" : ""}`}>
            {error && <div className="error">Помилка: {error}</div>}
            {!loading && filteredResults.length === 0 && query && (
              <div className="empty">Нічого не знайдено.</div>
            )}
            {!loading && filteredResults.length > 0 && viewMode === "card" && filteredResults[0].entity_type === "company" ? (
              <div className="company-full">
                <EntityCard entity={filteredResults[0]} />
              </div>
            ) : (
              <div className="entity-grid">
                {filteredResults.map((e) => (
                  <EntityCard key={e.entity_id} entity={e} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {!showHistory && (
        <button className="btn-secondary" style={{ marginBottom: 8 }} onClick={() => setShowHistory(true)}>
          Показати історію
        </button>
      )}
    </div>
  );
}
