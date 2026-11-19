import { Check, CircleAlert, Copy, Square, Volume2 } from "lucide-react";
import { useEffect, useRef, useState, type ButtonHTMLAttributes, type ReactNode } from "react";

import { useApp } from "../context/AppContext";
import { isSpeaking, onSpeakingChange, speak, stopSpeaking } from "../lib/speech";

type Tone = "plain" | "signal" | "night" | "quiet";
type Size = "md" | "lg" | "xl";

const TONES: Record<Tone, string> = {
  plain: "keycap",
  signal: "keycap keycap-signal",
  night: "keycap keycap-night",
  quiet: "inline-flex items-center gap-2 font-bold underline decoration-2 underline-offset-4 hover:decoration-signal",
};

const SIZES: Record<Size, string> = {
  md: "",
  lg: "min-h-14 px-6 text-lg",
  xl: "min-h-16 px-8 text-xl",
};

export function Button({
  tone = "plain",
  size = "md",
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { tone?: Tone; size?: Size }) {
  return (
    <button type="button" className={`${TONES[tone]} ${tone === "quiet" ? "" : SIZES[size]} ${className}`} {...props}>
      {children}
    </button>
  );
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <p className="mb-3 inline-flex items-center gap-2 text-sm font-bold uppercase tracking-[0.14em] text-ink-soft">
      <span aria-hidden className="size-2.5 rounded-full bg-signal ring-2 ring-ink/80" />
      {children}
    </p>
  );
}

/** Page title. Takes focus after navigation so screen readers announce the new page. */
export function PageHeading({ children, focusOnMount }: { children: ReactNode; focusOnMount: boolean }) {
  const ref = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (focusOnMount) ref.current?.focus();
  }, [focusOnMount]);
  return (
    <h1 ref={ref} tabIndex={-1} className="display text-[2.6rem] outline-none sm:text-6xl">
      {children}
    </h1>
  );
}

export function Thinking({ label }: { label: string }) {
  const { voiceOn } = useApp();
  return (
    <div role={voiceOn ? undefined : "status"} className="rise flex items-center gap-4 rounded-2xl border-2 border-dashed border-line p-5 text-lg">
      <span aria-hidden className="dots text-ink">
        <span />
        <span />
        <span />
      </span>
      {label}
    </div>
  );
}

export function ErrorNotice({ children }: { children: ReactNode }) {
  return (
    <div role="alert" className="rise flex gap-3 rounded-2xl border-2 border-warn bg-warn-soft p-4 text-ink">
      <CircleAlert aria-hidden className="mt-0.5 size-6 shrink-0 text-warn" />
      <div className="text-lg">{children}</div>
    </div>
  );
}

/** Yellow camera-viewfinder corners around any content. */
export function Viewfinder({ children, className = "" }: { children: ReactNode; className?: string }) {
  const corner = "pointer-events-none absolute size-9 border-signal";
  return (
    <div className={`relative ${className}`}>
      {children}
      <span aria-hidden className={`${corner} left-3 top-3 rounded-tl-xl border-l-[5px] border-t-[5px]`} />
      <span aria-hidden className={`${corner} right-3 top-3 rounded-tr-xl border-r-[5px] border-t-[5px]`} />
      <span aria-hidden className={`${corner} bottom-3 left-3 rounded-bl-xl border-b-[5px] border-l-[5px]`} />
      <span aria-hidden className={`${corner} bottom-3 right-3 rounded-br-xl border-b-[5px] border-r-[5px]`} />
    </div>
  );
}

export function useSpeaking(): boolean {
  const [speaking, setSpeaking] = useState(isSpeaking);
  useEffect(() => onSpeakingChange(setSpeaking), []);
  return speaking;
}

export function ListenButton({ text, lang }: { text: string; lang: string }) {
  const speaking = useSpeaking();
  return speaking ? (
    <Button onClick={stopSpeaking}>
      <Square aria-hidden className="size-4 fill-current" /> Stop
    </Button>
  ) : (
    <Button tone="signal" onClick={() => speak(text, lang)}>
      <Volume2 aria-hidden className="size-5" /> Listen
    </Button>
  );
}

export function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard blocked; nothing useful to do */
    }
  };
  return (
    <Button onClick={copy} aria-live="polite">
      {copied ? <Check aria-hidden className="size-5" /> : <Copy aria-hidden className="size-5" />}
      {copied ? "Copied" : "Copy"}
    </Button>
  );
}

/** Floating "now speaking" bar with a stop button, shown on every page. */
export function SpeakingBar() {
  const speaking = useSpeaking();
  if (!speaking) return null;
  return (
    <div className="rise fixed inset-x-0 top-20 z-40 flex justify-center px-4">
      <div className="flex items-center gap-4 rounded-full bg-night py-2 pl-5 pr-2 text-night-ink shadow-[0_10px_30px_-10px_rgb(0_0_0/0.6)]">
        <span aria-hidden className="eq">
          <span />
          <span />
          <span />
          <span />
        </span>
        <span className="font-bold">Speaking</span>
        <button
          type="button"
          onClick={stopSpeaking}
          className="inline-flex min-h-11 items-center gap-2 rounded-full bg-signal px-4 font-bold text-night"
        >
          <Square aria-hidden className="size-4 fill-current" /> Stop
        </button>
      </div>
    </div>
  );
}
