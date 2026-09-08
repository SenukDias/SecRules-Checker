/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        rulescope: {
          bg: "#12151c",
          surface: "#1b1f29",
          surfaceAlt: "#232838",
          border: "#2c3244",
          orange: "#e8620c",
          orangeLight: "#ff8a3d",
          green: "#1f9d55",
          greenLight: "#3ecf7e",
          white: "#f5f7fa",
          muted: "#8b93a7",
        },
      },
    },
  },
  plugins: [],
};
