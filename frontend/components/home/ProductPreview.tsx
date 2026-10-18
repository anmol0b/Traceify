import Image from "next/image";
import { ContainerScroll } from "@/components/ui/container-scroll-animation";
import preview from "@/public/preview.jpg";

export function ProductPreview() {
  return (
    <ContainerScroll className="px-3 pt-14 pb-16 md:px-12 md:pt-20 md:pb-24">
      <div className="flex h-9 items-center gap-3 border-b bg-surface px-3 md:h-10 md:px-4">
        <div aria-hidden className="flex gap-1.5">
          <span className="size-2.5 rounded-full bg-[#2e2e2e]" />
          <span className="size-2.5 rounded-full bg-[#2e2e2e]" />
          <span className="size-2.5 rounded-full bg-[#2e2e2e]" />
        </div>
        <div className="mx-auto flex h-6 max-w-xs flex-1 items-center justify-center rounded-md border bg-background px-3 font-mono text-[11px] text-subtle-foreground md:text-xs">
          traceify.anmol0b.xyz/x/naval
        </div>
        <div aria-hidden className="w-[42px]" />
      </div>
      <Image
        src={preview}
        alt="The Traceify profile page for @naval: profile stats and top tweets on the left, the AI chat with suggested questions on the right."
        sizes="(min-width: 1100px) 1024px, 100vw"
        placeholder="blur"
        className="h-auto w-[640px] max-w-none sm:w-full sm:max-w-full"
      />
    </ContainerScroll>
  );
}
