import { Mic, MicOff } from "lucide-react";
import { useState } from "react";

import { useApp } from "../context/AppContext";
import { canListen, canRecord, listenOnce, recordAndTranscribe, stopListening } from "../lib/listen";
import { hold } from "../lib/speech";

/** Tap, speak a question, get it back as text. Shared by the Photo and Live pages. */
export function useVoiceAsk(onQuestion: (question: string) => void) {
  const { lang, announce, tell, config, voiceInput } = useApp();

  // Private (on-device Whisper) where it's accurate; the browser's recogniser otherwise.
  const local =
    !!config?.local_stt &&
    canRecord() &&
    (voiceInput === "local" || !canListen() || (voiceInput === "auto" && config.local_stt_languages.includes(lang)));
  const [listening, setListening] = useState(false);
  const [error, setError] = useState("");

  const toggle = async () => {
    if (listening) {
      stopListening();
      setListening(false);
      hold(false);
      return;
    }
    hold(true); // VisionAI stays silent (and beeps pause) while you talk
    setError("");
    setListening(true);
    announce("Listening.");
    let failure = "";
    let question = "";
    try {
      question = local ? await recordAndTranscribe(lang) : await listenOnce(lang);
    } catch (err) {
      failure = err instanceof Error ? err.message : "Couldn't hear that.";
    } finally {
      setListening(false);
      hold(false);
    }
    // Only after the mic is closed may VisionAI speak again.
    if (failure) {
      setError(failure);
      tell(failure);
    } else if (question) onQuestion(question);
  };

  return { supported: canListen() || (!!config?.local_stt && canRecord()), listening, error, toggle, private: local };
}

export function MicButton({
  listening,
  onClick,
  disabled,
  className = "",
  label = "Ask by voice",
}: {
  listening: boolean;
  onClick: () => void;
  disabled?: boolean;
  className?: string;
  label?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={listening}
      className={`keycap ${listening ? "keycap-signal pulse-ring" : "keycap-night"} ${className}`}
    >
      {listening ? <MicOff aria-hidden className="size-6" /> : <Mic aria-hidden className="size-6" />}
      {listening ? "Listening… tap to stop" : label}
    </button>
  );
}
