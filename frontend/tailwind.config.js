/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        parchment: {
          50:  '#fdfaf3',
          100: '#f9f1dc',
          200: '#f0ddb0',
          300: '#e5c47e',
          400: '#d9a84e',
          500: '#cc8e30',
          600: '#b07225',
          700: '#8d5520',
          800: '#714221',
          900: '#5d3620',
        },
        ink: {
          DEFAULT: '#1a1208',
          50:  '#f6f3ee',
          100: '#e8e0d0',
          200: '#d0c0a0',
          300: '#b09870',
          400: '#8a7050',
          500: '#6b5538',
          600: '#544228',
          700: '#3d3018',
          800: '#2a200e',
          900: '#1a1208',
        },
        library: {
          green:  '#2d5016',
          gold:   '#c8972a',
          red:    '#8b1a1a',
          cream:  '#fdf6e3',
        }
      },
      fontFamily: {
        display: ['Georgia', 'Times New Roman', 'serif'],
        body:    ['Palatino Linotype', 'Palatino', 'Book Antiqua', 'Georgia', 'serif'],
        mono:    ['Courier New', 'monospace'],
      },
      backgroundImage: {
        'paper': "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.08'/%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [],
};
