"use client"

import * as React from "react"
import { Tabs as TabsPrimitive } from "radix-ui"

import { cn } from "@/lib/utils"

function Tabs({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Root>) {
  return (
    <TabsPrimitive.Root
      data-slot="tabs"
      className={cn("flex flex-col gap-4", className)}
      {...props}
    />
  )
}

/**
 * `variant="underline"` reproduit la barre d'onglets des maquettes : libellés
 * en capitales espacées sur une règle continue, onglet actif souligné en
 * cuivre. `pill` (défaut) reste utilisé par les sous-onglets internes
 * (Discussion/Notes, Aperçu/Compétences…), où la règle n'aurait pas de sens.
 */
type TabsVariant = "pill" | "underline"

const TabsVariantContext = React.createContext<TabsVariant>("pill")

function TabsList({
  className,
  variant = "pill",
  ...props
}: React.ComponentProps<typeof TabsPrimitive.List> & { variant?: TabsVariant }) {
  return (
    <TabsVariantContext.Provider value={variant}>
      <TabsPrimitive.List
        data-slot="tabs-list"
        data-variant={variant}
        className={cn(
          variant === "underline"
            ? "flex w-full items-center gap-1 overflow-x-auto border-b border-bronze-faint"
            : "inline-flex w-fit items-center gap-1 rounded-lg border border-bronze-faint bg-obsidian-deep/60 p-1",
          className
        )}
        {...props}
      />
    </TabsVariantContext.Provider>
  )
}

function TabsTrigger({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  const variant = React.useContext(TabsVariantContext)
  return (
    <TabsPrimitive.Trigger
      data-slot="tabs-trigger"
      className={cn(
        "inline-flex items-center justify-center gap-2 whitespace-nowrap transition-colors outline-none focus-visible:ring-2 focus-visible:ring-copper/50 disabled:pointer-events-none disabled:opacity-50",
        variant === "underline"
          ? "-mb-px border-b-2 border-transparent px-2.5 py-3 text-xs font-semibold uppercase tracking-[0.08em] text-titane/60 hover:text-ivoire/90 data-[state=active]:border-copper data-[state=active]:text-copper-light xl:px-4 xl:tracking-[0.16em]"
          : "rounded-md px-3.5 py-1.5 text-sm font-medium text-titane/70 hover:text-ivoire/90 data-[state=active]:bg-copper/12 data-[state=active]:text-copper-light",
        className
      )}
      {...props}
    />
  )
}

function TabsContent({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Content>) {
  return (
    <TabsPrimitive.Content
      data-slot="tabs-content"
      className={cn("outline-none", className)}
      {...props}
    />
  )
}

export { Tabs, TabsList, TabsTrigger, TabsContent }
