import { useState } from "react";
import { useWorkspaceStore } from "../store/workspaceState";

type SettingsTab = "ai" | "adapters" | "workspaces" | "team" | "security";

interface Adapter {
  id: string;
  name: string;
  accessType: "api" | "scraper" | "browser";
  status: "enabled" | "disabled" | "degraded" | "error";
  lastCall: string;
  mock: boolean;
}

const ADAPTERS: Adapter[] = [
  { id: "shodan", name: "Shodan", accessType: "api", status: "enabled", lastCall: "—", mock: true },
  { id: "whois", name: "WHOIS (RDAP)", accessType: "api", status: "enabled", lastCall: "—", mock: false },
  { id: "google_maps", name: "Google Maps", accessType: "api", status: "disabled", lastCall: "—", mock: true },
  { id: "company_profile", name: "Company Profile", accessType: "scraper", status: "enabled", lastCall: "—", mock: false },
  { id: "web_search", name: "Web Search", accessType: "scraper", status: "enabled", lastCall: "—", mock: false },
  { id: "telegram", name: "Telegram", accessType: "api", status: "disabled", lastCall: "—", mock: true },
  { id: "social_browser", name: "Social Browser", accessType: "browser", status: "enabled", lastCall: "—", mock: false },
  { id: "registry", name: "Registry (ЄДР)", accessType: "api", status: "enabled", lastCall: "—", mock: false },
];

export default function SettingsView() {
  const currentId = useWorkspaceStore((s) => s.currentId);
  const [activeTab, setActiveTab] = useState<SettingsTab>("ai");
  const [adapters, setAdapters] = useState(ADAPTERS);
  const [adapterKeys, setAdapterKeys] = useState<Record<string, string>>({});
  const [testingAdapter, setTestingAdapter] = useState<string | null>(null);

  const tabs: { id: SettingsTab; label: string }[] = [
    { id: "ai", label: "AI-моделі" },
    { id: "adapters", label: "Адаптери" },
    { id: "workspaces", label: "Дослідження" },
    { id: "team", label: "Команда" },
    { id: "security", label: "Безпека" },
  ];

  const handleToggleAdapter = (id: string) => {
    setAdapters((prev) =>
      prev.map((a) =>
        a.id === id ? { ...a, status: a.status === "enabled" ? "disabled" : "enabled" } : a
      )
    );
  };

  const handleToggleMock = (id: string) => {
    setAdapters((prev) =>
      prev.map((a) => (a.id === id ? { ...a, mock: !a.mock } : a))
    );
  };

  const handleTest = (id: string) => {
    setTestingAdapter(id);
    setTimeout(() => {
      setAdapters((prev) =>
        prev.map((a) => a.id === id ? { ...a, status: "enabled", lastCall: new Date().toLocaleTimeString() } : a)
      );
      setTestingAdapter(null);
    }, 1500);
  };

  return (
    <div className="settings-view">
      <div className="settings-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`settings-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "ai" && (
        <div>
          <h3>AI-моделі</h3>
          <div className="adapter-list">
            {["Mock", "Ollama", "Claude", "OpenAI"].map((name) => (
              <div key={name} className="adapter-item">
                <div className="adapter-info">
                  <div>{name}</div>
                </div>
                <span className="adapter-status enabled">Налаштовано</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "adapters" && (
        <div>
          <h3>Адаптери</h3>
          <div className="adapter-list">
            {adapters.map((adapter) => (
              <div key={adapter.id} className="adapter-item">
                <div className="adapter-info">
                  <div>
                    <div>{adapter.name}</div>
                    <div className="muted" style={{ fontSize: 12 }}>
                      {adapter.accessType} · Останній виклик: {adapter.lastCall}
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                  <label style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12 }}>
                    <input type="checkbox" checked={adapter.mock} onChange={() => handleToggleMock(adapter.id)} />
                    Mock
                  </label>
                  <button className="btn-secondary" onClick={() => handleTest(adapter.id)} disabled={testingAdapter === adapter.id}>
                    {testingAdapter === adapter.id ? "Тест..." : "Тестувати"}
                  </button>
                  <button className="btn-secondary" onClick={() => handleToggleAdapter(adapter.id)}>
                    {adapter.status === "enabled" ? "Вимкнути" : "Увімкнути"}
                  </button>
                  <span className={`adapter-status ${adapter.status}`}>
                    {adapter.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "workspaces" && (
        <div>
          <h3>Дослідження</h3>
          <p className="muted">Керування воркспейсами досліджень.</p>
        </div>
      )}

      {activeTab === "team" && (
        <div>
          <h3>Команда</h3>
          <p className="muted">Керування користувачами та ролями (OAuth2/Keycloak — фаза 7).</p>
        </div>
      )}

      {activeTab === "security" && (
        <div>
          <h3>Безпека</h3>
          <p className="muted">Шифрування ключів, аудит, rate limiting (фаза 7).</p>
        </div>
      )}
    </div>
  );
}
