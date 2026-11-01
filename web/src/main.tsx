import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles/tokens.css";

/**
 * Dev only: start the MSW worker so the app shell runs against realistic
 * mock data with no server (P1 acceptance). Production builds never import it.
 */
async function enableMocks(): Promise<void> {
  if (!import.meta.env.DEV) return;
  const { worker } = await import("./mocks/browser");
  await worker.start({ quiet: true, onUnhandledRequest: "bypass" });
}

enableMocks().then(() => {
  createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
});
