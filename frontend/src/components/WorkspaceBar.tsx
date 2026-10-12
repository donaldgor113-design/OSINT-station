import { useEffect, useState } from "react";
import { createWorkspace, listWorkspaces } from "../api";
import { useWorkspaceStore } from "../store/workspaceState";

export default function WorkspaceBar() {
  const workspaces = useWorkspaceStore((s) => s.workspaces);
  const currentId = useWorkspaceStore((s) => s.currentId);
  const setWorkspaces = useWorkspaceStore((s) => s.setWorkspaces);
  const setCurrentId = useWorkspaceStore((s) => s.setCurrentId);

  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listWorkspaces()
      .then((ws) => {
        setWorkspaces(ws);
        if (ws.length > 0 && currentId == null) {
          setCurrentId(ws[0].id);
        }
      })
      .catch((e: unknown) => setError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function create() {
    const n = name.trim();
    if (!n) return;
    setError(null);
    try {
      const ws = await createWorkspace(n);
      const updated = await listWorkspaces();
      setWorkspaces(updated);
      setCurrentId(ws.id);
      setName("");
      setCreating(false);
    } catch (e: unknown) {
      setError(String(e));
    }
  }

  return (
    <div className="workspace-bar">
      <span className="ws-label">Дослідження:</span>
      <select
        value={currentId ?? ""}
        onChange={(e) =>
          setCurrentId(e.target.value ? Number(e.target.value) : null)
        }
        disabled={workspaces.length === 0}
      >
        {workspaces.length === 0 && <option value="">— немає —</option>}
        {workspaces.map((w) => (
          <option key={w.id} value={w.id}>
            {w.name}
          </option>
        ))}
      </select>

      {creating ? (
        <span className="ws-create">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && create()}
            placeholder="Назва дослідження…"
            autoFocus
          />
          <button onClick={create}>Створити</button>
          <button onClick={() => setCreating(false)}>Скасувати</button>
        </span>
      ) : (
        <button onClick={() => setCreating(true)}>+ Нове</button>
      )}

      {error && <span className="ws-error">{error}</span>}
    </div>
  );
}
