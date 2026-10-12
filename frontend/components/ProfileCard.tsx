import type { Profile } from "@/lib/types";
import { formatCount } from "@/lib/api";

function Stat({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="rounded-lg border border-line bg-surface px-3 py-3">
      <div className="font-mono text-[0.65rem] uppercase tracking-[0.15em] text-faint">{label}</div>
      <div className="mt-1 text-xl font-medium tabular-nums text-[#f5f5ff]">{formatCount(value)}</div>
    </div>
  );
}

function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function ProfileCard({ profile }: { profile: Profile }) {
  const avatar = profile.profile_image_url?.replace("_normal", "_400x400");
  const joined = profile.joined_at ? new Date(profile.joined_at) : null;

  return (
    <section aria-label="Profile" className="space-y-5">
      <div className="flex items-start gap-4">
        {avatar ? (
          // eslint-disable-next-line @next/next/no-img-element -- remote avatar from pbs.twimg.com
          <img src={avatar} alt="" width={80} height={80} className="size-20 shrink-0 rounded-full border border-line object-cover" />
        ) : (
          <div className="grid size-20 shrink-0 place-items-center rounded-full border border-line bg-surface-2 font-serif text-3xl">
            {profile.display_name.slice(0, 1)}
          </div>
        )}
        <div className="min-w-0">
          <h1 className="truncate font-serif text-3xl text-[#f5f5ff]">{profile.display_name}</h1>
          <div className="mt-1 flex flex-wrap items-center gap-2 font-mono text-sm text-muted">
            <a href={profile.public_url} target="_blank" rel="noreferrer" className="hover:text-accent">
              @{profile.handle} ↗
            </a>
            {profile.is_verified && (
              <span className="rounded-full border border-accent/30 bg-accent/10 px-2 py-0.5 text-[0.65rem] uppercase tracking-wider text-accent">
                ✓ Verified
              </span>
            )}
          </div>
        </div>
      </div>

      {profile.bio ? (
        <p className="whitespace-pre-line leading-relaxed text-fg/85">{profile.bio}</p>
      ) : (
        <p className="italic text-faint">No bio.</p>
      )}

      <div className="flex flex-wrap gap-x-5 gap-y-1 font-mono text-xs text-muted">
        {profile.location && <span>📍 {profile.location}</span>}
        {profile.website && (
          <a href={profile.website} target="_blank" rel="noreferrer nofollow" className="hover:text-accent">
            🔗 {hostname(profile.website)}
          </a>
        )}
        {joined && !Number.isNaN(joined.getTime()) && (
          <span>📅 Joined {joined.toLocaleDateString("en", { month: "short", year: "numeric" })}</span>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2">
        <Stat label="Followers" value={profile.followers} />
        <Stat label="Following" value={profile.following} />
        <Stat label="Posts" value={profile.tweet_count} />
      </div>

      {profile.warnings.length > 0 && (
        <ul className="rounded-lg border border-warn/30 bg-warn/5 px-4 py-3 text-sm text-warn">
          {profile.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
