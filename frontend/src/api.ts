import type {
  AiProvider,
  AiProviderInput,
  AnalyzeResponse,
  GeocodeResult,
  ImageAnalysis,
  SearchResponse,
  UniversalEntity,
  Workspace,
} from "./types";

// --- Workspaces -----------------------------------------------------------

export async function listWorkspaces(): Promise<Workspace[]> {
  const res = await fetch("/api/workspaces");
  if (!res.ok) throw new Error(`Failed to load workspaces: ${res.status}`);
  return res.json();
}

export async function createWorkspace(name: string, description = ""): Promise<Workspace> {
  const res = await fetch("/api/workspaces", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error(`Failed to create workspace: ${res.status}`);
  return res.json();
}

// --- Search ---------------------------------------------------------------

export async function searchEntities(
  query: string,
  workspaceId: number
): Promise<SearchResponse> {
  const res = await fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, source: "auto", workspace_id: workspaceId }),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

// --- Entities -------------------------------------------------------------

export async function listEntities(workspaceId: number): Promise<UniversalEntity[]> {
  const res = await fetch(`/api/entities?workspace_id=${workspaceId}`);
  if (!res.ok) throw new Error(`Failed to load entities: ${res.status}`);
  return res.json();
}

// --- Analysis -------------------------------------------------------------

export async function analyzeEntities(
  workspaceId: number,
  entityIds: string[],
  provider: string
): Promise<AnalyzeResponse> {
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      workspace_id: workspaceId,
      entity_ids: entityIds,
      provider,
    }),
  });
  if (!res.ok) throw new Error(`Analyze failed: ${res.status}`);
  return res.json();
}

// --- AI providers ---------------------------------------------------------

export async function getAiProviders(): Promise<AiProvider[]> {
  const res = await fetch("/api/ai/providers");
  if (!res.ok) throw new Error(`Failed to load AI providers: ${res.status}`);
  const data = await res.json();
  return data.providers;
}

export async function createAiProvider(input: AiProviderInput): Promise<void> {
  const res = await fetch("/api/ai/providers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.detail || `Failed to create provider: ${res.status}`);
  }
}

export async function deleteAiProvider(id: number): Promise<void> {
  const res = await fetch(`/api/ai/providers/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to delete provider: ${res.status}`);
}

// --- Geocode (non-persisting, for the map tool) ---------------------------

export async function geocode(query: string): Promise<GeocodeResult[]> {
  const res = await fetch("/api/geocode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Geocode failed: ${res.status}`);
  const data = await res.json();
  return data.results;
}

// --- Image analysis -------------------------------------------------------

export async function analyzeImage(file: File): Promise<ImageAnalysis> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/images/analyze", {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`Image analysis failed: ${res.status}`);
  return res.json();
}
