/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,html}",
  ],
  theme: {
    extend: {
      colors: {
        eco: {
          primary: '#22c55e',
          secondary: '#16a34a',
          light: '#dcfce7',
          dark: '#15803d'
        },
        grade: {
          A: '#22c55e',
          B: '#84cc16',
          C: '#eab308',
          D: '#f97316',
          E: '#ef4444'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif']
      }
    },
  },
  plugins: [],
}
