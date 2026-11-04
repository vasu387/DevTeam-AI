/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    'bg-obsidian-900',
    'bg-obsidian-950',
    'bg-obsidian-850',
    'bg-obsidian-800',
    'bg-obsidian-700',
    'text-electric-lime',
    'border-obsidian-700',
    'border-obsidian-600',
    'text-obsidian-50',
    'text-obsidian-300',
    'text-obsidian-400',
  ],
  theme: {
    extend: {
      colors: {
        // OBSIDIAN + ELECTRIC LIME palette
        obsidian: {
          50:  '#F2F3EC',
          100: '#E4E6DA',
          200: '#C8CCB5',
          300: '#969D94',
          400: '#6B7268',
          500: '#3D4238',
          600: '#252A22',
          700: '#191E1A',  // card bg
          800: '#141710',  // subtle variant
          850: '#0A0D0B',  // sidebar
          900: '#101211',  // main bg
          950: '#080A08',
          DEFAULT: '#101211',
        },
        'electric-lime': {
          DEFAULT: '#C5F467',
          50:  '#F7FDE8',
          100: '#EDFAC7',
          200: '#D8F493',
          300: '#C5F467',  // electric lime primary accent
          400: '#AEE83C',
          500: '#8FCA1A',
          600: '#6EA012',
          700: '#527A0D',
          800: '#3F5E0B',
          900: '#344F0A',
        },
        lime: {
          DEFAULT: '#C5F467',
          50:  '#F7FDE8',
          100: '#EDFAC7',
          200: '#D8F493',
          300: '#C5F467',
          400: '#AEE83C',
          500: '#8FCA1A',
          600: '#6EA012',
          700: '#527A0D',
          800: '#3F5E0B',
          900: '#344F0A',
        },
        sage: {
          DEFAULT: '#829B70',
          300: '#B3C9A0',
          400: '#829B70', // secondary accent
          500: '#637855',
          600: '#4C5C41',
        },
        // Status colors
        status: {
          success: '#8ED49B',
          warning: '#E9AD55',
          error:   '#E16D6D',
        },
        // Backwards compatibility with initial components
        dark: {
          50:  '#F2F3EC',
          100: '#E4E6DA',
          200: '#C8CCB5',
          700: '#191E1A',
          800: '#141710',
          850: '#0A0D0B',
          900: '#101211',
          950: '#080A08',
        },
        brand: {
          50:  '#F7FDE8',
          100: '#EDFAC7',
          400: '#C5F467',
          500: '#C5F467',
          600: '#AEE83C',
          700: '#8FCA1A',
        },
        accent: {
          purple: '#8B5CF6',
          cyan:   '#06B6D4',
          green:  '#8ED49B',
          amber:  '#E9AD55',
          red:    '#E16D6D',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        // Subtle technical grid texture
        'grid-obsidian': `
          linear-gradient(rgba(197,244,103,0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(197,244,103,0.03) 1px, transparent 1px)
        `,
      },
      backgroundSize: {
        'grid-sm': '24px 24px',
        'grid-md': '40px 40px',
      },
      animation: {
        'pulse-slow':  'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in':     'fadeIn 0.25s ease-out',
        'slide-in':    'slideIn 0.25s ease-out',
        'blink':       'blink 1.2s step-end infinite',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%':   { transform: 'translateX(-8px)', opacity: '0' },
          '100%': { transform: 'translateX(0)',    opacity: '1' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}

