/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: '#FAF8F5',
          subtle: '#F4F0E8',
          card: '#FFFFFF',
          dark: '#141416',
          sand: '#ECE7DD',
        },
        ink: {
          DEFAULT: '#141416',
          secondary: '#3F3F46',
          muted: '#71717A',
          faint: '#A1A1AA',
        },
        accent: {
          gold: '#C29B38',
          crimson: '#9E2A2B',
          amber: '#D97706',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        serif: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      letterSpacing: {
        tightest: '-0.04em',
        tighter: '-0.025em',
        tight: '-0.015em',
      },
      boxShadow: {
        'subtle': '0 1px 3px 0 rgba(28, 25, 23, 0.04), 0 1px 2px 0 rgba(28, 25, 23, 0.02)',
        'card': '0 1px 3px 0 rgba(28, 25, 23, 0.03), 0 8px 24px -4px rgba(28, 25, 23, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.95), inset 0 0 0 1px rgba(255, 255, 255, 0.5)',
        'card-hover': '0 4px 12px 0 rgba(28, 25, 23, 0.05), 0 16px 36px -6px rgba(28, 25, 23, 0.1), inset 0 1px 0 rgba(255, 255, 255, 1)',
        'paper-float': '0 2px 6px rgba(28, 25, 23, 0.04), 0 16px 32px -4px rgba(28, 25, 23, 0.1), 0 36px 72px -16px rgba(28, 25, 23, 0.18), 0 0 0 1px rgba(180, 165, 145, 0.25)',
        'paper-emboss': 'inset 0 2px 4px rgba(255, 255, 255, 0.9), inset 0 -2px 4px rgba(0, 0, 0, 0.06), 0 4px 12px rgba(28, 25, 23, 0.08)',
        'floating-dock': '0 24px 60px -12px rgba(28, 25, 23, 0.16), 0 12px 24px -6px rgba(28, 25, 23, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.95), 0 0 0 1px rgba(228, 224, 216, 0.8)',
        'inner-bevel': 'inset 0 1.5px 0.5px rgba(255, 255, 255, 0.9), inset 0 -1.5px 0.5px rgba(0, 0, 0, 0.04)',
        'loupe-lens': '0 20px 40px -10px rgba(0,0,0,0.3), 0 0 0 8px rgba(255,255,255,0.85), inset 0 0 20px rgba(0,0,0,0.15)',
      },
      backgroundImage: {
        'parchment-gradient': 'linear-gradient(145deg, #FFFDFB 0%, #FAF7F0 45%, #F4EFE3 100%)',
        'mat-gradient': 'radial-gradient(circle at 50% 35%, #F5F1E8 0%, #E8E2D5 60%, #DDD5C5 100%)',
        'subtle-mesh': 'radial-gradient(at 0% 0%, rgba(245, 240, 232, 0.85) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(238, 231, 218, 0.7) 0px, transparent 50%), radial-gradient(at 50% 50%, rgba(255, 255, 255, 0.5) 0px, transparent 100%)',
        'ambient-glow': 'radial-gradient(circle at 50% 0%, rgba(235, 225, 205, 0.45) 0%, transparent 70%)',
        'glass-gradient': 'linear-gradient(180deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 255, 255, 0.65) 100%)',
        'gold-seal': 'radial-gradient(circle at 35% 35%, #FFF6D6 0%, #E6CA65 40%, #B38B25 75%, #805E12 100%)',
        'crimson-seal': 'radial-gradient(circle at 35% 35%, #FFD6D6 0%, #E66565 40%, #9E1F1F 75%, #6B0E0E 100%)',
      }
    },
  },
  plugins: [],
}
