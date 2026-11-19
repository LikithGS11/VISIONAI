import { ArrowUp, ShieldCheck, Banknote, Camera, Eye, FileText, HandHelping, ImagePlus, Mic, MicOff, Plus, ScanSearch, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";

import { BrandMark, LanguageSelect, Wordmark } from "../components/brand";
import { CardView, SUGGESTIONS } from "../components/chat/cards";
import { spokenText, type Card, type Message } from "../components/chat/types";
import { SettingsButton } from "../components/SettingsPanel";
import { useVoiceAsk } from "../components/VoiceAsk";
import { useApp } from "../context/AppContext";
import { api } from "../lib/api";
import { tick } from "../lib/beeper";
import { prepareImage } from "../lib/image";
import { detectIntent, type Intent } from "../lib/intents";
import { NATIVE_NAMES } from "../lib/languages";
import { getOrigin } from "../lib/location";
import { stopSpeaking } from "../lib/speech";
import LivePage from "./LivePage";

interface Photo {
  blob: Blob;
  url: string;
}

const PENDING: Record<Intent["kind"], string> = {
  describe: "Looking at your photo",
  read: "Reading the text",
  objects: "Looking for objects",
  currency: "Checking the money",
  assist: "Thinking it through",
  ask: "Thinking about your question",
  route: "Finding a walking route",
  translate: "Translating",
  live: "Opening the live camera",
  help: "",
  chat: "Thinking",
};

const PHOTO_ACTIONS: { label: string; intent: Intent; icon: typeof Eye }[] = [
  { label: "Describe", intent: { kind: "describe" }, icon: Eye },
  { label: "Read text", intent: { kind: "read" }, icon: FileText },
  { label: "Find objects", intent: { kind: "objects" }, icon: ScanSearch },
  { label: "Money", intent: { kind: "currency" }, icon: Banknote },
  { label: "Help me", intent: { kind: "assist" }, icon: HandHelping },
];

let nextId = 1;
const now = () => new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

function greeting(): string {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
}

// ---------------------------------------------------------------- views ----

function UserBubble({ m }: { m: Message }) {
  return (
    <div className="rise flex justify-end">
      <div className="max-w-[85%] space-y-2 sm:max-w-[70%]">
        {m.image && (
          <img src={m.image} alt="Photo you sent" className="ml-auto max-h-72 rounded-3xl border-2 border-line object-cover" />
        )}
        {m.text && (
          <p className="rounded-3xl rounded-br-lg bg-ink px-5 py-3 text-lg text-paper">
            <span className="sr-only">You said: </span>
            {m.text}
          </p>
        )}
      </div>
    </div>
  );
}

function AssistantMessage({ m }: { m: Message }) {
  return (
    <div className="rise flex gap-3">
      <BrandMark className="mt-1 size-9 shrink-0" />
      <div className="min-w-0 flex-1">
        <h2 className="sr-only">VisionAI said:</h2>
        {m.pending ? (
          <p role="status" className="flex items-center gap-3 py-2 text-lg text-ink-soft">
            <span aria-hidden className="dots text-ink">
              <span />
              <span />
              <span />
            </span>
            {m.pending}…
          </p>
        ) : (
          m.card && <CardView card={m.card} />
        )}
      </div>
    </div>
  );
}

function EmptyState({ onSuggestion }: { onSuggestion: (i: number) => void }) {
  const { lang, config } = useApp();
  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center px-2 pt-6 text-center sm:pt-12">
      <BrandMark className="size-16" />
      <p className="mt-6 text-lg font-bold text-ink-soft">{greeting()}.</p>
      <h1 className="display mt-2 text-[2.4rem] sm:text-5xl">What would you like to see?</h1>
      <p className="mt-3 max-w-lg text-lg text-ink-soft">
        Send a photo, type, or tap the microphone and speak. I'll answer out loud in{" "}
        <strong className="text-ink">{NATIVE_NAMES[lang] ?? "English"}</strong>.
      </p>
      {config?.ai_provider === "local" && (
        <p className="mt-4 inline-flex items-center gap-2 rounded-full border-2 border-go px-4 py-1.5 text-sm font-bold text-go">
          <ShieldCheck aria-hidden className="size-4" /> Private: the AI runs on this device. Nothing is sent online.
        </p>
      )}
      <ul className="mt-8 grid w-full gap-3 text-left sm:grid-cols-2 lg:grid-cols-3">
        {SUGGESTIONS.map(({ icon: Icon, title, body }, i) => (
          <li key={title}>
            <button
              type="button"
              onClick={() => onSuggestion(i)}
              className="group flex h-full w-full gap-3 rounded-3xl border-2 border-line bg-surface p-4 text-left transition-colors hover:border-ink"
            >
              <span
                aria-hidden
                className="grid size-11 shrink-0 place-items-center rounded-2xl bg-signal-soft transition-colors group-hover:bg-signal group-hover:text-night"
              >
                <Icon className="size-5" />
              </span>
              <span>
                <strong className="block text-lg leading-tight">{title}</strong>
                <span className="text-sm text-ink-soft">{body}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ----------------------------------------------------------------- page ----

export default function ChatPage({ openLiveOnStart = false }: { openLiveOnStart?: boolean }) {
  const { config, lang, voiceOn, directionStyle, tell } = useApp();
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [attachment, setAttachment] = useState<Photo | null>(null);
  const [activePhoto, setActivePhoto] = useState<Photo | null>(null);
  const [busy, setBusy] = useState(false);
  const [liveOpen, setLiveOpen] = useState(openLiveOnStart);

  const fileInput = useRef<HTMLInputElement>(null);
  const textRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const afterPhoto = useRef<string | null>(null); // a suggestion waiting for the user to pick a photo
  const photos = useRef<string[]>([]); // object URLs to free on "New chat"

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  useEffect(() => {
    if (!text && textRef.current) {
      textRef.current.style.height = "";
      textRef.current.style.overflowY = "hidden";
    }
  }, [text]);

  const push = (m: Omit<Message, "id" | "time">) => {
    const msg = { ...m, id: nextId++, time: now() };
    setMessages((prev) => [...prev, msg]);
    return msg.id;
  };
  const finish = (id: number, card: Card) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, pending: undefined, card } : m)));
    const say = spokenText(card);
    if (say?.text) tell(say.text, { lang: say.lang });
  };

  const respond = useCallback(
    async (intent: Intent, photo: Photo | null): Promise<Card> => {
      const needPhoto = () => {
        if (!photo) throw new Error("Attach a photo first — tap the + button.");
        return photo.blob;
      };
      switch (intent.kind) {
        case "describe":
          return { type: "answer", title: "Description", text: (await api.describe(needPhoto(), lang)).text, lang };
        case "assist":
          return { type: "answer", title: "Help", text: (await api.assist(needPhoto(), lang)).text, lang };
        case "currency":
          return { type: "answer", title: "Money", text: (await api.currency(needPhoto(), lang)).text, lang };
        case "ask":
          return { type: "answer", title: "Answer", text: (await api.ask(needPhoto(), lang, intent.question)).text, lang };
        case "read": {
          const r = await api.ocr(needPhoto(), lang);
          return { type: "read", text: r.found ? r.text : "I couldn't find any readable text.", found: r.found, source: r.source, lang };
        }
        case "objects": {
          const d = await api.detect(needPhoto(), lang, directionStyle);
          return { type: "objects", detection: d, image: photo!.url, text: d.summary, lang };
        }
        case "route": {
          const origin = await getOrigin(config?.default_location);
          const route = await api.route(intent.destination, origin.lat, origin.lon, lang);
          return { type: "route", route, origin, lang };
        }
        case "translate": {
          if (lang === "en") throw new Error("Choose your language in the menu at the top first, then ask me to translate.");
          return { type: "translation", source: intent.text, text: (await api.translate([intent.text], lang)).translations[0], lang };
        }
        case "chat":
          return { type: "answer", title: "VisionAI", text: (await api.chat(intent.message, lang)).text, lang };
        case "help":
        case "live":
          return { type: "help" };
      }
    },
    [lang, directionStyle, config],
  );

  const send = useCallback(
    async (raw: string, opts: { intent?: Intent; photo?: Photo | null } = {}) => {
      if (busy) return;
      const message = raw.trim();
      const newPhoto = opts.photo !== undefined ? opts.photo : attachment;
      if (!message && !newPhoto && !opts.intent) return;

      stopSpeaking();
      const photo = newPhoto ?? activePhoto;
      const intent = opts.intent ?? detectIntent(message, !!photo);

      push({ role: "user", text: message || undefined, image: newPhoto?.url });
      if (newPhoto) setActivePhoto(newPhoto);
      setAttachment(null);
      setText("");

      if (intent.kind === "live") {
        setLiveOpen(true);
        return;
      }
      if (intent.kind === "help") {
        const id = push({ role: "assistant" });
        finish(id, { type: "help" });
        return;
      }

      tick();
      setBusy(true);
      const id = push({ role: "assistant", pending: PENDING[intent.kind] });
      try {
        finish(id, await respond(intent, photo));
      } catch (err) {
        finish(id, { type: "error", message: err instanceof Error ? err.message : "Something went wrong." });
      } finally {
        setBusy(false);
        textRef.current?.focus();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [busy, attachment, activePhoto, respond],
  );

  const pickPhoto = async (file: Blob) => {
    const blob = await prepareImage(file);
    const photo = { blob, url: URL.createObjectURL(blob) };
    photos.current.push(photo.url);
    const queued = afterPhoto.current;
    afterPhoto.current = null;
    if (queued) void send(queued, { photo });
    else {
      setAttachment(photo);
      textRef.current?.focus();
    }
  };

  const onSuggestion = (i: number) => {
    const s = SUGGESTIONS[i];
    if (s.needsPhoto) {
      afterPhoto.current = s.prompt;
      fileInput.current?.click();
    } else if (s.prompt.endsWith(" ")) {
      setText(s.prompt);
      requestAnimationFrame(() => {
        const el = textRef.current;
        el?.focus();
        el?.setSelectionRange(s.prompt.length, s.prompt.length);
      });
    } else void send(s.prompt);
  };

  const newChat = () => {
    stopSpeaking();
    photos.current.forEach((u) => URL.revokeObjectURL(u));
    photos.current = [];
    setMessages([]);
    setAttachment(null);
    setActivePhoto(null);
    setText("");
    textRef.current?.focus();
  };

  const voice = useVoiceAsk((q) => void send(q));

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void send(text);
  };
  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      void send(text);
    }
  };

  const photoInPlay = attachment ?? activePhoto;

  if (liveOpen) {
    return (
      <div className="mx-auto max-w-6xl px-4 pb-16 pt-8 sm:px-6">
        <LivePage
          focusHeading
          onClose={(summary) => {
            setLiveOpen(false);
            const id = push({ role: "assistant" });
            setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, card: { type: "live", summary, lang } } : m)));
          }}
        />
      </div>
    );
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-20 border-b-2 border-line bg-paper">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Wordmark />
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                type="button"
                onClick={newChat}
                className="inline-flex min-h-11 items-center gap-2 rounded-full border-2 border-line bg-surface px-3 font-bold sm:px-4"
              >
                <Plus aria-hidden className="size-5" />
                <span className="hidden sm:inline">New chat</span>
                <span className="sr-only sm:hidden">New chat</span>
              </button>
            )}
            <LanguageSelect />
            <SettingsButton />
          </div>
        </div>
      </header>

      <main id="main" tabIndex={-1} className="mx-auto w-full max-w-3xl flex-1 outline-none px-4 pb-6 pt-6 sm:px-6">
        {messages.length === 0 ? (
          <EmptyState onSuggestion={onSuggestion} />
        ) : (
          <div role="log" aria-live={voiceOn ? "off" : "polite"} aria-label="Conversation" className="space-y-6">
            {messages.map((m) => (m.role === "user" ? <UserBubble key={m.id} m={m} /> : <AssistantMessage key={m.id} m={m} />))}
            <div ref={endRef} />
          </div>
        )}
      </main>

      {/* Composer */}
      <div className="sticky bottom-0 z-20 bg-gradient-to-t from-paper from-70% to-transparent pt-6">
        <div className="mx-auto w-full max-w-3xl px-4 pb-4 sm:px-6">
          {photoInPlay && (
            <div className="mb-3 flex flex-wrap items-center gap-2">
              {PHOTO_ACTIONS.map(({ label, intent, icon: Icon }) => (
                <button
                  key={label}
                  type="button"
                  disabled={busy}
                  onClick={() => void send(label, { intent, photo: attachment })}
                  className="inline-flex min-h-11 items-center gap-2 rounded-full border-2 border-line bg-surface px-4 font-bold hover:border-ink disabled:opacity-50"
                >
                  <Icon aria-hidden className="size-4" /> {label}
                </button>
              ))}
            </div>
          )}

          <form
            onSubmit={onSubmit}
            className="rounded-[28px] border-2 border-line bg-surface p-2 shadow-[0_10px_30px_-18px_rgb(0_0_0/0.5)] focus-within:border-ink focus-within:ring-3 focus-within:ring-focus/40"
          >
            {photoInPlay && (
              <div className="flex items-center gap-3 px-2 pb-2 pt-1">
                <img src={photoInPlay.url} alt="" className="size-14 rounded-xl border-2 border-line object-cover" />
                <p className="flex-1 text-sm text-ink-soft">
                  {attachment ? "Photo attached — ask anything about it." : "Questions will be about your last photo."}
                </p>
                <button
                  type="button"
                  onClick={() => (attachment ? setAttachment(null) : setActivePhoto(null))}
                  aria-label={attachment ? "Remove photo" : "Stop asking about the last photo"}
                  className="grid size-10 place-items-center rounded-full hover:bg-paper-2"
                >
                  <X aria-hidden className="size-5" />
                </button>
              </div>
            )}
            <div className="flex items-end gap-2">
              <button
                type="button"
                onClick={() => fileInput.current?.click()}
                aria-label="Add a photo"
                className="grid size-12 shrink-0 place-items-center rounded-full bg-paper-2 hover:bg-signal hover:text-night"
              >
                <ImagePlus aria-hidden className="size-6" />
              </button>
              <label htmlFor="composer" className="sr-only">
                Message VisionAI
              </label>
              <textarea
                id="composer"
                ref={textRef}
                rows={1}
                value={text}
                onChange={(e) => {
                  setText(e.target.value);
                  // Grow with the text up to ~5 lines; only then allow scrolling.
                  const el = e.target;
                  el.style.height = "auto";
                  el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
                  el.style.overflowY = el.scrollHeight > 160 ? "auto" : "hidden";
                }}
                onKeyDown={onKeyDown}
                maxLength={1000}
                placeholder={photoInPlay ? "Ask about this photo…" : "Message VisionAI…"}
                className="h-12 max-h-40 flex-1 resize-none overflow-hidden bg-transparent px-2 py-2.5 text-lg leading-7 text-ink outline-none placeholder:text-ink-soft focus-visible:outline-none"
              />
              <button
                type="button"
                onClick={() => setLiveOpen(true)}
                aria-label="Open live camera"
                className="hidden size-12 shrink-0 place-items-center rounded-full hover:bg-paper-2 sm:grid"
              >
                <Camera aria-hidden className="size-6" />
              </button>
              {voice.supported && (
                <button
                  type="button"
                  onClick={() => void voice.toggle()}
                  disabled={busy}
                  aria-pressed={voice.listening}
                  aria-label={voice.listening ? "Stop listening" : "Speak your message"}
                  className={`grid size-12 shrink-0 place-items-center rounded-full ${
                    voice.listening ? "pulse-ring bg-signal text-night" : "hover:bg-paper-2"
                  }`}
                >
                  {voice.listening ? <MicOff aria-hidden className="size-6" /> : <Mic aria-hidden className="size-6" />}
                </button>
              )}
              <button
                type="submit"
                disabled={busy || (!text.trim() && !attachment)}
                aria-label="Send"
                className="grid size-12 shrink-0 place-items-center rounded-full bg-ink text-paper disabled:opacity-30"
              >
                <ArrowUp aria-hidden className="size-6" />
              </button>
            </div>
          </form>
          {voice.error && <p className="mt-2 px-2 text-sm text-warn">{voice.error}</p>}
          <p className="mt-2 text-center text-xs text-ink-soft">
            VisionAI can make mistakes. Keep using your cane or guide dog for safety.
          </p>
        </div>
      </div>

      <input
        ref={fileInput}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const file = e.currentTarget.files?.[0];
          e.currentTarget.value = "";
          if (file) void pickPhoto(file);
          else afterPhoto.current = null;
        }}
      />
    </div>
  );
}
