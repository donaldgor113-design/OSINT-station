import { useEffect, useState } from "react";
import { listEntities, listWorkspaces } from "../api";
import { useWorkspaceStore } from "../store/workspaceState";
import type { UniversalEntity, Workspace } from "../types";

interface WidgetConfig {
  id: string;
  type: string;
  title: string;
  size: "1x1" | "2x1" | "2x2" | "4x1";
  x: number;
  y: number;
}

const DEFAULT_WIDGETS: WidgetConfig[] = [
  { id: "w1", type: "system_status", title: "Статус системи", size: "2x1", x: 0, y: 0 },
  { id: "w2", type: "current_workspace", title: "Поточне дослідження", size: "2x1", x: 2, y: 0 },
  { id: "w3", type: "statistics", title: "Статистика", size: "2x2", x: 0, y: 1 },
  { id: "w4", type: "recent", title: "Останні знахідки", size: "2x2", x: 2, y: 1 },
  { id: "w5", type: "saved_searches", title: "Закріплені пошуки", size: "2x1", x: 0, y: 3 },
  { id: "w6", type: "mini_map", title: "Міні-карта", size: "2x1", x: 2, y: 3 },
  { id: "w7", type: "ai_queue", title: "Черга AI", size: "2x1", x: 0, y: 4 },
  { id: "w8", type: "ai_hints", title: "Підказки AI", size: "2x1", x: 2, y: 4 },
  { id: "w9", type: "quick_actions", title: "Швидкі дії", size: "2x1", x: 0, y: 5 },
];

export default function HomeView() {
  const currentId = useWorkspaceStore((s) => s.currentId);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [entities, setEntities] = useState<UniversalEntity[]>([]);
  const [loading, setLoading] = useState(false);
  const [widgets, setWidgets] = useState<WidgetConfig[]>(() => {
    try {
      const saved = localStorage.getItem("home_widgets");
      return saved ? JSON.parse(saved) : DEFAULT_WIDGETS;
    } catch { return DEFAULT_WIDGETS; }
  });
  const [editMode, setEditMode] = useState(false);

  useEffect(() => {
    localStorage.setItem("home_widgets", JSON.stringify(widgets));
  }, [widgets]);

  useEffect(() => {
    listWorkspaces().then(setWorkspaces).catch(() => {});
  }, []);

  useEffect(() => {
    if (currentId == null) {
      setEntities([]);
      return;
    }
    setLoading(true);
    listEntities(currentId)
      .then(setEntities)
      .finally(() => setLoading(false));
  }, [currentId]);

  const totalEntities = entities.length;
  const companies = entities.filter((e) => e.entity_type === "company" || e.properties?.company).length;
  const people = entities.filter((e) => e.entity_type === "person").length;
  const withGeo = entities.filter((e) => e.properties?.geo?.address).length;
  const withDocs = entities.filter((e) => e.entity_type === "document" || e.properties?.document).length;
  const currentWorkspace = workspaces.find((w) => w.id === currentId);

  const handleRemoveWidget = (id: string) => {
    setWidgets((prev) => prev.filter((w) => w.id !== id));
  };

  const handleResize = (id: string) => {
    setWidgets((prev) => prev.map((w) => {
      if (w.id !== id) return w;
      const sizes: WidgetConfig["size"][] = ["1x1", "2x1", "2x2", "4x1"];
      const idx = sizes.indexOf(w.size);
      return { ...w, size: sizes[(idx + 1) % sizes.length] };
    }));
  };

  const handleReset = () => {
    setWidgets(DEFAULT_WIDGETS);
  };

  const renderWidget = (widget: WidgetConfig) => {
    switch (widget.type) {
      case "system_status":
        return (
          <>
            <div className="entity-row muted">Backend: OK</div>
            <div className="entity-row muted">БД: OK</div>
            <div className="entity-row muted">AI: Ollama</div>
          </>
        );
      case "current_workspace":
        return (
          <>
            <div className="entity-row"><strong>{currentWorkspace?.name ?? "Не вибрано"}</strong></div>
            <div className="entity-row muted">Досліджень: {workspaces.length}</div>
            <div className="entity-row muted">Сутностей: {totalEntities}</div>
          </>
        );
      case "statistics":
        return (
          <>
            <div className="entity-row">Підприємства: {companies}</div>
            <div className="entity-row">Особи: {people}</div>
            <div className="entity-row">З адресами: {withGeo}</div>
            <div className="entity-row">Документи: {withDocs}</div>
          </>
        );
      case "recent":
        return (
          <>
            {entities.slice(0, 5).map((e) => (
              <div key={e.entity_id} className="entity-row muted">
                {e.entity_name} ({e.entity_type})
              </div>
            ))}
            {entities.length === 0 && <div className="muted">Немає знахідок</div>}
          </>
        );
      case "saved_searches":
        return <div className="muted">Збережені пошуки з'являться тут.</div>;
      case "mini_map":
        return <div className="muted">Міні-карта з пінами гео-сутностей.</div>;
      case "ai_queue":
        return <div className="muted">Черга AI-задач порожня.</div>;
      case "ai_hints":
        return <div className="muted">Підказки AI з'являться після аналізу.</div>;
      case "quick_actions":
        return (
          <>
            <button className="btn-secondary" style={{ marginRight: 4 }}>Новий пошук</button>
            <button className="btn-secondary" style={{ marginRight: 4 }}>Завантажити файл</button>
            <button className="btn-secondary">Створити звіт</button>
          </>
        );
      default:
        return <div className="muted">Невідомий віджет</div>;
    }
  };

  return (
    <div className="home-dashboard-container">
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 8 }}>
        <button className="btn-secondary" onClick={() => setEditMode(!editMode)}>
          {editMode ? "Готово" : "Редагувати"}
        </button>
        <button className="btn-secondary" style={{ marginLeft: 4 }} onClick={handleReset}>
          Скинути
        </button>
      </div>

      <div className="home-dashboard">
        {widgets.map((widget) => (
          <div
            key={widget.id}
            className={`home-widget widget-${widget.size} ${editMode ? "editing" : ""}`}
            style={{ gridColumn: `span ${widget.size.split("x")[0]}`, gridRow: `span ${widget.size.split("x")[1]}` }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h4>{widget.title}</h4>
              {editMode && (
                <div>
                  <button className="icon-btn" onClick={() => handleResize(widget.id)}>⤢</button>
                  <button className="icon-btn" onClick={() => handleRemoveWidget(widget.id)}>✕</button>
                </div>
              )}
            </div>
            {renderWidget(widget)}
          </div>
        ))}
      </div>

      {widgets.length === 0 && (
        <div className="empty-state">
          <h3>Галерея віджетів</h3>
          <p className="muted">Перетягніть віджети сюди, щоб додати їх на дашборд.</p>
          <button className="btn-secondary" onClick={handleReset}>Скинути до стандартного</button>
        </div>
      )}

      {loading && <div className="empty">Завантаження...</div>}
    </div>
  );
}
