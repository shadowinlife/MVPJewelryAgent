import Image from "next/image";

import { cn } from "@/lib/utils";

export function WatermarkImage({
  src,
  alt,
  caseNo,
  userSuffix,
  ratio = "square",
  className,
  priority,
}: {
  src: string;
  alt: string;
  caseNo: string;
  userSuffix?: string;
  ratio?: "square" | "video" | "portrait";
  className?: string;
  priority?: boolean;
}) {
  const ratioClass =
    ratio === "video"
      ? "aspect-video"
      : ratio === "portrait"
        ? "aspect-[3/4]"
        : "aspect-square";

  const marker = userSuffix ? `${caseNo} · ${userSuffix}` : caseNo;

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-md border border-border bg-muted",
        ratioClass,
        className,
      )}
      data-watermark="true"
    >
      <Image
        src={src}
        alt={alt}
        fill
        sizes="(max-width: 768px) 100vw, 50vw"
        priority={priority}
        className="object-cover select-none pointer-events-none"
        draggable={false}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 mix-blend-soft-light"
        style={{
          backgroundImage: `url("data:image/svg+xml;utf8,${encodeURIComponent(
            `<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'>
              <g transform='rotate(-28 110 110)' fill='%23f8f4ea' opacity='0.55' font-family='Georgia, serif' font-size='14' letter-spacing='3'>
                <text x='10' y='60'>YAOQI · ${marker}</text>
                <text x='10' y='140'>YAOQI · ${marker}</text>
                <text x='10' y='220'>YAOQI · ${marker}</text>
              </g>
            </svg>`,
          )}")`,
          backgroundRepeat: "repeat",
        }}
      />
      <div className="absolute bottom-2 right-2 rounded-sm bg-foreground/55 px-1.5 py-0.5 text-[10px] tracking-wide text-background">
        {marker}
      </div>
    </div>
  );
}
