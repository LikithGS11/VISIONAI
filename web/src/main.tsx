import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import { AppProvider } from "./context/AppContext";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

// Installable app + offline app shell (production builds only; dev uses Vite's live reload).
if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      /* app still works without it */
    });
  });
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AppProvider>
        <App />
      </AppProvider>
    </QueryClientProvider>
  </StrictMode>,
);
