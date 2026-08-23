"use client";

import {
  LOUNGE_ACTIVITIES,
  type LoungeActivity,
  type LoungeActivityId,
} from "@/components/lounge/lounge-constants";

type Props = {
  onPlay: (id: LoungeActivityId) => void;
};

function ActivityCard({
  activity,
  onPlay,
}: {
  activity: LoungeActivity;
  onPlay: (id: LoungeActivityId) => void;
}) {
  return (
    <article
      className="flex w-[148px] shrink-0 flex-col items-center overflow-hidden rounded-xl border border-white/10 bg-obsidian-2 sm:w-[156px]"
      style={{ boxShadow: `0 0 18px ${activity.accent}` }}
    >
      <p className="w-full px-2 pt-3 text-center text-[11px] font-semibold uppercase tracking-[0.14em] text-ivory">
        {activity.label}
      </p>

      <div className="mt-2 h-[100px] w-[124px] overflow-hidden rounded-lg bg-obsidian-deep sm:h-[108px] sm:w-[132px]">
        {activity.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={activity.image}
            alt=""
            className="h-full w-full object-contain object-center"
          />
        ) : (
          <span
            className="flex h-full w-full items-center justify-center text-3xl"
            style={{
              background: `radial-gradient(circle at 50% 40%, ${activity.accent}, #0E1014 70%)`,
            }}
            aria-hidden
          >
            🎨
          </span>
        )}
      </div>

      <p className="mt-2 line-clamp-2 min-h-[2.5rem] w-full px-2.5 text-center text-[10px] leading-snug text-titanium/55">
        {activity.blurb}
      </p>

      {/* Jouer : bouton centré dans la card (pas full-bleed) */}
      <div className="mt-auto flex w-full justify-center px-3 pb-3 pt-1">
        <button
          type="button"
          onClick={() => onPlay(activity.id)}
          className="min-w-[72%] rounded-md border border-copper/55 bg-copper/15 px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-[0.18em] text-copper transition hover:border-copper/80 hover:bg-copper/25"
        >
          Jouer
        </button>
      </div>
    </article>
  );
}

/** Cards jeux : titre / image / texte / Jouer centrés dans la carte. */
export function LoungeActivitiesGrid({ onPlay }: Props) {
  return (
    <section>
      <h2 className="mb-3 text-[11px] font-medium uppercase tracking-[0.2em] text-copper/85">
        Choisis ton activité
      </h2>
      <div className="alnua-scroll flex gap-2.5 overflow-x-auto pb-1">
        {LOUNGE_ACTIVITIES.map((a) => (
          <ActivityCard key={a.id} activity={a} onPlay={onPlay} />
        ))}
      </div>
    </section>
  );
}
