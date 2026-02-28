/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        saffron:  { DEFAULT: '#FF671F', light: '#FF8C47', dark: '#CC4E0F' },
        indgreen: { DEFAULT: '#046A38', light: '#058A48', dark: '#034D28' },
        navy:     { DEFAULT: '#0F2C5C', light: '#1A4080', dark: '#091E40' },
        gold:     { DEFAULT: '#E8B84B', light: '#F0CA70', dark: '#C99830' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-up':   'slideUp 0.4s ease-out',
        'fade-in':    'fadeIn 0.5s ease-out',
      },
      keyframes: {
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
