import { useState } from "react";
import { recomputeCritic, sendCommand } from "../api";
import { CAPTION_STYLES, STYLE_LABELS } from "../types";
import type { Project } from "../types";
import StyleGrid from "./StyleGrid";

export default function AssistantPanel({
  project,
  onProjectUpdated,
  onStylePicked,
  onHookPicked,
}: {
  project: Project;
  onProjectUpdated: (project: Project) => void;
  onStylePicked: (style: string) => void;
  onHookPicked: (hookText: string) => void;
}) {
  const [command, setCommand] = useState("");
  const [sending, setSending] = useState(false);
  const [criticLoading, setCriticLoading] = useState(false);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!command.trim()) return;
    setSending(true);
    try {
      const updated = await sendCommand(project.id, command.trim());
      onProjectUpdated(updated);
      setCommand("");
    } finally {
      setSending(false);
    }
  }

  async function handleRecomputeCritic() {
    setCriticLoading(true);
    try {
      const updated = await recomputeCritic(project.id);
      onProjectUpdated(updated);
    } finally {
      setCriticLoading(false);
    }
  }

  return (
    <div className="panel">
      <h3>Assistente</h3>

      <div className="style-tabs">
        {CAPTION_STYLES.map((style) => (
          <button
            key={style}
            className={`style-tab ${project.caption_style === style ? "active" : ""}`}
            onClick={() => onStylePicked(style)}
          >
            {STYLE_LABELS[style]}
          </button>
        ))}
      </div>

      <StyleGrid
        project={project}
        onStylePicked={onStylePicked}
        onPreviewsGenerated={(previews) => onProjectUpdated({ ...project, style_previews: previews })}
      />

      <h3 style={{ marginTop: 18 }}>Gancho (abertura)</h3>
      <div className="hook-options">
        {project.hook_options.map((option) => (
          <button
            key={option}
            className={`hook-option ${project.hook.text === option ? "active" : ""}`}
            onClick={() => onHookPicked(option)}
          >
            {option}
          </button>
        ))}
      </div>

      <h3>Crítico</h3>
      <div className="critic-box">
        {project.critic ? (
          <>
            <div className="critic-score">Força {project.critic.score}/10</div>
            <div>{project.critic.summary}</div>
            <ul>
              {project.critic.suggestions.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </>
        ) : (
          <p style={{ color: "var(--text-dim)" }}>Sem avaliação ainda.</p>
        )}
        <button className="small-button" onClick={handleRecomputeCritic} disabled={criticLoading} style={{ marginTop: 8 }}>
          {criticLoading ? "A avaliar..." : "Reavaliar gancho"}
        </button>
      </div>

      <h3>Pedir à IA</h3>
      <div className="chat-log">
        {project.chat.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            {msg.text}
          </div>
        ))}
      </div>
      <form className="command-input-row" onSubmit={handleSend}>
        <input
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder="ex: tira a música, gancho mais forte, estilo karaoke"
        />
        <button className="small-button" type="submit" disabled={sending}>
          {sending ? "..." : "Enviar"}
        </button>
      </form>
    </div>
  );
}
