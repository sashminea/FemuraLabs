"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { docsFlat } from "@/lib/docs";

const normalize = (p: string) => p.replace(/^\/+|\/+$/g, "");

export function Pager() {
  const pathname = usePathname();
  const idx = docsFlat.findIndex(
    (p) => normalize(p.href) === normalize(pathname),
  );
  if (idx === -1) return null;

  const prev = docsFlat[idx - 1];
  const next = docsFlat[idx + 1];

  return (
    <nav className="mt-24 grid gap-3 sm:grid-cols-2">
      {prev && (
        <Link
          href={prev.href}
          rel="prev"
          className="group flex flex-col rounded-2xl border border-line bg-s1 p-5 transition-colors hover:border-line2 hover:bg-s2"
        >
          <span className="font-mono text-[11px] uppercase tracking-[0.1em] text-dim">
            Previous
          </span>
          <span className="mt-1.5 flex items-center gap-2 text-[15px] text-tx">
            <span className="transition-transform group-hover:-translate-x-1">
              ←
            </span>
            {prev.title}
          </span>
        </Link>
      )}
      {next && (
        <Link
          href={next.href}
          rel="next"
          className="group flex flex-col items-end rounded-2xl border border-line bg-s1 p-5 text-right transition-colors hover:border-line2 hover:bg-s2 sm:col-start-2"
        >
          <span className="font-mono text-[11px] uppercase tracking-[0.1em] text-dim">
            Next
          </span>
          <span className="mt-1.5 flex items-center gap-2 text-[15px] text-tx">
            {next.title}
            <span className="transition-transform group-hover:translate-x-1">
              →
            </span>
          </span>
        </Link>
      )}
    </nav>
  );
}
