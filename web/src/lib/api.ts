// Typed client for the VisionAI FastAPI backend (see api/ in the project root).

export interface Place {
  name: string;
  lat: number;
  lon: number;
}

export interface AppConfig {
  version: string;
  languages: Record<string, string>;
  default_location: Place | null;
  emergency_share_enabled: boolean;
  max_upload_mb: number;
  /** Offline IndicTrans2 translation is set up on the server. */
  translation_available: boolean;
  /** "local" = AI runs on this machine (Ollama), "cloud" = Gemini, "none" = not set up. */
  ai_provider: "local" | "cloud" | "none";
  local_stt: boolean;
  local_stt_languages: string[];
  local_tts: boolean;
}

export interface TextResult {
  text: string;
  lang: string;
}

export interface OcrResult {
  text: string;
  found: boolean;
  source: "tesseract" | "gemini" | "none";
}

export interface DetectedObject {
  name: string;
  confidence: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  position: "left" | "ahead" | "right";
  proximity: "very close" | "close" | "far";
  clock: number;
}

export interface DetectResult {
  width: number;
  height: number;
  count: number;
  summary: string;
  objects: DetectedObject[];
  annotated_image: string | null;
}

export interface RouteResult {
  destination: Place;
  distance_km: number;
  duration_min: number;
  geometry: [number, number][];
  steps: string[];
  /** Language the steps are in ("en" unless offline translation is set up). */
  steps_lang: string;
  /** The original English steps (used to pick turn arrows). */
  steps_en?: string[];
  spoken: string;
}

export interface LiveMessage {
  objects?: DetectedObject[];
  summary?: string;
  announce?: string | null;
  urgent?: boolean;
  /** Direction of the announced object (10..2), for playing speech from that side. */
  clock?: number | null;
  error?: string;
}

export type DirectionStyle = "sides" | "clock";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function send(path: string, init?: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(path, init);
  } catch {
    throw new ApiError("Can't reach the VisionAI server. Is it running?", 0);
  }
  if (!res.ok) {
    let message = "Something went wrong. Please try again.";
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail)) message = "Some of the information sent wasn't valid.";
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(message, res.status);
  }
  return res;
}

const json = async <T>(path: string, init?: RequestInit) => (await send(path, init)).json() as Promise<T>;

function imageForm(image: Blob, lang: string, extra: Record<string, string> = {}): FormData {
  const form = new FormData();
  form.append("file", image, "photo.jpg");
  form.append("lang", lang);
  for (const [k, v] of Object.entries(extra)) form.append(k, v);
  return form;
}

const post = (body: FormData): RequestInit => ({ method: "POST", body });

export const api = {
  config: () => json<AppConfig>("/api/config"),
  describe: (image: Blob, lang: string) => json<TextResult>("/api/describe", post(imageForm(image, lang))),
  assist: (image: Blob, lang: string) => json<TextResult>("/api/assist", post(imageForm(image, lang))),
  ask: (image: Blob, lang: string, question: string) =>
    json<TextResult>("/api/ask", post(imageForm(image, lang, { question }))),
  chat: (message: string, lang: string) =>
    json<TextResult>("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, lang }),
    }),
  currency: (image: Blob, lang: string) => json<TextResult>("/api/currency", post(imageForm(image, lang))),
  ocr: (image: Blob, lang: string) => json<OcrResult>("/api/ocr", post(imageForm(image, lang))),
  detect: (image: Blob, lang: string, style: DirectionStyle) =>
    json<DetectResult>("/api/detect?annotate=false", post(imageForm(image, lang, { style }))),
  tts: async (text: string, lang: string) =>
    (
      await send("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, lang }),
      })
    ).blob(),
  route: (destination: string, lat: number, lon: number, lang: string) =>
    json<RouteResult>(
      `/api/navigation/route?${new URLSearchParams({ destination, lat: String(lat), lon: String(lon), lang })}`,
    ),
  translate: (texts: string[], lang: string) =>
    json<{ translations: string[]; lang: string }>("/api/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texts, lang }),
    }),
  transcribe: (audio: Blob, lang: string) => {
    const form = new FormData();
    form.append("file", audio, "speech.webm");
    form.append("lang", lang);
    return json<{ text: string; lang: string }>("/api/transcribe", { method: "POST", body: form });
  },
  share: (lat: number, lon: number) =>
    json<{ url: string }>(`/api/navigation/share?${new URLSearchParams({ lat: String(lat), lon: String(lon) })}`),
};

export function liveSocketUrl(lang: string, style: DirectionStyle): string {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  return `${scheme}://${location.host}/ws/live?${new URLSearchParams({ lang, style })}`;
}
