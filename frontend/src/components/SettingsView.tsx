import { useEffect, useState } from "react";
import { createAiProvider, deleteAiProvider, getAiProviders } from "../api";
import type { AiProvider } from "../types";

type Kind = "openai" | "ollama" | "claude";

export default function SettingsView() {
  const [providers, setProviders] = useState<AiProvider[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [name, setName] = useState("");
  const [kind, setKind] = useState<Kind>("openai");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");

  async function refresh() {
    try {
      setProviders(await getAiProviders());
    } catch (e: unknown) {
      setError(String(e));
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function add() {
    if (!name.trim()) return;
    setError(null);
    try {
      await createAiProvider({
        name: name.trim(),
        kind,
        base_url: baseUrl.trim(),
        api_key: apiKey.trim(),
        model: model.trim(),
      });
      setName("");
      setBaseUrl("");
      setApiKey("");
      setModel("");
      setShowForm(false);
      await refresh();
    } catch (e: unknown) {
      setError(String(e));
    }
  }

  async function remove(id: number) {
    setError(null);
    try {
      await deleteAiProvider(id);
      await refresh();
    } catch (e: unknown) {
      setError(String(e));
    }
  }

  return (
    <div className="settings-view">
      <h2>Налаштування</h2>

      <section className="settings-section">
        <h3>AI-моделі</h3>
        <p className="muted">
          Підключайте будь-які моделі — локальні (Ollama) або хмарні (OpenAI-сумісні API, Claude).
        </p>

        <ul className="provider-list">
          {providers.map((p) => (
            <li key={p.name} className="provider-item">
              <div>
                <strong>{p.label}</strong>
                <span className="muted">
                  {p.local ? " · локально" : ""}
                  {!p.configured ? " · не налаштовано" : ""}
                  {p.custom ? " · власна" : ""}
                </span>
              </div>
              {p.custom && p.id != null && (
                <button className="icon-btn" onClick={() => remove(p.id)} title="Видалити">
                  🗑
                </button>
              )}
            </li>
          ))}
        </ul>

        {!showForm ? (
          <button className="primary" onClick={() => setShowForm(true)}>
            + Додати модель
          </button>
        ) : (
          <div className="provider-form">
            <input
              placeholder="Назва (напр. openrouter)"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <select value={kind} onChange={(e) => setKind(e.target.value as Kind)}>
              <option value="openai">OpenAI-сумісний API (GPT, Groq, OpenRouter…)</option>
              <option value="ollama">Ollama (локально)</option>
              <option value="claude">Claude (Anthropic)</option>
            </select>
            <input
              placeholder="Base URL (порожньо = стандартний)"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
            />
            <input
              placeholder="API-ключ"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
            <input
              placeholder="Модель (напр. gpt-4o-mini)"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
            <div className="form-actions">
              <button className="primary" onClick={add}>
                Зберегти
              </button>
              <button onClick={() => setShowForm(false)}>Скасувати</button>
            </div>
          </div>
        )}

        {error && <div className="error">Помилка: {error}</div>}
      </section>
    </div>
  );
}
