"use client";

export function AdminShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto max-w-6xl pb-16">
      <header className="mb-8 border-b border-copper/10 pb-6">
        <p className="label-caps mb-2 text-copper/80">Admin · Tier 3</p>
        <h1 className="font-title text-2xl text-ivory md:text-3xl">{title}</h1>
        <p className="mt-2 font-body text-sm text-titanium/70">{subtitle}</p>
      </header>
      {children}
    </div>
  );
}
