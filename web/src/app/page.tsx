import { LobbyView } from "@/components/lobby/lobby-view";
import { HQ_HUB_IMAGE_WEBP } from "@/lib/hq-hub-offices";

export default function HomePage() {
  return (
    <>
      <link
        rel="preload"
        as="image"
        href={HQ_HUB_IMAGE_WEBP}
        type="image/webp"
      />
      <LobbyView />
    </>
  );
}
