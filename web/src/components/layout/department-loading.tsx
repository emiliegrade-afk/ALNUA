/** Instant skeleton while a bureau route chunk hydrates (lobby → bureau). */
export default function DepartmentRouteLoading() {
  return (
    <div className="animate-pulse px-6 pb-12 pt-16">
      <div className="mb-8 flex items-center gap-2">
        <div className="h-3 w-12 rounded bg-white/5" />
        <div className="h-3 w-3 rounded bg-white/5" />
        <div className="h-3 w-24 rounded bg-copper/20" />
      </div>
      <div className="mb-2 h-7 w-64 max-w-full rounded bg-white/5" />
      <div className="mb-8 h-4 w-80 max-w-full rounded bg-white/[0.03]" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="h-28 rounded-xl border border-white/5 bg-white/[0.02]" />
        <div className="h-28 rounded-xl border border-white/5 bg-white/[0.02]" />
        <div className="h-28 rounded-xl border border-white/5 bg-white/[0.02] sm:col-span-2 lg:col-span-1" />
      </div>
      <div className="mt-6 h-40 rounded-xl border border-white/5 bg-white/[0.02]" />
    </div>
  );
}
