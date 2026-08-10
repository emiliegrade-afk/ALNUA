import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        background: "var(--background)",
        foreground: "var(--foreground)",
        obsidian: {
          DEFAULT: "#0E1014",
          2: "#16181D",
          3: "#1A1E24",
        },
        void: "#000000",
        ivory: "#F5F2EA",
        titanium: "#B8BDC4",
        "titanium-cold": "#E2E5E9",
        copper: {
          DEFAULT: "#E09B6A",
          light: "#F5C9A4",
          dim: "#B86E45",
          glow: "#F5C9A4",
          muted: "#B86E45",
        },
        surface: {
          DEFAULT: "#12141A",
          raised: "#1A1E24",
        },
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
        sidebar: {
          DEFAULT: "var(--sidebar)",
          foreground: "var(--sidebar-foreground)",
          primary: "var(--sidebar-primary)",
          "primary-foreground": "var(--sidebar-primary-foreground)",
          accent: "var(--sidebar-accent)",
          "accent-foreground": "var(--sidebar-accent-foreground)",
          border: "var(--sidebar-border)",
          ring: "var(--sidebar-ring)",
        },
        // Brand board ALNUA — source de vérité pour les tokens sémantiques
        alnua: {
          bg: "#0E1014",
          surface: "#12141A",
          border: "#2A2E38",
          titane: "#B8BDC4",
          ivoire: "#F5F2EA",
          cuivre: "#E09B6A",
          teal: "#2DD4BF",
          danger: "#F87171",
          DEFAULT: "#E09B6A",
          glow: "#F5C9A4",
          muted: "#B86E45",
        },
        bronze: {
          DEFAULT: "#E09B6A",
          bright: "#F5C9A4",
        },
        cuivre: "#E09B6A",
        titane: "#B8BDC4",
        ivoire: "#F5F2EA",
        teal: "#2DD4BF",
        danger: "#F87171",
        glow: "#F5C9A4",
        online: { DEFAULT: "#2DD4BF", soft: "#5EEAD4" },
        "obsidian-deep": "#050507",
      },
      fontFamily: {
        display: ["var(--font-space-grotesk)", "Space Grotesk", "sans-serif"],
        title: ["var(--font-space-grotesk)", "Space Grotesk", "sans-serif"],
        subtitle: ["Avenir Next", "Nunito", "sans-serif"],
        body: ["var(--font-inter)", "Inter", "sans-serif"],
        sans: ["var(--font-inter)", "Inter", "sans-serif"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.5s ease-out forwards",
        shimmer: "shimmer 2s linear infinite",
        "confetti-fall": "confettiFall 2.5s ease-out forwards",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        confettiFall: {
          "0%": { transform: "translateY(-10vh) rotate(0deg)", opacity: "1" },
          "100%": { transform: "translateY(110vh) rotate(720deg)", opacity: "0" },
        },
      },
      letterSpacing: {
        forge: "0.35em",
        "forge-sm": "0.2em",
      },
      boxShadow: {
        "copper-glow": "0 0 0 1px rgba(224,155,106,0.35), 0 0 20px rgba(245,201,164,0.45), 0 0 40px rgba(224,155,106,0.5)",
        "copper-glow-lg": "0 0 0 1px rgba(224,155,106,0.45), 0 0 28px rgba(245,201,164,0.5), 0 0 64px rgba(224,155,106,0.55)",
      },
    },
  },
  plugins: [],
};
export default config;
