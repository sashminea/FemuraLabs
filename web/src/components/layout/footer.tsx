import Link from "next/link";

import { site } from "@/lib/site";

export function Footer() {
  return (
    <footer className="mt-auto border-t border-line py-10">
      <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-6 px-6">
        <div className="flex flex-wrap items-center gap-x-7 gap-y-2 text-sm text-mut">
          <Link href="/" className="font-medium text-tx">
            {site.name}
          </Link>
          <Link href="/docs" className="transition-colors hover:text-tx">
            Documentation
          </Link>
          <Link href="/docs/cli" className="transition-colors hover:text-tx">
            CLI Reference
          </Link>
          <a
            href={site.github}
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-tx"
          >
            GitHub
          </a>
          <a
            href={site.kaggle}
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-tx"
          >
            Kaggle
          </a>
          <a
            href={site.dataset}
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-tx"
          >
            Dataset
          </a>
        </div>
        <p className="font-mono text-xs text-dim">
          Code: {site.license} · Data: CC BY-NC-SA · Not for clinical use
        </p>
      </div>
    </footer>
  );
}
