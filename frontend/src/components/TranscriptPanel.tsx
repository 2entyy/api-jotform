import type { Segment } from "../types";

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function TranscriptPanel({
  segments,
  onSeek,
}: {
  segments: Segment[];
  onSeek: (time: number) => void;
}) {
  return (
    <div className="panel">
      <h3>Transcrição</h3>
      {segments.length === 0 && <p style={{ color: "var(--text-dim)" }}>Sem transcrição.</p>}
      {segments.map((seg) => (
        <div key={seg.id} className="segment-row" onClick={() => onSeek(seg.start)}>
          <div className="segment-time">
            {formatTime(seg.start)} – {formatTime(seg.end)}
          </div>
          <div>{seg.text}</div>
        </div>
      ))}
    </div>
  );
}
