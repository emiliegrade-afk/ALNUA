import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import { HubShell } from "@/components/layout/hub-shell";
import { cn } from "@/lib/utils";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  // Brand board: Inter = body/UI ; alias legacy --font-geist-sans conservé
  variable: "--font-inter",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
});

export const viewport: Viewport = {
  themeColor: "#0E1014",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export const metadata: Metadata = {
  title: "ALNUA Hub",
  description:
    "Cockpit ALNUA — Imagination, Technology, Creation. Transformées en réalité.",
  applicationName: "ALNUA Hub",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "ALNUA",
  },
  icons: {
    icon: [
      { url: "/favicon.ico?v=20260811", sizes: "any", type: "image/x-icon" },
      { url: "/favicon-32.png?v=20260811", sizes: "32x32", type: "image/png" },
      { url: "/icon-192.png?v=20260811", sizes: "192x192", type: "image/png" },
      { url: "/icon-512.png?v=20260811", sizes: "512x512", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png?v=20260811",
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
        "dark h-full",
        inter.variable,
        spaceGrotesk.variable,
        jetbrainsMono.variable
      )}
    >
      <body className="h-full min-h-screen bg-obsidian font-body text-ivory antialiased">
        <HubShell>{children}</HubShell>
      </body>
    </html>
  );
}
