import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      colors: {
        primary: {
          50: "#e8edf4",
          100: "#c5d1e3",
          200: "#9eb3d0",
          300: "#7795bd",
          400: "#597eaf",
          500: "#3b67a1",
          600: "#1E3A5F",
          700: "#1a3354",
          800: "#152b48",
          900: "#0f1f34",
          950: "#0a1523",
        },
        accent: {
          50: "#e0f5fd",
          100: "#b3e8fa",
          200: "#80daf7",
          300: "#4dccf3",
          400: "#26c2f0",
          500: "#00AEEF",
          600: "#009cdb",
          700: "#0087c1",
          800: "#0073a7",
          900: "#00547c",
        },
        va: {
          dark: "#1E3A5F",
          light: "#00AEEF",
          bg: "#F3F5F7",
          card: "#FFFFFF",
          heading: "#2A2A2A",
          body: "#494949",
          border: "#E2E8F0",
          muted: "#94A3B8",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
