import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: "#0B1F33",
          50: "#E8EEF3",
          100: "#C5D3E0",
          200: "#9BB0C4",
          300: "#718DA8",
          400: "#4A6B8A",
          500: "#2E4F6E",
          600: "#1A3854",
          700: "#0B1F33",
          800: "#081826",
          900: "#05101A",
        },
        surface: "#F7F8FA",
        accent: {
          DEFAULT: "#0F766E",
          light: "#14B8A6",
          dark: "#0D5F58",
        },
      },
      fontFamily: {
        serif: ["var(--font-source-serif)", "Georgia", "serif"],
        sans: ["var(--font-ibm-plex)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 1px 3px 0 rgb(11 31 51 / 0.06), 0 1px 2px -1px rgb(11 31 51 / 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
