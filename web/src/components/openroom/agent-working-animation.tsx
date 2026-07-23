import { TypewriterCode } from "./typewriter-code";

interface AgentWorkingAnimationProps {
  status: string;
  currentCodeLines?: string[];
}

export function AgentWorkingAnimation({
  status,
  currentCodeLines = [],
}: AgentWorkingAnimationProps) {
  if (status !== "working") return null;

  if (!currentCodeLines.length) {
    return (
      <div className="mb-4 rounded-lg border border-copper/10 bg-obsidian px-3 py-2 font-mono text-[10px] text-titanium/60">
        Agent en cours — en attente du flux code live (IDE / pipeline)…
      </div>
    );
  }

  return (
    <div className="relative mb-4 h-32 w-full overflow-hidden rounded-lg border border-copper/10 bg-obsidian">
      <div className="absolute bottom-0 left-5 flex flex-col items-center">
        <div className="mb-0.5 h-5 w-5 rounded-full bg-titanium/30" />
        <div className="h-10 w-8 rounded-t-md bg-titanium/15 [animation:sway_2s_ease-in-out_infinite]" />
        <div className="-mt-1.5 flex gap-0.5">
          <div className="h-5 w-2.5 rounded bg-titanium/15 [animation:type-left_0.4s_ease-in-out_infinite_alternate]" />
          <div className="h-5 w-2.5 rounded bg-titanium/15 [animation:type-right_0.4s_ease-in-out_infinite_alternate_200ms]" />
        </div>
      </div>

      <div className="absolute bottom-3 right-3 top-3 w-44 overflow-hidden rounded border border-copper/20 bg-[#0a0c10] p-2 font-mono text-[8px]">
        <TypewriterCode lines={currentCodeLines} />
      </div>

      <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent to-copper/[0.03]" />
    </div>
  );
}
