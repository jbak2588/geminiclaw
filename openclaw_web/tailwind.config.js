/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0B0D17",
        surface: "rgba(255, 255, 255, 0.05)",
        primary: "#8B5CF6",
        secondary: "#22D3EE",
        accent: "#F43F5E",
      },
      backdropBlur: {
        xs: "2px",
      }
    },
  },
  plugins: [],
}
