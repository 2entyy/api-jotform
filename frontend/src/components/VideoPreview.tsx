import { forwardRef } from "react";
import { mediaUrl } from "../api";
import type { Project } from "../types";

const VideoPreview = forwardRef<HTMLVideoElement, { project: Project }>(({ project }, ref) => {
  const src = project.render_url
    ? mediaUrl(project.render_url)
    : mediaUrl(`/media/projects/${project.id}/uploads/${project.source_video}`);

  return (
    <div className="preview-area">
      {src ? (
        <video ref={ref} src={src} controls />
      ) : (
        <div className="empty-preview">Sem vídeo</div>
      )}
    </div>
  );
});

export default VideoPreview;
