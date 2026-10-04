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
        sentra: {
          50: "#eef9ff",
          100: "#d8f0ff",
          200: "#bae4ff",
          300: "#8bd2ff",
          400: "#54b6ff",
          500: "#2b96ff",
          600: "#1377f6",
          700: "#0d5edb",
          800: "#114cae",
          900: "#144288",
          950: "#0b234b",
        },
        nvidia: {
          green: "#76B900",
          dark: "#1A1A1A",
        }
      },
    },
  },
  plugins: [],
};
export default config;
