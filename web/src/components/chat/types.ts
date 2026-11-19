import type { DetectResult, RouteResult } from "../../lib/api";
import type { Origin } from "../../lib/location";

export type Card =
  | { type: "answer"; title: string; text: string; lang: string }
  | { type: "objects"; detection: DetectResult; image: string; text: string; lang: string }
  | { type: "read"; text: string; found: boolean; source: string; lang: string }
  | { type: "translation"; source: string; text: string; lang: string }
  | { type: "route"; route: RouteResult; origin: Origin; lang: string }
  | { type: "live"; summary: string; lang: string }
  | { type: "help" }
  | { type: "error"; message: string };

export interface Message {
  id: number;
  role: "user" | "assistant";
  time: string;
  text?: string;
  /** Object URL of a photo the user sent. */
  image?: string;
  card?: Card;
  /** Assistant is still working on this one. */
  pending?: string;
}

/** What should be read aloud for a card (if anything). */
export function spokenText(card: Card): { text: string; lang: string } | null {
  switch (card.type) {
    case "answer":
    case "objects":
    case "read":
    case "translation":
      return { text: card.text, lang: card.lang };
    case "live":
      return card.summary ? { text: card.summary, lang: card.lang } : null;
    case "route":
      return { text: card.route.spoken, lang: card.lang };
    case "error":
      return { text: card.message, lang: "en" };
    case "help":
      return {
        text: "Hi, I'm VisionAI. Send me a photo and ask anything about it, or ask me for walking directions, or open the live camera.",
        lang: "en",
      };
  }
}
