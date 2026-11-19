// Turns a chat message (+ whether a photo is in play) into what VisionAI should do.
// Plain keyword rules: instant, offline and predictable. Anything unrecognised goes to
// the AI as a question, so nothing a user types is ever "wrong".

export type Intent =
  | { kind: "describe" }
  | { kind: "read" }
  | { kind: "objects" }
  | { kind: "currency" }
  | { kind: "assist" }
  | { kind: "ask"; question: string }
  | { kind: "route"; destination: string }
  | { kind: "translate"; text: string }
  | { kind: "live" }
  | { kind: "help" }
  | { kind: "chat"; message: string };

// "take me to X", "how do I get to X", "directions to X", "navigate X"…
const ROUTE_TO =
  /^(?:please\s+)?(?:take me|guide me|walk me|how (?:do|can) i (?:get|go|walk)|(?:i want to |i need to |let'?s )?go|walking route|route|directions?|navigate)\s+(?:to|till|towards?|for)\s+(.{2,})$/i;
const ROUTE_BARE = /^(?:please\s+)?(?:navigate|directions|route)\s+(.{2,})$/i;
const TRANSLATE = /^translate\s*(?:this|that)?\s*:?\s+(.+)$/i;

export function detectIntent(raw: string, hasPhoto: boolean): Intent {
  const text = raw.trim();
  const t = text.toLowerCase().replace(/[?.!]+$/, "");

  if (!t) return hasPhoto ? { kind: "describe" } : { kind: "help" };
  // Only an explicit request for help shows the feature card; greetings and small talk go to the AI.
  if (/^(help|what can you do|what all can you do|how (?:do|does) (?:this|it|you) work)\b/.test(t)) return { kind: "help" };
  if (/\b(live camera|start (?:the )?camera|open (?:the )?camera|live mode|what'?s around me)\b/.test(t)) return { kind: "live" };

  const plain = text.replace(/[?.!]+$/, "");
  const route = ROUTE_TO.exec(plain) ?? ROUTE_BARE.exec(plain);
  if (route) return { kind: "route", destination: route[1].trim() };

  const translate = TRANSLATE.exec(text);
  if (translate) return { kind: "translate", text: translate[1].trim() };

  if (hasPhoto) {
    if (/^(describe|what(?:'s| is) (?:this|in (?:this|the) (?:photo|picture|image))|what do you see)\b/.test(t)) return { kind: "describe" };
    if (/\b(money|currency|notes?|rupees?|coins?|cash|₹|rs\.?)\b/.test(t)) return { kind: "currency" };
    if (/\b(read|text|written|what does (?:it|this) say|sign|label)\b/.test(t)) return { kind: "read" };
    if (/\b(objects?|obstacles?|in front|find|detect|anything (?:near|close))\b/.test(t)) return { kind: "objects" };
    if (/\b(help me|guide|what should i|how (?:do|should) i use)\b/.test(t)) return { kind: "assist" };
    return { kind: "ask", question: text };
  }
  return { kind: "chat", message: text };
}
