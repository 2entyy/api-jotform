import type { Project, Trim } from "../types";

function pct(value: number, total: number): string {
  if (total <= 0) return "0%";
  return `${Math.min(100, Math.max(0, (value / total) * 100))}%`;
}

export default function Timeline({
  project,
  onTrimChange,
}: {
  project: Project;
  onTrimChange: (trim: Trim) => void;
}) {
  const lastSegmentEnd = project.segments.reduce((max, s) => Math.max(max, s.end), 0);
  const duration = Math.max(lastSegmentEnd, project.trim.end ?? 0, project.hook.end, 1);

  return (
    <div className="timeline">
      <h3 style={{ fontSize: 12, color: "var(--text-dim)", margin: "0 0 10px" }}>Timeline</h3>

      <div className="timeline-track">
        <div className="timeline-track-label">Câmara</div>
        <div className="timeline-lane">
          <div className="timeline-block camara" style={{ left: 0, width: "100%" }} />
        </div>
      </div>

      <div className="timeline-track">
        <div className="timeline-track-label">Legendas</div>
        <div className="timeline-lane">
          {project.segments.map((seg) => (
            <div
              key={seg.id}
              className="timeline-block legenda"
              style={{ left: pct(seg.start, duration), width: pct(seg.end - seg.start, duration) }}
              title={seg.text}
            />
          ))}
        </div>
      </div>

      <div className="timeline-track">
        <div className="timeline-track-label">Gancho</div>
        <div className="timeline-lane">
          {project.hook.text && (
            <div
              className="timeline-block gancho"
              style={{
                left: pct(project.hook.start, duration),
                width: pct(Math.max(0.2, project.hook.end - project.hook.start), duration),
              }}
              title={project.hook.text}
            />
          )}
        </div>
      </div>

      <div className="timeline-track">
        <div className="timeline-track-label">Música</div>
        <div className="timeline-lane">
          {project.music.filename && (
            <div className="timeline-block musica" style={{ left: 0, width: "100%" }} />
          )}
        </div>
      </div>

      <div className="trim-controls">
        <div className="field">
          <label>Corte início (s)</label>
          <input
            type="number"
            min={0}
            step={0.1}
            value={project.trim.start}
            onChange={(e) => onTrimChange({ ...project.trim, start: Number(e.target.value) })}
          />
        </div>
        <div className="field">
          <label>Corte fim (s)</label>
          <input
            type="number"
            min={0}
            step={0.1}
            value={project.trim.end ?? ""}
            placeholder={duration.toFixed(1)}
            onChange={(e) =>
              onTrimChange({
                ...project.trim,
                end: e.target.value === "" ? null : Number(e.target.value),
              })
            }
          />
        </div>
      </div>
    </div>
  );
}
