/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        alnua: {
          bg: '#0A0E1A',
          surface: '#111827',
          'surface-2': '#1F2937',
          border: '#374151',
          accent: '#6366F1',
          app: '#10B981',
          gaming: '#F59E0B',
          robo: '#3B82F6',
          success: '#22C55E',
          error: '#EF4444',
          text: '#F9FAFB',
          muted: '#9CA3AF',
        },
      },
      fontFamily: {
        heading: ['"Space Grotesk"', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'accent-glow': '0 0 24px rgba(99, 102, 241, 0.3)',
      },
    },
  },
  plugins: [],
}
