import lineClamp from '@tailwindcss/line-clamp'

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      container: { center: true, padding: '1rem' },
      colors: {
        brand: {
          50: '#F0FAF7',
          100: '#E6F3EF',
          200: '#BFE1D7',
          300: '#99CFBF',
          400: '#33A583',
          500: '#1F9A78',
          600: '#008060', // Shopify green
          700: '#00664D',
          800: '#004D3A',
          900: '#003D2F',
        },
      },
      borderRadius: {
        xl: '0.75rem',
      },
    },
  },
  // Do not invoke plugins; pass the function reference
  plugins: [lineClamp],
}
