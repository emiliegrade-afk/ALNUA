export default function Loading() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center px-6">
      <div className="w-full max-w-md space-y-4 animate-pulse">
        <div className="mx-auto h-0.5 w-24 overflow-hidden rounded-full bg-obsidian/50">
          <div className="h-full w-1/2 animate-hub-nav-progress bg-copper/70" />
        </div>
        <div className="h-4 rounded bg-obsidian/50" />
        <div className="h-32 rounded-xl border border-copper/10 bg-obsidian-deep/40" />
      </div>
    </div>
  );
}
