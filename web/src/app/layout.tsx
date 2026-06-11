import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import { HubShell } from "@/components/layout/hub-shell";
import { cn } from "@/lib/utils";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
});

export const metadata: Metadata = {
  title: "ALNUA Hub",
  description:
    "Cockpit ALNUA — Imagination, Technology, Creation. Transformées en réalité.",
  icons: {
    icon: "/alnua-icon.png",
    apple: "/alnua-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="fr"
      className={cn(
        "dark",
        inter.variable,
        spaceGrotesk.variable,
        jetbrainsMono.variable
      )}
    >
      <body className="min-h-screen font-body antialiased">
        <div className="relative min-h-screen bg-obsidian">
          <div className="pointer-events-none fixed inset-0 forge-grid opacity-50" />
          <div className="pointer-events-none fixed inset-0 bg-gradient-to-br from-copper/5 via-transparent to-transparent" />
          <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(192,138,98,0.06),transparent_50%)]" />

          <HubShell>{children}</HubShell>
        </div>
      </body>
    </html>
  );
}
