import { useState } from "react";
import { generateStylePreviews, mediaUrl } from "../api";
import type { Project, StylePreview } from "../types";

export default function StyleGrid({
  project,
  onStylePicked,
  onPreviewsGenerated,
}: {
  project: Project;
  onStylePicked: (style: string) => void;
  onPreviewsGenerated: (previews: StylePreview[]) => void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const previews = await generateStylePreviews(project.id);
      onPreviewsGenerated(previews);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha a gerar pré-visualizações");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 12, color: "var(--text-dim)" }}>Lote de legendas</span>
        <button className="small-button" onClick={handleGenerate} disabled={loading}>
          {loading ? "A gerar..." : "Ver como fica"}
        </button>
      </div>
      {error && <p className="error-text">{error}</p>}
      {project.style_previews.length > 0 && (
        <div className="style-grid">
          {project.style_previews.map((preview) => (
            <div key={preview.style} className="style-grid-item">
              <video src={mediaUrl(preview.url)} muted loop controls={false}
                     onMouseEnter={(e) => e.currentTarget.play()}
                     onMouseLeave={(e) => e.currentTarget.pause()} />
              <div className="label">
                <span>{preview.label}</span>
                <button
                  className={`small-button ${project.caption_style === preview.style ? "active" : ""}`}
                  onClick={() => onStylePicked(preview.style)}
                >
                  {project.caption_style === preview.style ? "Em uso" : "Usar"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
