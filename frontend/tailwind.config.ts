import type { Config } from "tailwindcss";
import daisyui from "daisyui";

export default {
  content: ["./app/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        heading: ["Inter", "sans-serif"],
        sans: ["Inter", "sans-serif"],
        sketch: ["Inter", "sans-serif"],
      },
      boxShadow: {
        'brutal': '0 3px 4px -1px rgba(0, 0, 0, 0.10)',
        'brutal-sm': '0 1px 2px rgba(0, 0, 0, 0.06)',
        'brutal-lg': '0 8px 20px -2px rgba(29,33,41,0.10), 0 32px 48px -12px rgba(29,33,41,0.12)',
        'brutal-hover': '0 8px 20px -2px rgba(29,33,41,0.10), 0 32px 48px -12px rgba(29,33,41,0.12)',
      },
    },
  },
  plugins: [daisyui],
  daisyui: {
    themes: [
      {
        doodle: {
          "primary": "#222222",
          "primary-content": "#f5f5f5",
          "secondary": "#155dfc",
          "secondary-content": "#ffffff",
          "accent": "#00a63e",
          "accent-content": "#ffffff",
          "neutral": "#444444",
          "neutral-content": "#f5f5f5",
          "base-100": "#f5f5f5",
          "base-200": "#eeeeee",
          "base-300": "#cccccc",
          "base-content": "#222222",
          "info": "#155dfc",
          "info-content": "#ffffff",
          "success": "#00a63e",
          "success-content": "#ffffff",
          "warning": "#d08700",
          "warning-content": "#ffffff",
          "error": "#e7000b",
          "error-content": "#ffffff",
        },
      },
      {
        "doodle-dark": {
          "primary": "#f4f6ff",
          "primary-content": "#131b2b",
          "secondary": "#155dfc",
          "secondary-content": "#ffffff",
          "accent": "#4ade80",
          "accent-content": "#131b2b",
          "neutral": "#2c3950",
          "neutral-content": "#f4f6ff",
          "base-100": "#131b2b",
          "base-200": "#222d41",
          "base-300": "#2c3950",
          "base-content": "#f4f6ff",
          "info": "#155dfc",
          "info-content": "#ffffff",
          "success": "#4ade80",
          "success-content": "#131b2b",
          "warning": "#facc15",
          "warning-content": "#131b2b",
          "error": "#f87171",
          "error-content": "#131b2b",
        },
      },
    ],
    darkTheme: "doodle-dark",
  },
} satisfies Config;
