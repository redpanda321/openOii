import { useEffect } from "react";
import { useAuthStore } from "~/stores/authStore";
import { useThemeStore } from "~/stores/themeStore";
import { useSettingsStore } from "~/stores/settingsStore";
import { LocaleEnum } from "~/i18n";

// Theme mapping: Hanggent uses "light"/"dark", openOii uses "doodle"/"doodle-dark"
const THEME_MAP: Record<string, "doodle" | "doodle-dark"> = {
  light: "doodle",
  dark: "doodle-dark",
};

interface HanggentMessage {
  type: string;
  version: number;
  [key: string]: unknown;
}

export function useParentMessages() {
  useEffect(() => {
    // Only listen when running inside an iframe
    if (window === window.parent) return;

    function handleMessage(event: MessageEvent) {
      const data = event.data as HanggentMessage;
      if (!data || typeof data.type !== "string" || !data.type.startsWith("hanggent:")) return;

      switch (data.type) {
        case "hanggent:auth": {
          const token = data.token as string;
          const userId = data.userId as number;
          if (token && typeof userId === "number") {
            useAuthStore.getState().setAuth(token, userId);
          }
          break;
        }
        case "hanggent:theme": {
          const theme = data.theme as string;
          const mapped = THEME_MAP[theme];
          if (mapped) {
            useThemeStore.getState().setTheme(mapped);
          }
          break;
        }
        case "hanggent:locale": {
          const locale = data.locale as string;
          const validLocales = Object.values(LocaleEnum) as string[];
          if (validLocales.includes(locale)) {
            useSettingsStore.getState().setLanguage(locale as LocaleEnum);
          }
          break;
        }
        case "hanggent:providers": {
          // Store providers for future use (comic generation, etc.)
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (window as any).__hanggent_providers = data.providers;
          break;
        }
      }
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);
}
