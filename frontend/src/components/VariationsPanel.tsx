import { useState } from "react";
import { generateVariations, mediaUrl } from "../api";
import type { Project } from "../types";

export default function VariationsPanel({
  project,
  onProjectUpdated,
}: {
  project: Project;
  onProjectUpdated: (project: Project) => void;
}) {
  const [count, setCount] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!project.render_url) return null;

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const updated = await generateVariations(project.id, count);
      onProjectUpdated(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha a gerar variações");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="variations-section">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3 style={{ margin: 0 }}>Variações para testar em Reels</h3>
          <p style={{ color: "var(--text-dim)", fontSize: 12, margin: "4px 0 0" }}>
            Cada variação parte do vídeo aprovado e aplica pequenos ajustes aleatórios de
            velocidade, cor e enquadramento.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="number"
            min={1}
            max={20}
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            style={{
              width: 60,
              background: "var(--panel-alt)",
              border: "1px solid var(--border)",
              color: "var(--text)",
              borderRadius: 6,
              padding: "6px 8px",
            }}
          />
          <button className="primary-button" onClick={handleGenerate} disabled={loading}>
            {loading ? "A gerar..." : "Gerar variações"}
          </button>
        </div>
      </div>
      {error && <p className="error-text">{error}</p>}
      {project.variation_urls.length > 0 && (
        <div className="variations-grid">
          {project.variation_urls.map((url, i) => (
            <video key={url} src={mediaUrl(url)} controls>
              Variação {i + 1}
            </video>
          ))}
        </div>
      )}
    </div>
  );
}
