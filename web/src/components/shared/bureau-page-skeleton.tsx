export function BureauPageSkeleton() {
  return (
    <div className="mx-auto max-w-7xl animate-pulse px-6 py-8">
      <div className="mb-8 pt-12">
        <div className="mb-3 h-4 w-32 rounded bg-obsidian/50" />
        <div className="flex items-center gap-3">
          <div className="h-3 w-3 rounded-full bg-copper/30" />
          <div>
            <div className="mb-2 h-7 w-56 rounded bg-obsidian/50" />
            <div className="h-4 w-72 rounded bg-obsidian/50" />
          </div>
        </div>
      </div>
      <div className="mb-6 h-36 rounded-xl border border-copper/10 bg-obsidian-deep/40" />
      <div className="grid gap-4 md:grid-cols-2">
        <div className="h-44 rounded-xl border border-copper/10 bg-obsidian-deep/40" />
        <div className="h-44 rounded-xl border border-copper/10 bg-obsidian-deep/40" />
      </div>
    </div>
  );
}
