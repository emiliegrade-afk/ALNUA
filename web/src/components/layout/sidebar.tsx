"use client";



import Link from "next/link";

import { usePathname } from "next/navigation";

import { useEffect, useState } from "react";

import {

  BarChart3,

  FlaskConical,

  Handshake,

  LayoutDashboard,

  Lightbulb,

  ListPlus,

  Megaphone,

  Newspaper,

  Palette,

  Rocket,

  Ticket,

  Wallet,

} from "lucide-react";

import { AlnuaLogo } from "@/components/brand/alnua-logo";

import {

  fetchTodayBriefing,

  type BriefingBadge,

} from "@/lib/briefing-api";

import { cn } from "@/lib/utils";



const NAV = [

  { href: "/", label: "Lobby", icon: LayoutDashboard },

  { href: "/briefing", label: "Briefing", icon: Newspaper, badge: true },

  { href: "/tickets", label: "Tickets", icon: Ticket },

  { href: "/beta", label: "Beta", icon: FlaskConical },

  { href: "/waitlist", label: "Waitlist", icon: ListPlus },

  { href: "/partnerships/manage", label: "Partenariats", icon: Handshake },

  { href: "/content", label: "Contenu", icon: Megaphone },

  { href: "/releases", label: "Releases", icon: Rocket },

  { href: "/analytics", label: "Analytics", icon: BarChart3 },

  { href: "/finances", label: "Finances", icon: Wallet },

  { href: "/rd", label: "R&D", icon: Lightbulb },

  { href: "/brand", label: "Brand Kit", icon: Palette },

] as const;



function BriefingNavBadge({ badge }: { badge: BriefingBadge | null }) {

  if (!badge) return null;



  const count = badge.has_urgent

    ? badge.urgent_count

    : badge.pending_count > 0

      ? badge.pending_count

      : 0;



  if (count <= 0) return null;



  return (

    <span

      className={cn(

        "ml-auto flex h-5 min-w-5 items-center justify-center rounded-full px-1 text-[10px] font-semibold",

        badge.has_urgent

          ? "bg-red-500/25 text-red-300"

          : "bg-copper/25 text-copper-light"

      )}

    >

      {count}

    </span>

  );

}



export function Sidebar() {

  const pathname = usePathname();

  const [briefingBadge, setBriefingBadge] = useState<BriefingBadge | null>(null);



  useEffect(() => {

    let cancelled = false;

    fetchTodayBriefing()

      .then((b) => {

        if (!cancelled) {

          setBriefingBadge({

            has_urgent: b.has_urgent,

            urgent_count: b.urgent_count,

            pending_count: b.pending_count,

          });

        }

      })

      .catch(() => {

        if (!cancelled) setBriefingBadge(null);

      });

    return () => {

      cancelled = true;

    };

  }, []);



  return (

    <aside className="fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-copper/10 bg-sidebar/95 backdrop-blur-xl">

      <div className="flex justify-center border-b border-copper/10 px-4 py-5">

        <Link href="/" className="transition opacity-90 hover:opacity-100">

          <AlnuaLogo variant="lockup" height={56} />

        </Link>

      </div>



      <nav className="flex-1 space-y-1 p-3">

        {NAV.map(({ href, label, icon: Icon, ...rest }) => {

          const active = pathname === href;

          const showBadge = "badge" in rest && rest.badge;

          return (

            <Link

              key={href}

              href={href}

              aria-current={active ? "page" : undefined}

              className={cn(

                "group flex items-center gap-3 rounded-lg border px-3 py-2.5 text-sm transition-all duration-200 outline-none focus-visible:ring-2 focus-visible:ring-copper/50",

                active

                  ? "border-copper/45 bg-copper/10 text-copper-light shadow-[0_0_16px_rgba(192,138,98,0.12)]"

                  : "border-transparent text-titanium hover:border-copper/20 hover:bg-copper/5 hover:text-ivory"

              )}

            >

              <Icon

                className={cn(

                  "h-4 w-4 shrink-0 transition-colors",

                  active

                    ? "text-copper"

                    : "text-titanium/70 group-hover:text-copper-light"

                )}

              />

              {label}

              {showBadge ? (

                <BriefingNavBadge badge={briefingBadge} />

              ) : null}

            </Link>

          );

        })}

      </nav>



      <div className="border-t border-copper/10 p-4">

        <div className="rounded-lg border border-copper/10 bg-white/[0.02] p-3">

          <p className="text-xs font-medium tracking-wide text-ivory/90">

            Emilie · CEO

          </p>

          <p className="mt-1 text-[11px] text-titanium">

            3 branches · 1 humaine

          </p>

          <div className="mt-2 flex gap-1.5">

            <span className="h-1.5 w-1.5 rounded-full bg-copper-light" title="Naïa" />

            <span

              className="h-1.5 w-1.5 rounded-full bg-copper"

              title="Wyrdheim"

            />

            <span className="h-1.5 w-1.5 rounded-full bg-copper-dim" title="Eve" />

          </div>

        </div>

      </div>

    </aside>

  );

}

