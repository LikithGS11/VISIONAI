// VisionAI speech engine: ONE voice at a time, ever.
//
//  - "urgent"  (Careful, person very close!) interrupts anything and plays now.
//  - "normal"  (a result the user asked for) replaces whatever was playing.
//  - "chatter" (live-camera info) only plays when nothing else is; otherwise it's skipped.
//  Queued urgent/chatter messages older than STALE_MS are dropped — late info is wrong info.
//  While the microphone is listening, VisionAI stays silent (hold()).
//
// Voices: the device's own voice for the language when it has one (instant, offline);
// otherwise the server's /api/tts audio. Server audio can be panned left/right so an
// object on your left is heard from the left (headphones).
import { api } from "./api";

export type Priority = "urgent" | "normal" | "chatter";

interface SpeakOptions {
  priority?: Priority;
  /** -1 (left) … 0 (centre) … 1 (right). Applied to server audio. */
  pan?: number;
}

interface Item {
  text: string;
  lang: string;
  priority: Priority;
  pan: number;
  created: number;
}

const STALE_MS = 2500;
const RANK: Record<Priority, number> = { chatter: 0, normal: 1, urgent: 2 };

let rate = 1;
let preferDevice = false; // false: VisionAI's offline server voice; true: the device's own voice
let queue: Item[] = [];
let current: { item: Item; cancel: () => void } | null = null;
let turn = 0;
let held = false;
let speaking = false;
const listeners = new Set<(speaking: boolean) => void>();

// ---------------------------------------------------------------- state ----

function setSpeaking(value: boolean) {
  if (speaking === value) return;
  speaking = value;
  listeners.forEach((fn) => fn(value));
}

export function onSpeakingChange(fn: (speaking: boolean) => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export const isSpeaking = () => speaking;
export const isHeld = () => held;

/** Choose between the device's built-in voices and VisionAI's offline voices (on the server). */
export function setPreferDeviceVoice(on: boolean) {
  preferDevice = on;
}

export function setSpeechRate(value: number) {
  rate = Math.min(2, Math.max(0.6, value));
}

/** Silence VisionAI while the user is talking (so the microphone doesn't hear it). */
export function hold(on: boolean) {
  held = on;
  if (on) stopSpeaking();
}

// --------------------------------------------------------------- voices ----

const voiceCache = new Map<string, Promise<SpeechSynthesisVoice | null>>();

function deviceVoice(lang: string): Promise<SpeechSynthesisVoice | null> {
  if (!("speechSynthesis" in window)) return Promise.resolve(null);
  let found = voiceCache.get(lang);
  if (!found) {
    found = new Promise((resolve) => {
      const pick = () => {
        const voices = window.speechSynthesis.getVoices();
        const ofLang = voices.filter((v) => v.lang.toLowerCase().replace("_", "-").startsWith(lang));
        // Prefer Indian variants and the higher-quality "Natural"/"Google" voices.
        const score = (v: SpeechSynthesisVoice) =>
          (v.lang.toLowerCase().endsWith("-in") ? 2 : 0) + (/natural|google|neural/i.test(v.name) ? 1 : 0);
        resolve(ofLang.sort((a, b) => score(b) - score(a))[0] ?? null);
      };
      if (window.speechSynthesis.getVoices().length) pick();
      else {
        window.speechSynthesis.addEventListener("voiceschanged", pick, { once: true });
        setTimeout(pick, 1200);
      }
    });
    voiceCache.set(lang, found);
  }
  return found;
}

/** Does this device have its own voice for `lang`? (Otherwise server audio is used.) */
export const hasDeviceVoice = async (lang: string) => preferDevice && !!(await deviceVoice(lang));

// Small LRU cache of server audio, so repeated live warnings play instantly.
const audioCache = new Map<string, Promise<Blob>>();
const AUDIO_CACHE_MAX = 40;

function serverAudio(text: string, lang: string): Promise<Blob> {
  const key = `${lang}\u0000${text}`;
  let blob = audioCache.get(key);
  if (blob) {
    audioCache.delete(key);
    audioCache.set(key, blob); // mark as recently used
    return blob;
  }
  blob = api.tts(text, lang);
  blob.catch(() => audioCache.delete(key));
  audioCache.set(key, blob);
  if (audioCache.size > AUDIO_CACHE_MAX) audioCache.delete(audioCache.keys().next().value!);
  return blob;
}

/** Warm the cache so the first live warnings aren't delayed by a download. */
export async function preload(texts: string[], lang: string) {
  if (await hasDeviceVoice(lang)) return;
  texts.forEach((t) => void serverAudio(t, lang).catch(() => undefined));
}

// Long text: Chrome stops speaking after ~15 s, and short chunks cancel instantly.
function chunks(text: string): string[] {
  const sentences = text.match(/[^.!?।\n]+[.!?।]*\s*/g) ?? [text];
  const out: string[] = [];
  let buf = "";
  for (const s of sentences) {
    if ((buf + s).length > 220 && buf) {
      out.push(buf.trim());
      buf = "";
    }
    buf += s;
  }
  if (buf.trim()) out.push(buf.trim());
  return out;
}

let audioCtx: AudioContext | null = null;

/** Create/resume the audio context. Call from a user gesture (e.g. Start camera). */
export function unlockAudio(): AudioContext | null {
  const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctor) return null;
  audioCtx ??= new Ctor();
  if (audioCtx.state === "suspended") void audioCtx.resume();
  return audioCtx;
}

// -------------------------------------------------------------- playing ----

// Chrome bug: utterances can be garbage-collected mid-speech, and then `onend` never fires.
const pinned = new Set<SpeechSynthesisUtterance>();

/** Speak one chunk with a device voice. "failed" = the voice never started (broken/offline voice). */
function sayChunk(text: string, voice: SpeechSynthesisVoice, signal: AbortSignal): Promise<"ok" | "failed"> {
  return new Promise((resolve) => {
    const u = new SpeechSynthesisUtterance(text);
    let started = false;
    let startTimer = 0;
    let endTimer = 0;
    const finish = (result: "ok" | "failed") => {
      window.clearTimeout(startTimer);
      window.clearTimeout(endTimer);
      pinned.delete(u);
      resolve(result);
    };
    u.voice = voice;
    u.lang = voice.lang;
    u.rate = rate;
    u.onstart = () => (started = true);
    u.onend = () => finish("ok");
    u.onerror = () => finish(started ? "ok" : "failed");
    // Watchdogs: a voice that doesn't start in 3 s is broken; nothing should take longer than its length allows.
    startTimer = window.setTimeout(() => !started && finish("failed"), 3000);
    endTimer = window.setTimeout(() => finish("ok"), 4000 + (text.length * 160) / rate);
    signal.addEventListener("abort", () => finish("ok"), { once: true });
    pinned.add(u);
    window.speechSynthesis.speak(u);
  });
}

async function play(item: Item, myTurn: number, signal: AbortSignal): Promise<void> {
  const alive = () => myTurn === turn && !signal.aborted;
  const voice = preferDevice ? await deviceVoice(item.lang) : null;
  if (!alive()) return;

  let remaining = item.text;
  if (voice) {
    const parts = chunks(item.text);
    for (let i = 0; i < parts.length; i++) {
      if (!alive()) return;
      if ((await sayChunk(parts[i], voice, signal)) === "failed") {
        // This voice doesn't work here: stop using it and finish with the server voice.
        window.speechSynthesis.cancel();
        voiceCache.set(item.lang, Promise.resolve(null));
        remaining = parts.slice(i).join(" ");
        break;
      }
      if (i === parts.length - 1) return;
    }
    if (!alive()) return;
  }

  const blob = await serverAudio(remaining, item.lang);
  if (!alive()) return; // a newer message took over while this was downloading
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.playbackRate = rate;
  audio.preservesPitch = true;
  let pannerSource: MediaElementAudioSourceNode | null = null;
  const ctx = item.pan ? unlockAudio() : null;
  if (ctx) {
    pannerSource = ctx.createMediaElementSource(audio);
    const panner = ctx.createStereoPanner();
    panner.pan.value = Math.max(-1, Math.min(1, item.pan));
    pannerSource.connect(panner).connect(ctx.destination);
  }
  try {
    await new Promise<void>((resolve) => {
      audio.onended = audio.onerror = () => resolve();
      // Safety net: never let one clip block the queue (cap based on its length once known).
      audio.onloadedmetadata = () => {
        const ms = (audio.duration / rate) * 1000 + 1500;
        if (Number.isFinite(ms)) window.setTimeout(resolve, ms);
      };
      signal.addEventListener(
        "abort",
        () => {
          audio.pause();
          resolve();
        },
        { once: true },
      );
      audio.play().catch(() => resolve());
    });
  } finally {
    pannerSource?.disconnect();
    URL.revokeObjectURL(url);
  }
}

function next() {
  if (current || held) return;
  const now = performance.now();
  queue = queue.filter((i) => i.priority === "normal" || now - i.created < STALE_MS);
  const item = queue.shift();
  if (!item) {
    setSpeaking(false);
    return;
  }

  const myTurn = ++turn;
  const controller = new AbortController();
  current = {
    item,
    cancel: () => {
      controller.abort();
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    },
  };
  setSpeaking(true);
  play(item, myTurn, controller.signal)
    .catch(() => undefined) // a failed download just means this message is skipped
    .finally(() => {
      if (myTurn !== turn) return;
      current = null;
      next();
    });
}

function cancelCurrent() {
  if (!current) return;
  turn++;
  current.cancel();
  current = null;
}

/** Stop talking and forget anything queued. */
export function stopSpeaking() {
  queue = [];
  cancelCurrent();
  setSpeaking(false);
}

/** Say something. Never overlaps: see the priority rules at the top of this file. */
export function speak(text: string, lang: string, opts: SpeakOptions = {}): void {
  const item: Item = {
    text: text.trim(),
    lang,
    priority: opts.priority ?? "normal",
    pan: opts.pan ?? 0,
    created: performance.now(),
  };
  if (!item.text || held) return;

  const busy = !!current || queue.length > 0;
  if (item.priority === "chatter") {
    if (busy) return; // live info is only worth saying right now
    queue.push(item);
  } else if (item.priority === "urgent") {
    queue = [item];
    cancelCurrent();
  } else {
    // A new result replaces older ones — but never cuts off an urgent warning.
    if (current && RANK[current.item.priority] > RANK.normal) {
      queue = [item];
      return;
    }
    queue = [item];
    cancelCurrent();
  }
  next();
}

/** Clock hour (10..2) -> stereo pan (-1..1). */
export function clockToPan(clock: number | null | undefined): number {
  if (clock == null) return 0;
  const h = clock > 6 ? clock - 12 : clock; // 10 -> -2, 12 -> 0, 2 -> 2
  return Math.max(-1, Math.min(1, h / 2));
}
