// Voice input via the browser's speech recognition (Chrome, Edge, Safari, Android).
// Recognition runs in the browser/OS; VisionAI only receives the final text.

interface RecognitionResultEvent {
  results: { 0: { transcript: string }; isFinal: boolean }[] & { length: number };
}

interface Recognition {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((e: RecognitionResultEvent) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

type RecognitionCtor = new () => Recognition;

function ctor(): RecognitionCtor | undefined {
  const w = window as unknown as { SpeechRecognition?: RecognitionCtor; webkitSpeechRecognition?: RecognitionCtor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition;
}

export const canListen = (): boolean => !!ctor();

export class ListenError extends Error {}

let active: Recognition | null = null;
let finishRecording: (() => void) | null = null;

/** Stop listening. A local recording is finished and still transcribed; browser recognition is cancelled. */
export function stopListening() {
  active?.abort();
  active = null;
  finishRecording?.();
}

export const canRecord = (): boolean => typeof MediaRecorder !== "undefined" && !!navigator.mediaDevices?.getUserMedia;

/**
 * Private voice input: record on this device, transcribe with Whisper on the VisionAI server.
 * Stops by itself ~1.2 s after you finish speaking (or when stopListening() is called).
 */
export async function recordAndTranscribe(lang: string): Promise<string> {
  let stream: MediaStream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
  } catch (err) {
    const name = err instanceof DOMException ? err.name : "";
    throw new ListenError(
      name === "NotAllowedError"
        ? "Microphone access was blocked. Allow the microphone for this site in your browser settings."
        : "No microphone was found.",
    );
  }

  const mime = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"].find((m) => MediaRecorder.isTypeSupported(m));
  const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
  const chunks: Blob[] = [];
  recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);

  // Simple voice-activity detection: volume above a threshold = speech.
  const ctx = new AudioContext();
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 1024;
  ctx.createMediaStreamSource(stream).connect(analyser);
  const samples = new Float32Array(analyser.fftSize);
  let heardSpeech = false;
  let lastSound = performance.now();
  const started = performance.now();

  const stopped = new Promise<void>((resolve) => (recorder.onstop = () => resolve()));
  const finish = () => recorder.state === "recording" && recorder.stop();
  finishRecording = finish;

  const timer = window.setInterval(() => {
    analyser.getFloatTimeDomainData(samples);
    const rms = Math.sqrt(samples.reduce((sum, v) => sum + v * v, 0) / samples.length);
    const now = performance.now();
    if (rms > 0.025) {
      heardSpeech = true;
      lastSound = now;
    }
    if ((heardSpeech && now - lastSound > 1200) || now - started > 15000 || (!heardSpeech && now - started > 6000)) finish();
  }, 100);

  recorder.start(250);
  await stopped;
  window.clearInterval(timer);
  stream.getTracks().forEach((t) => t.stop());
  void ctx.close();
  finishRecording = null;

  if (!heardSpeech) throw new ListenError("I didn't hear anything. Tap the microphone and speak.");
  const { api } = await import("./api");
  const { text } = await api.transcribe(new Blob(chunks, { type: recorder.mimeType }), lang);
  if (!text.trim()) throw new ListenError("I didn't catch that. Please try again.");
  return text.trim();
}

/** Listen for one spoken question. Resolves with the transcript. */
export function listenOnce(lang: string): Promise<string> {
  const Ctor = ctor();
  if (!Ctor) return Promise.reject(new ListenError("Voice input isn't supported in this browser. Try Chrome or Edge."));
  stopListening();

  return new Promise((resolve, reject) => {
    const rec = new Ctor();
    active = rec;
    rec.lang = lang === "en" ? "en-IN" : `${lang}-IN`;
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    let transcript = "";

    rec.onresult = (e) => {
      transcript = Array.from({ length: e.results.length }, (_, i) => e.results[i][0].transcript).join(" ").trim();
    };
    rec.onerror = (e) => {
      const messages: Record<string, string> = {
        "not-allowed": "Microphone access was blocked. Allow the microphone for this site in your browser settings.",
        "no-speech": "I didn't hear anything. Try again and speak after the beep.",
        "audio-capture": "No microphone was found.",
        network: "Voice input needs an internet connection.",
      };
      if (e.error !== "aborted") reject(new ListenError(messages[e.error] ?? "Couldn't understand that. Please try again."));
    };
    rec.onend = () => {
      active = null;
      if (transcript) resolve(transcript);
      else reject(new ListenError("I didn't catch that. Please try again."));
    };
    rec.start();
  });
}
