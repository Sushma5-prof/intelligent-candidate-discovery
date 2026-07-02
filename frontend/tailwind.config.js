/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#0D1117",
        panel: "#141A22",
        panel2: "#1B2230",
        border: "#262E3A",
        ink: "#E6EDF3",
        muted: "#7D8898",
        signal: "#39D6C0",
        velocity: "#F2A65A",
        penalty: "#F2545B",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui"],
      },
      keyframes: {
        pulse_ring: {
          "0%": { transform: "scale(0.9)", opacity: "0.8" },
          "80%": { transform: "scale(1.6)", opacity: "0" },
          "100%": { transform: "scale(1.6)", opacity: "0" },
        },
        scan: {
          "0%": { backgroundPosition: "0% 0%" },
          "100%": { backgroundPosition: "0% 200%" },
        },
      },
      animation: {
        pulse_ring: "pulse_ring 1.6s cubic-bezier(0.2,0.6,0.4,1) infinite",
        scan: "scan 3s linear infinite",
      },
    },
  },
  plugins: [],
};
