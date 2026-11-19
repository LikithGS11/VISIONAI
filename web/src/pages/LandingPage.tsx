import { ArrowRight, Camera, Ear, MessageSquareText, ShieldCheck, Volume2 } from "lucide-react";

import { BrandMark, Wordmark } from "../components/brand";
import { SUGGESTIONS } from "../components/chat/cards";
import { NATIVE_NAMES } from "../lib/languages";

/** A static preview of a real conversation, so people see the product before opening it. */
function ChatPreview() {
  return (
    <div aria-hidden className="relative">
      <div className="tactile-light absolute -inset-4 -z-10 rounded-[40px] sm:-inset-6" />
      <div className="rotate-1 rounded-[32px] border-2 border-[#16150F] bg-surface p-4 shadow-[0_30px_60px_-30px_rgb(0_0_0/0.55)] sm:p-5">
        <div className="mb-4 flex items-center gap-2 border-b-2 border-line pb-3">
          <BrandMark className="size-7" />
          <span className="display text-lg">VisionAI</span>
          <span className="ml-auto rounded-full bg-paper-2 px-3 py-1 text-xs font-bold">ಕನ್ನಡ</span>
        </div>
        <div className="space-y-3">
          <div className="flex justify-end">
            <div className="w-40 space-y-2">
              <img src="/sample.jpg" alt="" className="h-28 w-full rounded-2xl object-cover" />
              <p className="rounded-2xl rounded-br-md bg-ink px-3 py-2 text-sm text-paper">What's in front of me?</p>
            </div>
          </div>
          <div className="flex gap-2">
            <BrandMark className="size-7 shrink-0" />
            <div className="flex-1 overflow-hidden rounded-2xl border-2 border-line">
              <p className="flex items-center gap-2 border-b-2 border-line px-3 py-2 text-[11px] font-bold uppercase tracking-[0.14em] text-ink-soft">
                <span className="size-2 rounded-full bg-go" /> 3 objects found
              </p>
              <p className="px-3 py-2 text-sm">Person on your left, close. Person ahead, close.</p>
              <div className="flex gap-2 px-3 pb-3">
                <span className="rounded-lg bg-signal px-2.5 py-1 text-xs font-bold text-night">▶ Listen</span>
                <span className="rounded-lg border-2 border-line px-2.5 py-0.5 text-xs font-bold">Copy</span>
              </div>
            </div>
          </div>
          <div className="flex justify-end">
            <p className="rounded-2xl rounded-br-md bg-ink px-3 py-2 text-sm text-paper">Take me to Cubbon Park</p>
          </div>
          <div className="flex gap-2">
            <BrandMark className="size-7 shrink-0" />
            <div className="tactile-dark flex-1 rounded-2xl bg-signal px-3 py-3 text-night">
              <p className="text-[11px] font-bold uppercase tracking-[0.14em]">Walking to</p>
              <p className="display text-xl">Cubbon Park</p>
              <p className="display text-2xl">
                1.2<span className="text-sm"> km</span> · 15<span className="text-sm"> min</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const STEPS = [
  { icon: Camera, title: "Snap or speak", body: "Take a photo, type, or just tap the microphone and talk." },
  { icon: MessageSquareText, title: "Ask anything", body: "“What does this say?” “Which note is this?” “Take me home.”" },
  { icon: Volume2, title: "Hear the answer", body: "Clear spoken replies in your language, at your speed." },
];

export default function LandingPage() {
  return (
    <div className="overflow-x-hidden">
      <header className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <Wordmark />
        <nav aria-label="Page" className="hidden items-center gap-6 font-bold text-ink-soft md:flex">
          <a href="#how" className="hover:text-ink">
            How it works
          </a>
          <a href="#features" className="hover:text-ink">
            Features
          </a>
          <a href="#languages" className="hover:text-ink">
            Languages
          </a>
        </nav>
        <a href="#/chat" className="keycap keycap-signal whitespace-nowrap">
          <span className="sm:hidden">Open</span>
          <span className="hidden sm:inline">Open VisionAI</span>
          <ArrowRight aria-hidden className="size-5" />
        </a>
      </header>

      <main id="main" tabIndex={-1} className="outline-none">
        {/* Hero */}
        <section className="mx-auto grid max-w-6xl items-center gap-14 px-4 pb-20 pt-10 sm:px-6 lg:grid-cols-[1.15fr_1fr] lg:pt-16">
          <div>
            <p className="mb-5 inline-flex items-center gap-2 rounded-full border-2 border-line bg-surface px-4 py-1.5 text-sm font-bold">
              <Ear aria-hidden className="size-4" /> Built for blind & low-vision people
            </p>
            <h1 className="display text-[3.2rem] sm:text-7xl">
              See the world,{" "}
              <span className="inline-block -rotate-2 rounded-2xl border-2 border-[#16150F] bg-signal px-3 pb-1 text-night shadow-[0_6px_0_#16150F]">
                out loud.
              </span>
            </h1>
            <p className="mt-6 max-w-xl text-xl text-ink-soft">
              Just chat. Send a photo or speak a question — VisionAI describes scenes, reads signs, checks money, warns
              you about obstacles and walks you to where you're going. In 8 Indian languages.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <a href="#/chat" className="keycap keycap-signal min-h-16 px-8 text-xl">
                Start chatting <ArrowRight aria-hidden className="size-6" />
              </a>
              <a href="#/chat/live" className="keycap min-h-16 px-8 text-xl">
                <Camera aria-hidden className="size-6" /> Live camera
              </a>
            </div>
            <p className="mt-6 text-sm text-ink-soft">Works with TalkBack, NVDA & VoiceOver · Offline translation · Free</p>
          </div>
          <ChatPreview />
        </section>

        {/* How it works */}
        <section id="how" aria-labelledby="how-title" className="border-y-2 border-line bg-surface">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
            <h2 id="how-title" className="display text-4xl sm:text-5xl">
              As easy as a conversation.
            </h2>
            <ol className="mt-10 grid gap-6 md:grid-cols-3">
              {STEPS.map(({ icon: Icon, title, body }, i) => (
                <li key={title} className="relative rounded-[28px] border-2 border-line bg-paper p-6">
                  <span aria-hidden className="display absolute right-6 top-4 text-6xl text-line">
                    {i + 1}
                  </span>
                  <span aria-hidden className="grid size-14 place-items-center rounded-2xl bg-signal text-night">
                    <Icon className="size-7" />
                  </span>
                  <h3 className="mt-5 text-2xl font-bold">{title}</h3>
                  <p className="mt-2 text-lg text-ink-soft">{body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Features */}
        <section id="features" aria-labelledby="features-title" className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <h2 id="features-title" className="display text-4xl sm:text-5xl">
            One chat. Everything you need.
          </h2>
          <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {SUGGESTIONS.map(({ icon: Icon, title, body }, i) => (
              <li
                key={title}
                className={`rounded-[28px] border-2 p-6 ${
                  i === 0 ? "border-[#16150F] bg-signal text-night" : i === 4 ? "border-night bg-night text-night-ink" : "border-line bg-surface"
                }`}
              >
                <Icon aria-hidden className="size-8" />
                <h3 className="mt-4 text-2xl font-bold">{title}</h3>
                <p className="mt-1 text-lg opacity-80">{body}</p>
              </li>
            ))}
          </ul>
        </section>

        {/* Languages */}
        <section id="languages" aria-labelledby="lang-title" className="bg-night py-16 text-night-ink">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <h2 id="lang-title" className="display text-4xl text-signal sm:text-5xl">
              Speaks your language.
            </h2>
            <ul className="mt-8 flex flex-wrap gap-3">
              {Object.entries(NATIVE_NAMES).map(([code, name]) => (
                <li key={code} lang={code} className="rounded-full border-2 border-night-ink/25 px-5 py-2 text-2xl font-bold">
                  {name}
                </li>
              ))}
            </ul>
            <p className="mt-6 max-w-2xl text-lg text-night-ink/75">
              Warnings and object names are instant and offline. Signs and walking directions are translated on your own
              server with AI4Bharat's IndicTrans2 — nothing leaves your device for translation.
            </p>
          </div>
        </section>

        {/* Safety + CTA */}
        <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <div className="grid gap-6 lg:grid-cols-[1fr_1.3fr]">
            <div className="flex gap-4 rounded-[28px] border-2 border-line p-6">
              <ShieldCheck aria-hidden className="size-8 shrink-0" />
              <div>
                <h2 className="text-xl font-bold">A helper, not a replacement</h2>
                <p className="mt-1 text-ink-soft">
                  AI can miss things. Keep using your cane, guide dog or a trusted person for crossings and anything
                  safety-critical.
                </p>
              </div>
            </div>
            <div className="tactile-dark flex flex-col items-start justify-between gap-6 rounded-[28px] border-2 border-[#16150F] bg-signal p-8 text-night sm:flex-row sm:items-center">
              <p className="display text-4xl">Ready when you are.</p>
              <a href="#/chat" className="keycap keycap-night min-h-16 px-8 text-xl">
                Start chatting <ArrowRight aria-hidden className="size-6" />
              </a>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t-2 border-line">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-8 text-ink-soft sm:px-6">
          <Wordmark />
          <p>Made by Likith G S · Dayana G S · Manisha Koli · Ananya V</p>
        </div>
      </footer>
    </div>
  );
}
