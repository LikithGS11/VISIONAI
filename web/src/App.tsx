import { useEffect, useState } from "react";

import { SpeakingBar } from "./components/ui";
import ChatPage from "./pages/ChatPage";
import LandingPage from "./pages/LandingPage";

type Route = { page: "landing" } | { page: "chat"; live: boolean };

function parse(): Route {
  const hash = location.hash.replace(/^#\/?/, "");
  if (hash === "chat/live" || hash === "live") return { page: "chat", live: true };
  // Old links (#/photo, #/directions, #/home) all lead to the chat now.
  if (["chat", "photo", "directions", "home"].includes(hash)) return { page: "chat", live: false };
  return { page: "landing" };
}

export default function App() {
  const [route, setRoute] = useState(parse);
  useEffect(() => {
    const onChange = () => {
      const next = parse();
      // In-page anchors on the landing page (#how, #features) aren't routes — let the browser scroll.
      if (next.page === "landing" && /^#[a-z]+$/.test(location.hash)) return;
      setRoute(next);
      window.scrollTo({ top: 0 });
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  useEffect(() => {
    document.title = route.page === "chat" ? "VisionAI — Chat" : "VisionAI — See the world, out loud";
  }, [route]);

  return (
    <>
      <a
        href="#main"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main")?.focus();
        }}
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-signal focus:p-3 focus:font-bold focus:text-night"
      >
        Skip to main content
      </a>
      {route.page === "landing" ? <LandingPage /> : <ChatPage key={String(route.live)} openLiveOnStart={route.live} />}
      <SpeakingBar />
    </>
  );
}
