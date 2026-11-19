// Parking-sensor style distance beeps for the live camera.
// The closer the nearest obstacle in your path, the faster and higher the beeps.
// Beeps come from the obstacle's side (stereo) and dip in volume while VisionAI speaks.
import { clockToPan, isHeld, isSpeaking, unlockAudio } from "./speech";

type Level = "very close" | "close";

const SETTINGS: Record<Level, { every: number; freq: number }> = {
  "very close": { every: 230, freq: 1150 },
  close: { every: 620, freq: 860 },
};

let timer: number | null = null;
let currentKey = "";
let pan = 0;

function tone(freq: number, duration = 0.08, volume = 0.22, panValue = 0) {
  const ctx = unlockAudio();
  if (!ctx || ctx.state !== "running") return;
  const t = ctx.currentTime;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  const panner = ctx.createStereoPanner();
  osc.type = "sine";
  osc.frequency.value = freq;
  panner.pan.value = panValue;
  gain.gain.setValueAtTime(0, t);
  gain.gain.linearRampToValueAtTime(volume, t + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, t + duration);
  osc.connect(gain).connect(panner).connect(ctx.destination);
  osc.start(t);
  osc.stop(t + duration + 0.02);
}

/** Update the beeping for the nearest obstacle in the walking path (or null to stop). */
export function setObstacle(obstacle: { proximity: string; clock: number } | null) {
  const level = obstacle?.proximity as Level | undefined;
  if (!obstacle || !level || !(level in SETTINGS)) {
    stopBeeps();
    return;
  }
  pan = clockToPan(obstacle.clock);
  if (currentKey === level) return; // same rhythm; pan already updated
  stopBeeps();
  currentKey = level;
  const { every, freq } = SETTINGS[level];
  const beep = () => {
    if (isHeld()) return; // the user is talking
    tone(freq, 0.08, isSpeaking() ? 0.07 : 0.22, pan);
  };
  beep();
  timer = window.setInterval(beep, every);
}

export function stopBeeps() {
  if (timer !== null) window.clearInterval(timer);
  timer = null;
  currentKey = "";
}

/** Short, quiet "got it" tick when an action starts, so you know the tap worked. */
export function tick() {
  tone(660, 0.05, 0.12);
}
