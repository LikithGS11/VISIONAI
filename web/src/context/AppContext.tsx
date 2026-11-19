import { useQuery } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { api, type AppConfig, type DirectionStyle } from "../lib/api";
import { setPreferDeviceVoice, setSpeechRate, speak } from "../lib/speech";

export const SPEEDS = [
  { value: 0.85, label: "Slow" },
  { value: 1, label: "Normal" },
  { value: 1.3, label: "Fast" },
  { value: 1.65, label: "Very fast" },
] as const;

export type VoiceInput = "auto" | "local" | "browser";
export type VoiceEngine = "local" | "device";

interface AppState {
  config: AppConfig | undefined;
  lang: string;
  setLang: (lang: string) => void;
  /** true: VisionAI's own voice speaks. false: screen-reader mode (results go to the screen reader). */
  voiceOn: boolean;
  setVoiceOn: (on: boolean) => void;
  speed: number;
  setSpeed: (speed: number) => void;
  /** Voice input: "auto" (private where accurate), "local" (always on this device), "browser". */
  voiceInput: VoiceInput;
  setVoiceInput: (v: VoiceInput) => void;
  /** Voice output: "local" = VisionAI's offline voices, "device" = the phone/PC's own voices. */
  voiceEngine: VoiceEngine;
  setVoiceEngine: (v: VoiceEngine) => void;
  /** Parking-sensor beeps for obstacles in the live camera. */
  beepsOn: boolean;
  setBeepsOn: (on: boolean) => void;
  /** "sides" = left / ahead / right; "clock" = 10 to 2 o'clock. */
  directionStyle: DirectionStyle;
  setDirectionStyle: (style: DirectionStyle) => void;
  /** Screen-reader announcement. `urgent` interrupts the screen reader. */
  announce: (message: string, urgent?: boolean) => void;
  /**
   * Tell the user something through whichever channel they use:
   * VisionAI's voice, or their screen reader.
   */
  tell: (message: string, opts?: { lang?: string; urgent?: boolean }) => void;
}

const AppContext = createContext<AppState | null>(null);

function stored(key: string, fallback: string): string {
  try {
    return localStorage.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}

function store(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* private mode etc. — preference just won't persist */
  }
}

function usePref<T>(key: string, fallback: T, parse: (raw: string) => T): [T, (v: T) => void] {
  const [value, setValue] = useState<T>(() => parse(stored(key, String(fallback))));
  const set = (v: T) => {
    setValue(v);
    store(key, String(v));
  };
  return [value, set];
}

export function AppProvider({ children }: { children: ReactNode }) {
  const { data: config } = useQuery({ queryKey: ["config"], queryFn: api.config, staleTime: Infinity });
  const [lang, setLang] = usePref("visionai.lang", "en", (r) => r);
  const [voiceOn, setVoiceOn] = usePref("visionai.voice", true, (r) => r !== "false" && r !== "off");
  const [speed, setSpeed] = usePref("visionai.speed", 1, (r) => (Number.isFinite(+r) && +r > 0 ? +r : 1));
  const [beepsOn, setBeepsOn] = usePref("visionai.beeps", true, (r) => r !== "false");
  const [voiceInput, setVoiceInput] = usePref<VoiceInput>("visionai.voiceInput", "auto", (r) =>
    r === "local" || r === "browser" ? r : "auto",
  );
  const [voiceEngine, setVoiceEngine] = usePref<VoiceEngine>("visionai.voiceEngine", "local", (r) =>
    r === "device" ? "device" : "local",
  );
  const [directionStyle, setDirectionStyle] = usePref<DirectionStyle>("visionai.directions", "sides", (r) =>
    r === "clock" ? "clock" : "sides",
  );
  const [polite, setPolite] = useState("");
  const [assertive, setAssertive] = useState("");

  useEffect(() => setSpeechRate(speed), [speed]);
  // Offline voices need the server to have them; otherwise use the device's voices.
  useEffect(() => setPreferDeviceVoice(voiceEngine === "device" || config?.local_tts === false), [voiceEngine, config]);

  const announce = useCallback((text: string, urgent = false) => {
    // Clear first so repeating the same message is still announced.
    const set = urgent ? setAssertive : setPolite;
    set("");
    setTimeout(() => set(text), 60);
  }, []);

  const tell = useCallback(
    (text: string, opts: { lang?: string; urgent?: boolean } = {}) => {
      if (voiceOn) speak(text, opts.lang ?? "en", { priority: opts.urgent ? "urgent" : "normal" });
      else announce(text, opts.urgent);
    },
    [voiceOn, announce],
  );

  return (
    <AppContext.Provider
      value={{
        config,
        lang,
        setLang,
        voiceOn,
        setVoiceOn,
        speed,
        setSpeed,
        beepsOn,
        setBeepsOn,
        voiceInput,
        setVoiceInput,
        voiceEngine,
        setVoiceEngine,
        directionStyle,
        setDirectionStyle,
        announce,
        tell,
      }}
    >
      {children}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {polite}
      </div>
      <div aria-live="assertive" aria-atomic="true" className="sr-only">
        {assertive}
      </div>
    </AppContext.Provider>
  );
}

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside <AppProvider>");
  return ctx;
}
