export interface WordTiming {
  word: string;
  start: number;
  end: number;
}

export interface Segment {
  id: number;
  start: number;
  end: number;
  text: string;
  words: WordTiming[];
}

export interface Trim {
  start: number;
  end: number | null;
}

export interface HookState {
  text: string;
  start: number;
  end: number;
}

export interface MusicState {
  filename: string | null;
  volume: number;
  duck_level: number;
}

export interface CriticResult {
  score: number;
  summary: string;
  suggestions: string[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
}

export interface StylePreview {
  style: string;
  label: string;
  url: string;
}

export interface Project {
  id: string;
  created_at: string;
  source_video: string;
  duration: number | null;
  language: string;
  transcript: string;
  segments: Segment[];
  hook_options: string[];
  hook: HookState;
  caption_style: string;
  trim: Trim;
  speed: number;
  music: MusicState;
  critic: CriticResult | null;
  chat: ChatMessage[];
  style_previews: StylePreview[];
  status: string;
  render_url: string | null;
  variation_urls: string[];
}

export const CAPTION_STYLES = [
  "discreto",
  "editorial",
  "impacto",
  "karaoke",
  "uma_palavra",
  "manuscrito",
] as const;

export const STYLE_LABELS: Record<string, string> = {
  discreto: "Discreto",
  editorial: "Editorial",
  impacto: "Impacto",
  karaoke: "Karaoke",
  uma_palavra: "Uma palavra",
  manuscrito: "Manuscrito",
};
