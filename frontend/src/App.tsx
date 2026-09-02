import { useState } from "react";
import Editor from "./pages/Editor";
import Upload from "./pages/Upload";
import type { Project } from "./types";

export default function App() {
  const [project, setProject] = useState<Project | null>(null);

  if (!project) {
    return (
      <div className="app-shell">
        <div className="top-bar">
          <h1>Video Variator</h1>
        </div>
        <Upload onCreated={setProject} />
      </div>
    );
  }

  return <Editor initialProject={project} onBack={() => setProject(null)} />;
}
