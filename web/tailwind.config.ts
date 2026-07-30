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
          DEFAULT: "#100F0D",
          2: "#171512",
          3: "#201D19",
        },
        ivory: "#F5F2EA",
        titanium: "#A7ADB5",
        "titanium-cold": "#A7ADB5",
        copper: {
          DEFAULT: "#C08A72",
          light: "#D9A88F",
          dim: "#8A6050",
          glow: "#D9A88F",
          muted: "#8A6050",
        },
        surface: {
          DEFAULT: "#171512",
          raised: "#201D19",
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
        alnua: {
          DEFAULT: "#C08A72",
          glow: "#D9A88F",
          muted: "#8A6050",
        },
        bronze: {
          DEFAULT: "#C08A72",
          bright: "#D9A88F",
        },
        cuivre: "#C08A72",
        titane: "#A7ADB5",
        ivoire: "#F5F2EA",
        glow: "#D9A88F",
        online: { DEFAULT: "#7FC98C", soft: "#8FCB99" },
        "obsidian-deep": "#0A0908",
      },
      fontFamily: {
        title: ["var(--font-space-grotesk)", "Space Grotesk", "sans-serif"],
        subtitle: ["Avenir Next", "Nunito", "sans-serif"],
        body: ["var(--font-geist-sans)", "Inter", "sans-serif"],
        sans: ["var(--font-geist-sans)", "Inter", "sans-serif"],
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
        "copper-glow": "0 0 24px rgba(192, 138, 98, 0.08)",
        "copper-glow-lg": "0 0 20px rgba(192, 138, 98, 0.15)",
      },
    },
  },
  plugins: [],
};
export default config;
