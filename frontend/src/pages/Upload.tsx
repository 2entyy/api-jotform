import { useState } from "react";
import { createProject } from "../api";
import type { Project } from "../types";

const MODELS = ["tiny", "base", "small", "medium", "large"];

export default function Upload({ onCreated }: { onCreated: (project: Project) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [model, setModel] = useState("small");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const project = await createProject(file, model);
      onCreated(project);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao processar o vídeo");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="upload-page">
      <h2>Novo vídeo base</h2>
      <p style={{ color: "var(--text-dim)", fontSize: 13 }}>
        Sobe um vídeo. Vamos transcrever localmente (Whisper), sugerir um gancho para a
        abertura e dar uma primeira pontuação ao hook.
      </p>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>Vídeo</label>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>
        <div className="field">
          <label>Modelo Whisper</label>
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            {MODELS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
        {error && <p className="error-text">{error}</p>}
        <button className="primary-button" type="submit" disabled={!file || loading}>
          {loading ? "A transcrever (pode demorar)..." : "Criar projeto"}
        </button>
      </form>
    </div>
  );
}
