// Small hand-drawn-style illustrations for the mode tiles. Decorative only.

export function PhotoArt({ className = "" }: { className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 200 160" fill="none" className={className}>
      <g stroke="#16150F" strokeWidth="7" strokeLinecap="round">
        <path d="M20 46V30a10 10 0 0 1 10-10h16" />
        <path d="M154 20h16a10 10 0 0 1 10 10v16" />
        <path d="M180 114v16a10 10 0 0 1-10 10h-16" />
        <path d="M46 140H30a10 10 0 0 1-10-10v-16" />
      </g>
      <rect x="52" y="48" width="96" height="66" rx="14" fill="#16150F" />
      <circle cx="100" cy="81" r="22" fill="#FFC800" />
      <circle cx="100" cy="81" r="11" fill="#16150F" />
      <circle cx="106" cy="75" r="4" fill="#FFC800" />
      <rect x="64" y="38" width="26" height="14" rx="5" fill="#16150F" />
    </svg>
  );
}

export function LiveArt({ className = "" }: { className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 200 160" fill="none" className={className}>
      <g stroke="#FFC800" strokeLinecap="round">
        <path d="M60 128a40 40 0 0 1 80 0" strokeWidth="7" />
        <path d="M36 128a64 64 0 0 1 128 0" strokeWidth="6" opacity=".65" />
        <path d="M12 128a88 88 0 0 1 176 0" strokeWidth="5" opacity=".35" />
      </g>
      <circle cx="100" cy="128" r="12" fill="#FFC800" />
      <circle cx="136" cy="70" r="7" fill="#F4F0E6" />
      <circle cx="58" cy="88" r="5" fill="#F4F0E6" opacity=".8" />
    </svg>
  );
}

export function RouteArt({ className = "" }: { className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 200 160" fill="none" className={className}>
      <path
        d="M30 132c30 0 26-46 62-46s30-40 70-48"
        stroke="currentColor"
        strokeWidth="7"
        strokeLinecap="round"
        strokeDasharray="2 16"
      />
      <circle cx="30" cy="132" r="13" fill="#16150F" stroke="#FFC800" strokeWidth="6" />
      <path d="M162 16c-13 0-22 9-22 21 0 16 22 37 22 37s22-21 22-37c0-12-9-21-22-21Z" fill="#FFC800" stroke="#16150F" strokeWidth="5" />
      <circle cx="162" cy="37" r="7" fill="#16150F" />
    </svg>
  );
}
