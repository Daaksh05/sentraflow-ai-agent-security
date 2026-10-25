import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        nvidia: {
          green: "#76B900",
          bright: "#8ce000",
          hover: "#66a000",
          muted: "rgba(118, 185, 0, 0.15)",
          border: "#263512",
          dark: "#0b0e07",
          card: "#0d1117",
        },
        cyber: {
          bg: "#050608",
          card: "#0c0e14",
          surface: "#12161f",
          border: "#1e2638",
          hover: "#2a364f",
          muted: "#64748b",
        },
      },
      boxShadow: {
        "nvidia-sm": "0 0 10px rgba(118, 185, 0, 0.25)",
        "nvidia-glow": "0 0 25px rgba(118, 185, 0, 0.35)",
        "nvidia-lg": "0 0 45px rgba(118, 185, 0, 0.25)",
        "red-glow": "0 0 25px rgba(239, 68, 68, 0.35)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
      },
      keyframes: {
        pulseSlow: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" },
        },
      },
      animation: {
        "pulse-slow": "pulseSlow 3s ease-in-out infinite",
        float: "float 4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;
