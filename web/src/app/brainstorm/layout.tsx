export default function BrainstormLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="-my-8 flex h-[calc(100dvh-4rem)] flex-col overflow-hidden">
      {children}
    </div>
  );
}
