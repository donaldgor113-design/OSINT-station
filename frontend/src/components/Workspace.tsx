import { useCallback, useEffect, useState } from "react";
import { listEntities, searchEntities } from "../api";
import { useMapStore } from "../store/mapState";
import { useWorkspaceStore } from "../store/workspaceState";
import type { UniversalEntity } from "../types";
import AnalyzePanel from "./AnalyzePanel";
import EntityCard from "./EntityCard";
import GeoWorkspace from "./GeoWorkspace";
import ImagePanel from "./ImagePanel";
import ProfileView from "./ProfileView";
import SearchBar from "./SearchBar";
import SettingsView from "./SettingsView";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

const TITLES: Record<string, string> = {
  search: "Пошук",
  geo: "Гео-мапи",
  images: "Зображення",
  entities: "Сутності",
  analyze: "Аналіз",
  settings: "Налаштування",
  profile: "Профіль",
};

export default function Workspace() {
  const currentId = useWorkspaceStore((s) => s.currentId);
  const setCenter = useMapStore((s) => s.setCenter);

  const [active, setActive] = useState("search");
  const [results, setResults] = useState<UniversalEntity[]>([]);
  const [entities, setEntities] = useState<UniversalEntity[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  const refreshEntities = useCallback(async () => {
    if (currentId == null) {
      setEntities([]);
      return;
    }
    try {
      setEntities(await listEntities(currentId));
    } catch (e: unknown) {
      setError(String(e));
    }
  }, [currentId]);

  useEffect(() => {
    refreshEntities();
  }, [refreshEntities]);

  async function handleSearch(q: string) {
    if (currentId == null) return;
    setQuery(q);
    setLoading(true);
    setError(null);
    try {
      const res = await searchEntities(q, currentId);
      setResults(res.results);
      await refreshEntities();
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  function handleLocate(lat: number, lng: number) {
    setCenter({ lat, lng });
    setActive("geo");
  }

  function noWorkspace() {
    return (
      <div className="empty-state">
        <h3>Створіть дослідження</h3>
        <p className="muted">
          Щоб почати роботу, створіть нове дослідження через кнопку «+» у верхній панелі.
        </p>
      </div>
    );
  }

  return (
    <div className="app">
      <Sidebar active={active} onChange={setActive} />

      <div className="app-main">
        <TopBar title={TITLES[active] ?? ""} onOpenProfile={() => setActive("profile")} />

        <main className="app-content">
          {error && <div className="error">Помилка: {error}</div>}

          {active === "search" && (
            <>
              {currentId == null ? (
                noWorkspace()
              ) : (
                <>
                  <SearchBar onSearch={handleSearch} loading={loading} />
                  {query && !loading && (
                    <div className="result-count">Результатів: {results.length}</div>
                  )}
                  {results.length === 1 && results[0].entity_type === "company" ? (
                    <div className="company-full">
                      <EntityCard entity={results[0]} />
                    </div>
                  ) : (
                    <div className="entity-grid">
                      {results.map((e) => (
                        <EntityCard key={e.entity_id} entity={e} />
                      ))}
                    </div>
                  )}
                  {!loading && results.length === 0 && (
                    <div className="empty">Нічого не знайдено. Спробуйте інший запит.</div>
                  )}
                </>
              )}
            </>
          )}

          {active === "geo" && <GeoWorkspace />}
          {active === "images" && <ImagePanel onLocate={handleLocate} />}

          {active === "entities" && (
            <>
              {currentId == null ? (
                noWorkspace()
              ) : (
                <>
                  <div className="result-count">Всього збережено: {entities.length}</div>
                  <div className="entity-grid">
                    {entities.map((e) => (
                      <EntityCard key={e.entity_id} entity={e} />
                    ))}
                  </div>
                  {entities.length === 0 && <div className="empty">Сутностей поки немає.</div>}
                </>
              )}
            </>
          )}

          {active === "analyze" &&
            (currentId == null ? noWorkspace() : <AnalyzePanel />)}

          {active === "settings" && <SettingsView />}
          {active === "profile" && <ProfileView />}
        </main>
      </div>
    </div>
  );
}
