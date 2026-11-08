import type { MetadataRoute } from "next";

import { site } from "@/lib/site";

// Required for `output: "export"`: this file is generated at build time,
// not served by a Node.js server.
export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return [
    { url: `${site.url}/`, lastModified: now, changeFrequency: "monthly", priority: 1 },
    { url: `${site.url}/docs/`, lastModified: now, changeFrequency: "weekly", priority: 0.9 },
    { url: `${site.url}/docs/quickstart/`, lastModified: now, changeFrequency: "weekly", priority: 0.8 },
    { url: `${site.url}/docs/cli/`, lastModified: now, changeFrequency: "weekly", priority: 0.8 },
    { url: `${site.url}/docs/architecture/`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    { url: `${site.url}/docs/simulator/`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    { url: `${site.url}/docs/validation/`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    { url: `${site.url}/simulator/`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
  ];
}
