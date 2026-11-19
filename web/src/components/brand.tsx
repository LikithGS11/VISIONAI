import { useApp } from "../context/AppContext";
import { NATIVE_NAMES } from "../lib/languages";

export function BrandMark({ className = "size-9" }: { className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 36 36" className={className}>
      <rect x="1" y="1" width="34" height="34" rx="9" fill="#FFC800" stroke="#16150F" strokeWidth="2" />
      <circle cx="18" cy="18" r="8.5" fill="#16150F" />
      <circle cx="21" cy="15" r="2.6" fill="#FFC800" />
    </svg>
  );
}

export function Wordmark({ href = "#/" }: { href?: string }) {
  return (
    <a href={href} className="flex shrink-0 items-center gap-2.5">
      <BrandMark />
      <span className="display text-xl sm:text-2xl">VisionAI</span>
    </a>
  );
}

export function LanguageSelect() {
  const { config, lang, setLang } = useApp();
  const codes = Object.keys(config?.languages ?? { en: "English" });
  return (
    <label className="relative">
      <span className="sr-only">Language</span>
      <select
        value={lang}
        onChange={(e) => setLang(e.target.value)}
        className="min-h-11 max-w-[7.5rem] appearance-none rounded-full border-2 border-line bg-surface py-1 pl-4 pr-8 font-bold text-ink sm:max-w-none sm:pr-9"
      >
        {codes.map((code) => (
          <option key={code} value={code}>
            {NATIVE_NAMES[code] ?? config?.languages[code] ?? code}
          </option>
        ))}
      </select>
      <span aria-hidden className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-xs">
        ▼
      </span>
    </label>
  );
}
