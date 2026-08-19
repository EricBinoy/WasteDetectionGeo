/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#05070c",
        line: "rgba(148,163,196,.16)",
        line2: "rgba(148,163,196,.3)",
        gold: "#D4AF37",
        cyan: "#0ABDE3",
        accent: "#3B82F6",
        fg: "#ECF1FA",
        muted: "#8B9AB6",
        dim: "#5B6A85",
      },
      fontFamily: {
        serif: ["var(--font-fraunces)", "serif"],
        sans: ["var(--font-space-grotesk)", "sans-serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
      },
    },
  },
  plugins: [],
};
