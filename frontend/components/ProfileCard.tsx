import { ArrowUpRight, BadgeCheck, CalendarDays, Link2, MapPin, TriangleAlert } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { NumberTicker } from "@/components/ui/number-ticker";
import { formatCount } from "@/lib/api";
import type { Profile } from "@/lib/types";

function Stat({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="min-w-0 px-4 py-5 md:px-8">
      <div className="text-[13px] text-muted-foreground">{label}</div>
      <div className="mt-1 truncate text-2xl font-semibold tracking-[-0.03em] text-foreground md:text-[28px]">
        {value === null ? "—" : <NumberTicker value={value} format={formatCount} />}
      </div>
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
    <section aria-label="Profile">
      <div className="px-4 py-8 md:px-8">
        <div className="flex items-center gap-4 md:gap-5">
          <Avatar className="size-16 ring-1 ring-border md:size-[72px]">
            {avatar && <AvatarImage src={avatar} alt="" />}
            <AvatarFallback className="bg-secondary text-2xl font-semibold">{profile.display_name.slice(0, 1)}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <div className="flex min-w-0 items-center gap-1.5">
              <h1 className="truncate text-2xl font-semibold tracking-[-0.03em] text-foreground md:text-[28px]">
                {profile.display_name}
              </h1>
              {profile.is_verified && (
                <BadgeCheck role="img" aria-label="Verified account" className="size-5 shrink-0 text-info" />
              )}
            </div>
            <a
              href={profile.public_url}
              target="_blank"
              rel="noreferrer"
              className="group mt-0.5 inline-flex items-center gap-0.5 rounded-sm font-mono text-sm text-muted-foreground transition-colors duration-150 outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
            >
              @{profile.handle}
              <ArrowUpRight
                aria-hidden
                className="size-3.5 transition-transform duration-150 group-hover:translate-x-px group-hover:-translate-y-px motion-reduce:transition-none"
              />
            </a>
          </div>
        </div>

        {profile.bio ? (
          <p className="mt-6 max-w-prose text-[15px] leading-relaxed whitespace-pre-line text-foreground/90">{profile.bio}</p>
        ) : (
          <p className="mt-6 text-sm text-subtle-foreground">No bio.</p>
        )}

        {(profile.location || profile.website || joined) && (
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-muted-foreground">
            {profile.location && (
              <span className="inline-flex items-center gap-1.5">
                <MapPin aria-hidden className="size-3.5" />
                {profile.location}
              </span>
            )}
            {profile.website && (
              <a
                href={profile.website}
                target="_blank"
                rel="noreferrer nofollow"
                className="inline-flex items-center gap-1.5 rounded-sm transition-colors duration-150 outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
              >
                <Link2 aria-hidden className="size-3.5" />
                {hostname(profile.website)}
              </a>
            )}
            {joined && !Number.isNaN(joined.getTime()) && (
              <span className="inline-flex items-center gap-1.5">
                <CalendarDays aria-hidden className="size-3.5" />
                Joined {joined.toLocaleDateString("en", { month: "short", year: "numeric" })}
              </span>
            )}
          </div>
        )}

        {profile.warnings.length > 0 && (
          <Alert className="mt-6 border-warning/30 bg-warning/5 text-warning">
            <TriangleAlert aria-hidden />
            <AlertDescription className="text-warning/90">
              <ul className="space-y-1">
                {profile.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}
      </div>

      <div className="grid grid-cols-3 divide-x border-y">
        <Stat label="Followers" value={profile.followers} />
        <Stat label="Following" value={profile.following} />
        <Stat label="Posts" value={profile.tweet_count} />
      </div>
    </section>
  );
}
