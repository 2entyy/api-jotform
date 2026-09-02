import { useRef, useState } from "react";
import { renderProject, updateProject, uploadMusic } from "../api";
import AssistantPanel from "../components/AssistantPanel";
import Timeline from "../components/Timeline";
import TranscriptPanel from "../components/TranscriptPanel";
import VariationsPanel from "../components/VariationsPanel";
import VideoPreview from "../components/VideoPreview";
import type { Project, Trim } from "../types";

export default function Editor({
  initialProject,
  onBack,
}: {
  initialProject: Project;
  onBack: () => void;
}) {
  const [project, setProject] = useState(initialProject);
  const [rendering, setRendering] = useState(false);
  const [renderError, setRenderError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  function handleSeek(time: number) {
    if (videoRef.current) videoRef.current.currentTime = time;
  }

  async function handleTrimChange(trim: Trim) {
    const updated = await updateProject(project.id, { trim });
    setProject(updated);
  }

  async function handleStylePicked(style: string) {
    const updated = await updateProject(project.id, { caption_style: style });
    setProject(updated);
  }

  async function handleHookPicked(text: string) {
    const updated = await updateProject(project.id, { hook: { ...project.hook, text } });
    setProject(updated);
  }

  async function handleMusicUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const updated = await uploadMusic(project.id, file);
    setProject(updated);
  }

  async function handleRender() {
    setRendering(true);
    setRenderError(null);
    try {
      const updated = await renderProject(project.id);
      setProject(updated);
    } catch (err) {
      setRenderError(err instanceof Error ? err.message : "Falha a renderizar");
    } finally {
      setRendering(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="top-bar">
        <h1>Video Variator</h1>
        <button className="link-button" onClick={onBack}>
          ← Novo vídeo
        </button>
      </div>

      <div className="editor-layout">
        <TranscriptPanel segments={project.segments} onSeek={handleSeek} />

        <div className="center-column">
          <VideoPreview project={project} ref={videoRef} />
          <Timeline project={project} onTrimChange={handleTrimChange} />

          <div className="timeline" style={{ paddingTop: 0 }}>
            <div className="field">
              <label>Música de fundo</label>
              <input type="file" accept="audio/*" onChange={handleMusicUpload} />
              {project.music.filename && (
                <span style={{ color: "var(--text-dim)", fontSize: 12 }}>
                  {project.music.filename}
                </span>
              )}
            </div>
          </div>

          <div className="render-bar">
            <span className={`status-pill ${project.status === "ready" ? "ready" : ""}`}>
              {project.status === "ready" ? "publicável" : "rascunho"}
            </span>
            {renderError && <span className="error-text">{renderError}</span>}
            <button className="primary-button" onClick={handleRender} disabled={rendering}>
              {rendering ? "A renderizar..." : "Aprovar e renderizar"}
            </button>
          </div>

          <VariationsPanel project={project} onProjectUpdated={setProject} />
        </div>

        <AssistantPanel
          project={project}
          onProjectUpdated={setProject}
          onStylePicked={handleStylePicked}
          onHookPicked={handleHookPicked}
        />
      </div>
    </div>
  );
}
