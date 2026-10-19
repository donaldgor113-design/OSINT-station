import { useState, useCallback, useEffect } from "react";
import { analyzeEntities, listEntities } from "../api";
import { useWorkspaceStore } from "../store/workspaceState";
import type { UniversalEntity } from "../types";
import { DetailBlock } from "./EntityDetailCard";

type AnalyzeTab = "ai" | "graph" | "report" | "agents";

export default function AnalyzePanel() {
  const currentId = useWorkspaceStore((s) => s.currentId);
  const [activeTab, setActiveTab] = useState<AnalyzeTab>("ai");
  const [entities, setEntities] = useState<UniversalEntity[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [provider, setProvider] = useState("mock");
  const [result, setResult] = useState<{ summary: string; cross_check: string; anomalies: string[] } | null>(null);
  const [loading, setLoading] = useState(false);

  const [graphEntities, setGraphEntities] = useState<UniversalEntity[]>([]);
  const [graphTypeFilter, setGraphTypeFilter] = useState<string[]>([]);
  const [graphRelFilter, setGraphRelFilter] = useState<string[]>([]);
  const [graphMinConfidence, setGraphMinConfidence] = useState(0);

  const [reportBlocks, setReportBlocks] = useState<string[]>(["title", "summary", "entities", "sources"]);

  const [agents, setAgents] = useState<{ id: string; name: string; status: string }[]>([]);
  const [agentLog, setAgentLog] = useState<string[]>([]);

  useEffect(() => {
    if (currentId == null) {
      setEntities([]);
      setGraphEntities([]);
      return;
    }
    listEntities(currentId).then((ents) => {
      setEntities(ents);
      setGraphEntities(ents);
    });
  }, [currentId]);

  const handleAnalyze = useCallback(async () => {
    if (currentId == null || selectedIds.length === 0) return;
    setLoading(true);
    try {
      const res = await analyzeEntities(currentId, selectedIds, provider);
      setResult(res);
    } finally {
      setLoading(false);
    }
  }, [currentId, selectedIds, provider]);

  const toggleEntity = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const filteredGraphEntities = graphEntities.filter((e) => {
    if (graphTypeFilter.length > 0 && !graphTypeFilter.includes(e.entity_type)) return false;
    if (graphMinConfidence > 0 && (e.properties?.metadata?.sources?.[0]?.confidence || 0) < graphMinConfidence) return false;
    return true;
  });

  const graphNodes = filteredGraphEntities.slice(0, 20).map((e, i) => ({
    id: e.entity_id,
    name: e.entity_name,
    type: e.entity_type,
    x: 50 + (i % 5) * 150,
    y: 50 + Math.floor(i / 5) * 120,
  }));

  const allTypes = Array.from(new Set(graphEntities.map((e) => e.entity_type)));
  const allRelTypes = Array.from(new Set(graphEntities.flatMap((e) => e.relations?.map((r) => r.type) || [])));

  const handleRunAgent = (agentId: string) => {
    setAgents((prev) => [...prev, { id: agentId, name: agentId, status: "running" }]);
    setAgentLog((prev) => [...prev, `Запущено агент: ${agentId}`]);
    setTimeout(() => {
      setAgents((prev) => prev.map((a) => a.id === agentId ? { ...a, status: "done" } : a));
      setAgentLog((prev) => [...prev, `Агент ${agentId} завершено`]);
    }, 3000);
  };

  const tabs: { id: AnalyzeTab; label: string }[] = [
    { id: "ai", label: "AI-аналіз" },
    { id: "graph", label: "Граф зв'язків" },
    { id: "report", label: "Конструктор звіту" },
    { id: "agents", label: "AI-агенти" },
  ];

  const reportBlockLabels: Record<string, string> = {
    title: "Титульна сторінка",
    summary: "Резюме (AI)",
    entities: "Картки сутностей",
    sources: "Джерела",
    media: "Медіа-галерея",
    graph: "Граф зв'язків (PNG)",
    custom: "Власний текст",
  };

  return (
    <div className="analyze-panel">
      <div className="analyze-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`analyze-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "ai" && (
        <>
          <div className="ai-provider-row">
            <select value={provider} onChange={(e) => setProvider(e.target.value)} className="filter-select">
              <option value="mock">Mock</option>
              <option value="ollama">Ollama</option>
              <option value="claude">Claude</option>
              <option value="openai">OpenAI</option>
            </select>
          </div>
          <div className="select-entities">
            <div className="select-header">
              <span>Оберіть сутності для аналізу ({selectedIds.length} обрано)</span>
              <button className="btn-secondary" onClick={() => setSelectedIds(entities.map((e) => e.entity_id))}>Обрати всі</button>
            </div>
            <ul className="entity-select-list">
              {entities.map((e) => (
                <li key={e.entity_id}>
                  <label>
                    <input type="checkbox" checked={selectedIds.includes(e.entity_id)} onChange={() => toggleEntity(e.entity_id)} />
                    <span className="etype">{e.entity_type}</span>
                    {e.entity_name}
                  </label>
                </li>
              ))}
            </ul>
          </div>
          <button className="primary" onClick={handleAnalyze} disabled={loading || selectedIds.length === 0}>
            {loading ? "Аналізуємо..." : "Проаналізувати"}
          </button>
          {result && (
            <div className="analyze-results">
              <section><h3>Зведення</h3><p>{result.summary}</p></section>
              <section><h3>Кросс-перевірка</h3><p>{result.cross_check}</p></section>
              {result.anomalies.length > 0 && (
                <section><h3>Аномалії</h3><ul>{result.anomalies.map((a, i) => <li key={i}>{a}</li>)}</ul></section>
              )}
            </div>
          )}
        </>
      )}

      {activeTab === "graph" && (
        <>
          <div className="search-facets" style={{ marginBottom: 12 }}>
            <h4>Тип сутності</h4>
            <div className="facet-group">
              {allTypes.map((t) => (
                <label key={t} className="facet-item">
                  <input
                    type="checkbox"
                    checked={graphTypeFilter.includes(t)}
                    onChange={() => setGraphTypeFilter((prev) => prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t])}
                  />
                  <span>{t}</span>
                </label>
              ))}
            </div>
            <h4>Тип зв'язку</h4>
            <div className="facet-group">
              {allRelTypes.map((t) => (
                <label key={t} className="facet-item">
                  <input
                    type="checkbox"
                    checked={graphRelFilter.includes(t)}
                    onChange={() => setGraphRelFilter((prev) => prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t])}
                  />
                  <span>{t}</span>
                </label>
              ))}
            </div>
            <h4>Мінімальна довіра</h4>
            <input type="range" min={0} max={100} value={graphMinConfidence * 100} onChange={(e) => setGraphMinConfidence(Number(e.target.value) / 100)} />
          </div>
          <div className="graph-container">
            {graphNodes.map((node) => (
              <div
                key={node.id}
                className="graph-node"
                style={{ left: node.x, top: node.y }}
              >
                <div style={{ fontWeight: 500 }}>{node.name}</div>
                <div style={{ fontSize: 10, color: "var(--muted)" }}>{node.type}</div>
              </div>
            ))}
            {graphNodes.length === 0 && <div className="empty">Немає сутностей для графа.</div>}
          </div>
          <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
            <button className="btn-secondary">Експорт PNG</button>
            <button className="btn-secondary">Експорт SVG</button>
            <button className="btn-secondary">Експорт JSON</button>
          </div>
        </>
      )}

      {activeTab === "report" && (
        <div className="report-constructor">
          <div className="report-blocks">
            <h4>Блоки звіту</h4>
            {reportBlocks.map((block) => (
              <div key={block} className="report-block">
                <label>
                  <input
                    type="checkbox"
                    checked={true}
                    onChange={() => setReportBlocks((prev) => prev.includes(block) ? prev.filter((b) => b !== block) : [...prev, block])}
                  />
                  {reportBlockLabels[block] || block}
                </label>
              </div>
            ))}
            <button className="btn-secondary" onClick={() => setReportBlocks([...reportBlocks, "custom"])}>Додати блок</button>
          </div>
          <div className="report-preview">
            <h4>Прев'ю звіту</h4>
            {reportBlocks.includes("title") && <h2>{currentWorkspace?.name || "Звіт"}</h2>}
            {reportBlocks.includes("summary") && <p className="muted">Резюме генерується AI...</p>}
            {reportBlocks.includes("entities") && (
              <div>
                {entities.filter((e) => selectedIds.includes(e.entity_id)).map((e) => (
                  <div key={e.entity_id} className="entity-row muted">{e.entity_name}</div>
                ))}
              </div>
            )}
            {reportBlocks.includes("sources") && (
              <div>
                {entities.flatMap((e) => e.properties?.metadata?.sources || []).map((s, i) => (
                  <div key={i} className="entity-row muted">{s.name}</div>
                ))}
              </div>
            )}
            <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
              <button className="btn-secondary">Експорт PDF</button>
              <button className="btn-secondary">Експорт Markdown</button>
            </div>
          </div>
        </div>
      )}

      {activeTab === "agents" && (
        <>
          <h4>Бібліотека агентів</h4>
          <div className="adapter-list">
            {[
              { id: "person_profile", name: "Пошук профілю людини", desc: "ПІБ → соцмережі → person-сутність" },
              { id: "company_analysis", name: "Аналіз компанії", desc: "ЄДРПОУ → реєстри + веб → company-сутність" },
              { id: "reverse_image", name: "Reverse image", desc: "URL зображення → пошук публікацій" },
              { id: "telegram_monitor", name: "Моніторинг Telegram", desc: "Канал → останні пости → згадки" },
            ].map((agent) => (
              <div key={agent.id} className="adapter-item">
                <div className="adapter-info">
                  <div>
                    <div>{agent.name}</div>
                    <div className="muted" style={{ fontSize: 12 }}>{agent.desc}</div>
                  </div>
                </div>
                <button className="btn-secondary" onClick={() => handleRunAgent(agent.id)}>Запустити</button>
              </div>
            ))}
          </div>

          <h4 style={{ marginTop: 16 }}>Черга задач</h4>
          <div className="adapter-list">
            {agents.map((a) => (
              <div key={a.id} className="adapter-item">
                <div className="adapter-info">
                  <div>{a.name}</div>
                </div>
                <span className={`adapter-status ${a.status === "running" ? "degraded" : "enabled"}`}>
                  {a.status === "running" ? "Виконується..." : "Завершено"}
                </span>
              </div>
            ))}
            {agents.length === 0 && <div className="muted">Черга порожня</div>}
          </div>

          {agentLog.length > 0 && (
            <DetailBlock title="Лог">
              {agentLog.map((line, i) => (
                <div key={i} className="entity-row muted" style={{ fontFamily: "monospace", fontSize: 12 }}>{line}</div>
              ))}
            </DetailBlock>
          )}
        </>
      )}
    </div>
  );
}
