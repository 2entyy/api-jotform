import type { HookState, MusicState, Project, StylePreview, Trim } from "./types";

export const API_BASE = "http://localhost:8000";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail ?? detail;
    } catch {
      // response body wasn't JSON — keep the status text
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export function mediaUrl(path: string | null | undefined): string {
  if (!path) return "";
  return `${API_BASE}${path}`;
}

export async function listProjects(): Promise<Project[]> {
  return handle(await fetch(`${API_BASE}/api/projects`));
}

export async function createProject(file: File, model = "small"): Promise<Project> {
  const form = new FormData();
  form.append("file", file);
  form.append("model", model);
  return handle(await fetch(`${API_BASE}/api/projects`, { method: "POST", body: form }));
}

export async function getProject(id: string): Promise<Project> {
  return handle(await fetch(`${API_BASE}/api/projects/${id}`));
}

export interface ProjectPatch {
  caption_style?: string;
  hook?: HookState;
  trim?: Trim;
  music?: MusicState;
}

export async function updateProject(id: string, patch: ProjectPatch): Promise<Project> {
  return handle(
    await fetch(`${API_BASE}/api/projects/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    }),
  );
}

export async function uploadMusic(id: string, file: File): Promise<Project> {
  const form = new FormData();
  form.append("file", file);
  return handle(await fetch(`${API_BASE}/api/projects/${id}/music`, { method: "POST", body: form }));
}

export async function generateStylePreviews(id: string): Promise<StylePreview[]> {
  return handle(await fetch(`${API_BASE}/api/projects/${id}/style-previews`, { method: "POST" }));
}

export async function recomputeCritic(id: string): Promise<Project> {
  return handle(await fetch(`${API_BASE}/api/projects/${id}/critic`, { method: "POST" }));
}

export async function sendCommand(id: string, text: string): Promise<Project> {
  return handle(
    await fetch(`${API_BASE}/api/projects/${id}/command`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }),
  );
}

export async function renderProject(id: string): Promise<Project> {
  return handle(await fetch(`${API_BASE}/api/projects/${id}/render`, { method: "POST" }));
}

export async function generateVariations(id: string, count: number, seed?: number): Promise<Project> {
  return handle(
    await fetch(`${API_BASE}/api/projects/${id}/variations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ count, seed }),
    }),
  );
}
