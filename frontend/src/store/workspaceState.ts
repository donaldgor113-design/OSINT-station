import { create } from "zustand";
import type { Workspace } from "../types";

interface WorkspaceState {
  workspaces: Workspace[];
  currentId: number | null;
  setWorkspaces: (workspaces: Workspace[]) => void;
  setCurrentId: (id: number | null) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  workspaces: [],
  currentId: null,
  setWorkspaces: (workspaces) => set({ workspaces }),
  setCurrentId: (currentId) => set({ currentId }),
}));
