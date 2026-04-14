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
        background: "#0f0f13",
        surface: "#1a1a22",
        surfaceHover: "#22222e",
        border: "#2a2a36",
        accent: {
          purple: "#7c5cbf",
          orange: "#f97316",
        },
        text: {
          primary: "#f0f0f5",
          secondary: "#8888aa",
          muted: "#555568",
        },
      },
    },
  },
  plugins: [],
};
export default config;
