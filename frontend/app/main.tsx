import "./i18n";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles/globals.css";

async function enableMocking() {
  if (import.meta.env.MODE !== "development") {
    return;
  }

  const { worker } = await import("~/mocks/browser");

  // `worker.start()` returns a Promise that resolves
  // once the Service Worker is up and running.
  return worker.start({
    onUnhandledRequest: "bypass",
  });
}

const rootElement = document.getElementById("root")!;
const root = createRoot(rootElement);

enableMocking().then(() => {
  root.render(
    <StrictMode>
      <App />
    </StrictMode>
  );
});
