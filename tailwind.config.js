/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./*.html", "./*.js"],
  theme: {
    extend: {
      fontFamily: { sans: ['"Plus Jakarta Sans"', 'sans-serif'] },
      colors: {
        palm: { 50: '#f2f7ec', 100: '#e1efd3', 500: '#639922', 700: '#3B6D11', 800: '#2d530d' },
        s1: '#e8f5e9', s1b: '#4caf50', s2: '#e3f2fd', s2b: '#2196f3',
        s3: '#f3e5f5', s3b: '#9c27b0', s4: '#fff3e0', s4b: '#ff9800',
        s5: '#e0f2f1', s5b: '#009688',
      }
    }
  },
  plugins: [],
}
