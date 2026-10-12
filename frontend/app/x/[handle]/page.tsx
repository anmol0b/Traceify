import { Suspense } from "react";
import { ProfileSkeleton, ProfileView } from "@/components/ProfileView";

export default function ProfilePage({ params }: PageProps<"/x/[handle]">) {
  return (
    <Suspense fallback={<ProfileSkeleton />}>
      {params.then(({ handle }) => (
        <ProfileView key={handle} handle={decodeURIComponent(handle)} />
      ))}
    </Suspense>
  );
}
