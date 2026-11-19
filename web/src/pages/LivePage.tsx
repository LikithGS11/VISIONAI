import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, Eye, Hand, Play, Smartphone, Square, Vibrate } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { LiveArt } from "../components/art";
import { DirectionStyleToggle } from "../components/DirectionStyle";
import { MicButton, useVoiceAsk } from "../components/VoiceAsk";
import { Button, ErrorNotice, Eyebrow, ListenButton, PageHeading, Viewfinder } from "../components/ui";
import { useApp } from "../context/AppContext";
import { api, liveSocketUrl, type DetectedObject, type LiveMessage } from "../lib/api";
import { setObstacle, stopBeeps } from "../lib/beeper";
import { clockToPan, preload, speak, stopSpeaking, unlockAudio } from "../lib/speech";

type Status = "idle" | "starting" | "live";

const FRAME_WIDTH = 640; // enough for detection, small enough for mobile data
const MIN_FRAME_GAP_MS = 120;

function cameraErrorMessage(err: unknown): string {
  const name = err instanceof DOMException ? err.name : "";
  if (name === "NotAllowedError") return "Camera access was blocked. Allow the camera for this site in your browser settings, then try again.";
  if (name === "NotFoundError") return "No camera was found on this device.";
  if (name === "NotReadableError") return "The camera is being used by another app. Close it and try again.";
  return "Couldn't start the camera.";
}

function drawBoxes(canvas: HTMLCanvasElement, objects: DetectedObject[]) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.font = "bold 18px 'Atkinson Hyperlegible Next', sans-serif";
  for (const o of objects) {
    const urgent = o.position === "ahead" && o.proximity === "very close";
    ctx.lineWidth = 7;
    ctx.strokeStyle = "#16150F";
    ctx.strokeRect(o.x1, o.y1, o.x2 - o.x1, o.y2 - o.y1);
    ctx.lineWidth = 4;
    ctx.strokeStyle = urgent ? "#FF6A3D" : "#FFC800";
    ctx.strokeRect(o.x1, o.y1, o.x2 - o.x1, o.y2 - o.y1);
    const w = ctx.measureText(o.name).width + 14;
    ctx.fillStyle = urgent ? "#FF6A3D" : "#FFC800";
    ctx.fillRect(o.x1 - 2, Math.max(o.y1 - 28, 0), w, 28);
    ctx.fillStyle = "#16150F";
    ctx.fillText(o.name, o.x1 + 5, Math.max(o.y1 - 8, 20));
  }
}

// The urgent prefix is the most time-critical phrase; fetch its audio before it's needed.
const PRELOAD: Record<string, string> = {
  en: "Careful.",
  hi: "सावधान।",
  kn: "ಎಚ್ಚರಿಕೆ.",
  ta: "கவனம்.",
  te: "జాగ్రత్త.",
  ml: "ശ്രദ്ധിക്കുക.",
  mr: "सावधान.",
  bn: "সাবধান।",
};

const TIPS = [
  { icon: Smartphone, text: "Hold your phone at chest height, camera facing forward." },
  { icon: Hand, text: "Move slowly so detection can keep up." },
  { icon: Vibrate, text: "Your phone vibrates — and beeps faster — as something in your path gets closer." },
];

export default function LivePage({
  focusHeading,
  onClose,
}: {
  focusHeading: boolean;
  /** When shown over the chat: return there, passing the last thing the camera saw. */
  onClose?: (lastSummary: string) => void;
}) {
  const { lang, voiceOn, beepsOn, directionStyle, announce, tell } = useApp();
  const [status, setStatus] = useState<Status>("idle");
  const [summary, setSummary] = useState("");
  const [urgent, setUrgent] = useState(false);
  const [error, setError] = useState("");

  const videoRef = useRef<HTMLVideoElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const runningRef = useRef(false);
  const voiceRef = useRef(voiceOn);
  voiceRef.current = voiceOn;
  const langRef = useRef(lang);
  langRef.current = lang;
  const beepsRef = useRef(beepsOn);
  beepsRef.current = beepsOn;

  const stop = useCallback(() => {
    runningRef.current = false;
    socketRef.current?.close();
    socketRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    stopSpeaking();
    stopBeeps();
    const canvas = overlayRef.current;
    canvas?.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height);
    setStatus("idle");
    setUrgent(false);
  }, []);

  useEffect(() => stop, [stop]); // release the camera when leaving the page

  const grabFrame = useCallback((width = FRAME_WIDTH): HTMLCanvasElement | null => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return null;
    const frame = document.createElement("canvas");
    frame.width = width;
    frame.height = Math.round(video.videoHeight * (width / video.videoWidth));
    frame.getContext("2d")!.drawImage(video, 0, 0, frame.width, frame.height);
    return frame;
  }, []);

  const sendFrame = useCallback(() => {
    const socket = socketRef.current;
    if (!runningRef.current || !socket || socket.readyState !== WebSocket.OPEN) return;
    const frame = grabFrame();
    if (!frame) return void setTimeout(sendFrame, 200);
    const overlay = overlayRef.current;
    if (overlay && (overlay.width !== frame.width || overlay.height !== frame.height)) {
      overlay.width = frame.width;
      overlay.height = frame.height;
    }
    frame.toBlob((blob) => blob && socket.readyState === WebSocket.OPEN && socket.send(blob), "image/jpeg", 0.7);
  }, [grabFrame]);

  // "Describe this view" or a spoken question: send the current frame to the AI.
  const describeView = useMutation({
    mutationFn: async (question?: string) => {
      const frame = grabFrame(1280);
      if (!frame) throw new Error("The camera isn't ready yet.");
      const blob = await new Promise<Blob | null>((r) => frame.toBlob(r, "image/jpeg", 0.85));
      return question ? (await api.ask(blob!, lang, question)).text : (await api.describe(blob!, lang)).text;
    },
    onSuccess: (text) => tell(text, { lang }),
    onError: (err) => tell(err.message),
  });

  const start = async () => {
    unlockAudio(); // must happen inside the tap, or beeps / side audio stay silent on phones
    void preload([PRELOAD[langRef.current] ?? PRELOAD.en], langRef.current);
    setError("");
    setSummary("");
    setStatus("starting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 } },
        audio: false,
      });
      streamRef.current = stream;
      const video = videoRef.current!;
      video.srcObject = stream;
      await video.play();
    } catch (err) {
      setError(cameraErrorMessage(err));
      stop();
      return;
    }

    runningRef.current = true;
    const socket = new WebSocket(liveSocketUrl(langRef.current, directionStyle));
    socketRef.current = socket;
    let lastSent = 0;

    socket.onopen = () => {
      setStatus("live");
      tell("Live camera on.");
      lastSent = performance.now();
      sendFrame();
    };
    socket.onmessage = (event) => {
      const msg: LiveMessage = JSON.parse(event.data);
      if (msg.objects && overlayRef.current) drawBoxes(overlayRef.current, msg.objects);
      if (msg.summary) setSummary(msg.summary);
      setUrgent(!!msg.objects?.some((o) => o.position === "ahead" && o.proximity === "very close"));
      // Distance beeps for the nearest obstacle in the walking path (10:30 to 1:30).
      if (beepsRef.current && msg.objects) {
        const inPath = msg.objects
          .filter((o) => o.position === "ahead" && o.proximity !== "far")
          .sort((a, b) => (a.proximity === b.proximity ? (b.x2 - b.x1) * (b.y2 - b.y1) - (a.x2 - a.x1) * (a.y2 - a.y1) : a.proximity === "very close" ? -1 : 1));
        setObstacle(inPath[0] ?? null);
      } else stopBeeps();

      if (msg.announce) {
        if (msg.urgent && "vibrate" in navigator) navigator.vibrate([180, 90, 180]);
        if (voiceRef.current)
          speak(msg.announce, langRef.current, { priority: msg.urgent ? "urgent" : "chatter", pan: clockToPan(msg.clock) });
        else announce(msg.announce, msg.urgent);
      }
      // Send the next frame only after this one is answered, so slow networks never build a backlog.
      const wait = Math.max(0, MIN_FRAME_GAP_MS - (performance.now() - lastSent));
      setTimeout(() => {
        lastSent = performance.now();
        sendFrame();
      }, wait);
    };
    socket.onclose = () => {
      if (runningRef.current) {
        setError("Lost connection to the VisionAI server.");
        stop();
      }
    };
  };

  const active = status !== "idle";
  const voice = useVoiceAsk((q) => describeView.mutate(q));

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <Eyebrow>Live camera</Eyebrow>
          <PageHeading focusOnMount={focusHeading}>What's around me?</PageHeading>
        </div>
        {onClose && (
          <Button
            size="lg"
            onClick={() => {
              stop();
              onClose(summary);
            }}
          >
            <ArrowLeft aria-hidden className="size-5" /> Back to chat
          </Button>
        )}
        {active && (
          <span
            className={`inline-flex items-center gap-2 rounded-full px-4 py-2 font-bold ${
              status === "live" ? "bg-night text-night-ink" : "bg-paper-2"
            }`}
          >
            <span aria-hidden className={`size-3 rounded-full ${status === "live" ? "bg-go pulse-ring" : "bg-ink-soft"}`} />
            {status === "live" ? "Live" : "Starting…"}
          </span>
        )}
      </div>

      {error && <ErrorNotice>{error}</ErrorNotice>}

      {!active && (
        <div className="relative isolate grid items-center gap-8 overflow-hidden rounded-[32px] bg-night p-8 dark:ring-2 dark:ring-line text-night-ink sm:p-12 lg:grid-cols-[1.2fr_1fr]">
          <span aria-hidden className="tactile-light fade-left absolute inset-y-0 right-0 -z-10 w-1/2" />
          <div>
            <p className="display text-4xl text-signal sm:text-5xl">Hear the room.</p>
            <p className="mt-4 max-w-md text-lg text-night-ink/80">
              VisionAI watches through your camera and tells you what's around — and warns you when something is close
              in front of you.
            </p>
            <Button tone="signal" size="xl" className="mt-8" onClick={start}>
              <Play aria-hidden className="size-6 fill-current" /> Start camera
            </Button>
            <div className="mt-8 [&_legend]:text-night-ink/70">
              <DirectionStyleToggle />
            </div>
          </div>
          <LiveArt className="mx-auto w-full max-w-xs" />
        </div>
      )}

      <div className={active ? "grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]" : "hidden"}>
        <Viewfinder className={`overflow-hidden rounded-[28px] bg-night ${urgent ? "shadow-[0_0_0_6px_#FF6A3D]" : ""}`}>
          <div className="relative">
            <video ref={videoRef} muted playsInline className="block h-auto w-full" />
            <canvas ref={overlayRef} aria-hidden className="absolute inset-0 h-full w-full" />
          </div>
          {summary && (
            <p className="absolute inset-x-4 bottom-14 rounded-2xl bg-night/85 px-5 py-3 text-center text-xl font-bold text-night-ink backdrop-blur-sm">
              {summary}
            </p>
          )}
        </Viewfinder>

        <div className="space-y-4">
          <section aria-label="What the camera sees" className="rounded-3xl border-2 border-line bg-surface p-6">
            <p className="text-sm font-bold uppercase tracking-[0.14em] text-ink-soft">Right now</p>
            <p className={`display mt-3 text-3xl ${urgent ? "text-warn" : ""}`}>{summary || "Looking…"}</p>
          </section>
          <div className="flex flex-wrap gap-3">
            {voice.supported && (
              <MicButton
                listening={voice.listening}
                onClick={() => void voice.toggle()}
                disabled={status !== "live" || describeView.isPending}
                className="min-h-14 px-6 text-lg"
                label="Ask about this view"
              />
            )}
            <Button tone="signal" size="lg" disabled={status !== "live" || describeView.isPending} onClick={() => describeView.mutate(undefined)}>
              <Eye aria-hidden className="size-6" /> {describeView.isPending ? "Looking…" : "Describe this view"}
            </Button>
            <Button size="lg" onClick={stop}>
              <Square aria-hidden className="size-5 fill-current" /> Stop
            </Button>
          </div>
          {voice.error && <ErrorNotice>{voice.error}</ErrorNotice>}
          {describeView.isError && <ErrorNotice>{describeView.error.message}</ErrorNotice>}
          {describeView.data && (
            <section aria-label="Scene description" className="rise space-y-4 rounded-3xl border-2 border-line bg-surface p-6">
              <p className="text-xl leading-relaxed">{describeView.data}</p>
              <ListenButton text={describeView.data} lang={lang} />
            </section>
          )}
        </div>
      </div>

      <ul className="grid gap-4 sm:grid-cols-3">
        {TIPS.map(({ icon: Icon, text }) => (
          <li key={text} className="flex gap-4 rounded-3xl border-2 border-line p-5">
            <span aria-hidden className="grid size-12 shrink-0 place-items-center rounded-2xl bg-signal-soft">
              <Icon className="size-6" />
            </span>
            <span className="text-ink-soft">{text}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
