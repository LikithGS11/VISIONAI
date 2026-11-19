import { Settings, X } from "lucide-react";
import { useRef, type ReactNode } from "react";

import { SPEEDS, useApp } from "../context/AppContext";
import { NATIVE_NAMES } from "../lib/languages";
import { setSpeechRate, speak, stopSpeaking } from "../lib/speech";
import { DirectionStyleToggle } from "./DirectionStyle";

function Segmented<T extends string | number | boolean>({
  name,
  legend,
  hint,
  value,
  options,
  onChange,
}: {
  name: string;
  legend: string;
  hint?: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <fieldset>
      <legend className="mb-1 text-lg font-bold">{legend}</legend>
      {hint && <p className="mb-3 text-ink-soft">{hint}</p>}
      <div className="flex flex-wrap gap-1 rounded-2xl border-2 border-line bg-paper p-1">
        {options.map((o) => {
          const active = o.value === value;
          return (
            <label
              key={String(o.value)}
              className={`flex min-h-12 flex-1 cursor-pointer items-center justify-center rounded-xl px-3 text-center font-bold transition-colors has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-focus ${
                active ? "bg-ink text-paper" : "text-ink-soft hover:text-ink"
              }`}
            >
              <input
                type="radio"
                name={name}
                checked={active}
                onChange={() => onChange(o.value)}
                className="sr-only"
              />
              {o.label}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

function Row({ children }: { children: ReactNode }) {
  return <div className="border-b-2 border-line py-5 last:border-b-0">{children}</div>;
}

/** Header button + accessible modal with all voice/sound preferences. */
export function SettingsButton() {
  const ref = useRef<HTMLDialogElement>(null);
  const { lang, voiceOn, setVoiceOn, speed, setSpeed, beepsOn, setBeepsOn, voiceInput, setVoiceInput, voiceEngine, setVoiceEngine, config } =
    useApp();

  const preview = (s: number) => {
    setSpeed(s);
    setSpeechRate(s); // apply now so the preview below uses the new speed
    if (voiceOn) speak("This is how fast I will speak.", "en");
  };

  return (
    <>
      <button
        type="button"
        onClick={() => ref.current?.showModal()}
        className="inline-flex min-h-11 min-w-11 items-center justify-center gap-2 rounded-full border-2 border-ink bg-ink px-2.5 font-bold text-paper sm:px-4"
      >
        <Settings aria-hidden className="size-5" />
        <span className="hidden sm:inline">Settings</span>
        <span className="sr-only sm:hidden">Settings</span>
      </button>

      <dialog
        ref={ref}
        aria-labelledby="settings-title"
        onClose={() => stopSpeaking()}
        className="m-auto w-[min(36rem,calc(100vw-2rem))] rounded-[28px] border-2 border-line bg-surface p-0 text-ink backdrop:bg-black/60"
      >
        <div className="flex items-center justify-between border-b-2 border-line px-6 py-4">
          <h2 id="settings-title" className="display text-3xl">
            Settings
          </h2>
          <button
            type="button"
            onClick={() => ref.current?.close()}
            className="grid size-12 place-items-center rounded-full hover:bg-paper-2"
            aria-label="Close settings"
          >
            <X aria-hidden className="size-6" />
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto px-6">
          <Row>
            <Segmented
              name="voice"
              legend="Who reads results aloud?"
              hint="Using TalkBack, NVDA or VoiceOver? Choose your screen reader so you never hear two voices at once."
              value={voiceOn}
              options={[
                { value: true, label: "VisionAI voice" },
                { value: false, label: "My screen reader" },
              ]}
              onChange={setVoiceOn}
            />
          </Row>
          <Row>
            <Segmented
              name="speed"
              legend="Speaking speed"
              value={speed}
              options={SPEEDS.map((s) => ({ value: s.value as number, label: s.label }))}
              onChange={preview}
            />
          </Row>
          {config?.local_tts && (
            <Row>
              <Segmented
                name="voice-engine"
                legend="Voice"
                hint="VisionAI's offline voices work without internet. Your device's voices may sound smoother but some need internet."
                value={voiceEngine}
                options={[
                  { value: "local", label: "Offline voice" },
                  { value: "device", label: "Device voice" },
                ]}
                onChange={setVoiceEngine}
              />
            </Row>
          )}
          {config?.local_stt && (
            <Row>
              <Segmented
                name="voice-input"
                legend="Microphone"
                hint="“On this device” keeps your voice private (works best for English, Hindi and Tamil). “Browser” uses Google's recognition, which is better for other languages."
                value={voiceInput}
                options={[
                  { value: "auto", label: "Automatic" },
                  { value: "local", label: "On this device" },
                  { value: "browser", label: "Browser" },
                ]}
                onChange={setVoiceInput}
              />
            </Row>
          )}
          <Row>
            <Segmented
              name="beeps"
              legend="Distance beeps (live camera)"
              hint="Like a parking sensor: faster beeps as something in your path gets closer. Best with headphones — the beeps come from the obstacle's side."
              value={beepsOn}
              options={[
                { value: true, label: "On" },
                { value: false, label: "Off" },
              ]}
              onChange={setBeepsOn}
            />
          </Row>
          <Row>
            <DirectionStyleToggle />
          </Row>
          <p className="pb-5 text-sm text-ink-soft">
            Language: <strong>{NATIVE_NAMES[lang] ?? lang}</strong> — change it with the language menu in the header.
          </p>
        </div>
      </dialog>
    </>
  );
}
