import { useMutation } from "@tanstack/react-query";
import {
  ArrowUp,
  Banknote,
  Camera,
  CircleAlert,
  CornerUpLeft,
  CornerUpRight,
  Eye,
  FileText,
  Flag,
  Languages,
  Navigation,
  RotateCw,
  ScanSearch,
  type LucideIcon,
} from "lucide-react";
import { lazy, Suspense, type ReactNode } from "react";

import { useApp } from "../../context/AppContext";
import { api, type DetectResult } from "../../lib/api";
import { NATIVE_NAMES } from "../../lib/languages";
import { Button, CopyButton, ListenButton, Thinking } from "../ui";
import type { Card } from "./types";

const RouteMap = lazy(() => import("../RouteMap"));

function Shell({ accent, icon: Icon, title, children }: { accent: string; icon: LucideIcon; title: string; children: ReactNode }) {
  return (
    <div className="relative overflow-hidden rounded-3xl border-2 border-line bg-surface">
      <div className="flex items-center gap-2 border-b-2 border-line px-5 py-3">
        <span aria-hidden className={`grid size-8 place-items-center rounded-lg ${accent}`}>
          <Icon className="size-4" />
        </span>
        <h3 className="text-sm font-bold uppercase tracking-[0.14em] text-ink-soft">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function Actions({ text, lang }: { text: string; lang: string }) {
  return (
    <div className="mt-4 flex flex-wrap gap-3">
      <ListenButton text={text} lang={lang} />
      <CopyButton text={text} />
    </div>
  );
}

const Body = ({ children, lang }: { children: ReactNode; lang?: string }) => (
  <p lang={lang} className="whitespace-pre-line text-xl leading-relaxed">
    {children}
  </p>
);

// ---------------------------------------------------------------- answer --

function AnswerCard({ title, text, lang }: { title: string; text: string; lang: string }) {
  const icon = title === "Money" ? Banknote : Eye;
  return (
    <Shell accent="bg-signal text-night" icon={icon} title={title}>
      <Body lang={lang}>{text}</Body>
      <Actions text={text} lang={lang} />
    </Shell>
  );
}

// --------------------------------------------------------------- objects --

function Boxes({ detection }: { detection: DetectResult }) {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0">
      {detection.objects.map((o, i) => (
        <div
          key={i}
          className="absolute rounded-md border-[3px] border-signal shadow-[0_0_0_2px_#16150F]"
          style={{
            left: `${(o.x1 / detection.width) * 100}%`,
            top: `${(o.y1 / detection.height) * 100}%`,
            width: `${((o.x2 - o.x1) / detection.width) * 100}%`,
            height: `${((o.y2 - o.y1) / detection.height) * 100}%`,
          }}
        >
          <span className="absolute -left-[3px] -top-[3px] -translate-y-full rounded-t-md bg-signal px-2 py-0.5 text-xs font-bold text-night">
            {o.name}
          </span>
        </div>
      ))}
    </div>
  );
}

function ObjectsCard({ detection, image, text, lang }: { detection: DetectResult; image: string; text: string; lang: string }) {
  return (
    <Shell accent="bg-go text-white" icon={ScanSearch} title={`${detection.count} object${detection.count === 1 ? "" : "s"} found`}>
      {detection.count > 0 && (
        <div className="relative mb-4 overflow-hidden rounded-2xl bg-night p-3">
          <div className="relative">
            <img src={image} alt="" className="block h-auto w-full rounded-lg" />
            <Boxes detection={detection} />
          </div>
        </div>
      )}
      <Body lang={lang}>{text}</Body>
      {detection.objects.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-2">
          {detection.objects.map((o, i) => (
            <li key={i} className="rounded-full border-2 border-line px-3 py-1 text-sm">
              <strong>{o.name}</strong> · {o.position} ({o.clock} o’clock) · {o.proximity}
            </li>
          ))}
        </ul>
      )}
      <Actions text={text} lang={lang} />
    </Shell>
  );
}

// ------------------------------------------------------------ read text --

function TranslateButton({ text }: { text: string }) {
  const { lang, config, tell } = useApp();
  const translate = useMutation({
    mutationFn: async () => (await api.translate([text], lang)).translations[0],
    onSuccess: (t) => tell(t, { lang }),
    onError: (err) => tell(err.message),
  });
  if (lang === "en" || !config?.translation_available || !/[A-Za-z]/.test(text)) return null;
  const name = NATIVE_NAMES[lang] ?? lang;

  if (translate.data)
    return (
      <div className="mt-4 rounded-2xl bg-signal-soft p-4">
        <p className="text-sm font-bold uppercase tracking-[0.14em] text-ink-soft">In {name}</p>
        <Body lang={lang}>{translate.data}</Body>
        <div className="mt-3">
          <ListenButton text={translate.data} lang={lang} />
        </div>
      </div>
    );
  return (
    <div className="mt-4">
      <Button onClick={() => translate.mutate()} disabled={translate.isPending}>
        <Languages aria-hidden className="size-5" />
        {translate.isPending ? "Translating…" : `Translate to ${name}`}
      </Button>
      {translate.isError && <p className="mt-2 text-warn">{translate.error.message}</p>}
    </div>
  );
}

function ReadCard({ text, found, source, lang }: { text: string; found: boolean; source: string; lang: string }) {
  return (
    <Shell accent="bg-ink text-paper" icon={FileText} title="Text in the photo">
      <Body>{text}</Body>
      {source === "gemini" && <p className="mt-2 text-sm text-ink-soft">Read by AI because the text was hard to scan.</p>}
      {found && <TranslateButton text={text} />}
      <Actions text={text} lang={lang} />
    </Shell>
  );
}

function TranslationCard({ source, text, lang }: { source: string; text: string; lang: string }) {
  return (
    <Shell accent="bg-signal text-night" icon={Languages} title={`Translated to ${NATIVE_NAMES[lang] ?? lang}`}>
      <p className="text-ink-soft">“{source}”</p>
      <p lang={lang} className="display mt-2 text-3xl leading-tight">
        {text}
      </p>
      <Actions text={text} lang={lang} />
    </Shell>
  );
}

// ---------------------------------------------------------------- route --

function stepIcon(step: string): LucideIcon {
  const s = step.toLowerCase();
  if (s.startsWith("arrive")) return Flag;
  if (s.startsWith("head")) return Navigation;
  if (s.includes("roundabout")) return RotateCw;
  if (s.includes("left")) return CornerUpLeft;
  if (s.includes("right")) return CornerUpRight;
  return ArrowUp;
}

function RouteCard({ card }: { card: Extract<Card, { type: "route" }> }) {
  const { route, origin, lang } = card;
  return (
    <div className="overflow-hidden rounded-3xl border-2 border-[#16150F] bg-surface">
      <div className="tactile-dark bg-signal p-5 text-night sm:p-6">
        <p className="text-sm font-bold uppercase tracking-[0.14em]">Walking to</p>
        <h3 className="display mt-1 text-3xl">{route.destination.name.split(",")[0]}</h3>
        <p className="mt-1 text-sm opacity-80">From {origin.label}</p>
        <dl className="mt-4 flex gap-8">
          <div>
            <dt className="text-xs font-bold uppercase tracking-[0.14em]">Distance</dt>
            <dd className="display text-4xl">
              {route.distance_km}
              <span className="text-xl"> km</span>
            </dd>
          </div>
          <div>
            <dt className="text-xs font-bold uppercase tracking-[0.14em]">Walk</dt>
            <dd className="display text-4xl">
              {Math.round(route.duration_min)}
              <span className="text-xl"> min</span>
            </dd>
          </div>
        </dl>
      </div>
      <div className="space-y-5 p-5 sm:p-6">
        <ListenButton text={route.spoken} lang={lang} />
        {route.steps.length > 0 && (
          <ol lang={route.steps_lang} className="space-y-1">
            {route.steps.map((step, i) => {
              const Icon = stepIcon(route.steps_en?.[i] ?? step); // arrows come from the English instruction
              const last = i === route.steps.length - 1;
              return (
                <li key={i} className="flex gap-3 pb-2">
                  <span
                    aria-hidden
                    className={`grid size-10 shrink-0 place-items-center rounded-full border-2 ${
                      last ? "border-night bg-signal text-night" : "border-line bg-paper"
                    }`}
                  >
                    <Icon className="size-4" />
                  </span>
                  <span className="pt-1.5 text-lg">
                    <span className="sr-only">Step {i + 1}: </span>
                    {step}
                  </span>
                </li>
              );
            })}
          </ol>
        )}
        <Suspense fallback={<Thinking label="Loading map…" />}>
          <RouteMap from={origin} route={route} />
        </Suspense>
      </div>
    </div>
  );
}

// ------------------------------------------------------------ help/live --

export const SUGGESTIONS: { icon: LucideIcon; title: string; body: string; prompt: string; needsPhoto?: boolean }[] = [
  { icon: Eye, title: "Describe a photo", body: "Attach a photo and I'll tell you what's in it.", prompt: "Describe this photo", needsPhoto: true },
  { icon: FileText, title: "Read a sign or label", body: "Menus, letters, medicine, bus boards.", prompt: "Read the text", needsPhoto: true },
  { icon: Banknote, title: "Check money", body: "Which note is this, and how much in total?", prompt: "How much money is this?", needsPhoto: true },
  { icon: Navigation, title: "Walking directions", body: "“Take me to the railway station”", prompt: "Take me to " },
  { icon: Camera, title: "Live camera", body: "Hear what's around you, with warnings.", prompt: "Open live camera" },
  { icon: Languages, title: "Translate", body: "“Translate emergency exit”", prompt: "Translate " },
];

function HelpCard() {
  return (
    <Shell accent="bg-signal text-night" icon={Eye} title="What I can do">
      <ul className="grid gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map(({ icon: Icon, title, body }) => (
          <li key={title} className="flex gap-3 rounded-2xl bg-paper p-3">
            <Icon aria-hidden className="mt-1 size-5 shrink-0" />
            <span>
              <strong className="block">{title}</strong>
              <span className="text-sm text-ink-soft">{body}</span>
            </span>
          </li>
        ))}
      </ul>
    </Shell>
  );
}

function LiveCard({ summary, lang }: { summary: string; lang: string }) {
  return (
    <Shell accent="bg-night text-signal" icon={Camera} title="Live camera session">
      <p className="text-ink-soft">The last thing I saw:</p>
      <Body lang={lang}>{summary || "Nothing in view."}</Body>
    </Shell>
  );
}

function ErrorCard({ message }: { message: string }) {
  return (
    <div role="alert" className="flex gap-3 rounded-3xl border-2 border-warn bg-warn-soft p-5">
      <CircleAlert aria-hidden className="mt-0.5 size-6 shrink-0 text-warn" />
      <p className="text-lg">{message}</p>
    </div>
  );
}

export function CardView({ card }: { card: Card }) {
  switch (card.type) {
    case "answer":
      return <AnswerCard title={card.title} text={card.text} lang={card.lang} />;
    case "objects":
      return <ObjectsCard detection={card.detection} image={card.image} text={card.text} lang={card.lang} />;
    case "read":
      return <ReadCard text={card.text} found={card.found} source={card.source} lang={card.lang} />;
    case "translation":
      return <TranslationCard source={card.source} text={card.text} lang={card.lang} />;
    case "route":
      return <RouteCard card={card} />;
    case "live":
      return <LiveCard summary={card.summary} lang={card.lang} />;
    case "help":
      return <HelpCard />;
    case "error":
      return <ErrorCard message={card.message} />;
  }
}
