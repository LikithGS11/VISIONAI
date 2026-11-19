import { useApp } from "../context/AppContext";
import type { DirectionStyle } from "../lib/api";

const OPTIONS: { value: DirectionStyle; label: string; example: string }[] = [
  { value: "sides", label: "Left / right", example: "“Chair on your left”" },
  { value: "clock", label: "Clock face", example: "“Chair at 10 o'clock”" },
];

/** How VisionAI describes where things are. Clock directions are taught in O&M training. */
export function DirectionStyleToggle({ compact = false }: { compact?: boolean }) {
  const { directionStyle, setDirectionStyle } = useApp();
  return (
    <fieldset>
      <legend className={compact ? "sr-only" : "mb-2 text-sm font-bold uppercase tracking-[0.14em] text-ink-soft"}>
        Say directions as
      </legend>
      <div className="inline-flex rounded-full border-2 border-line bg-surface p-1">
        {OPTIONS.map(({ value, label, example }) => {
          const active = value === directionStyle;
          return (
            <label
              key={value}
              className={`flex min-h-11 cursor-pointer items-center rounded-full px-4 font-bold transition-colors has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-focus ${
                active ? "bg-ink text-paper" : "text-ink-soft hover:text-ink"
              }`}
            >
              <input
                type="radio"
                name="direction-style"
                value={value}
                checked={active}
                onChange={() => setDirectionStyle(value)}
                className="sr-only"
              />
              {label}
              <span className="sr-only">, for example {example}</span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
