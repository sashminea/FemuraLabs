import type { MetadataRoute } from "next";

import { site } from "@/lib/site";

// Required for `output: "export"`: this file is generated at build time,
// not served by a Node.js server.
export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: "/" }],
    sitemap: `${site.url}/sitemap.xml`,
  };
}
