import type { Metadata } from "next";

import { site } from "@/lib/site";

export function withOg(
  slug: string,
  title: string,
  description: string,
): Metadata {
  // Absolute URL — `new URL("/og/landing.png", metadataBase)` strips the
  // metadataBase path when the image path starts with `/`, which would
  // point at sashminea.github.io/og/landing.png instead of
  // sashminea.github.io/FemuraLabs/og/landing.png.
  const image = `${site.url}/og/${slug}.png`;
  return {
    title,
    description,
    openGraph: {
      title,
      description,
      images: [{ url: image, width: 1200, height: 630, alt: title }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [image],
    },
  };
}
