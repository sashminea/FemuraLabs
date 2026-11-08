import Link from "next/link";

import { Reveal } from "@/components/ui/reveal";
import { site } from "@/lib/site";

const LINKS = [
  { label: "Apache 2.0 licence", href: `${site.github}/blob/main/LICENSE`, external: true },
  { label: "VSD dataset on Zenodo", href: site.dataset, external: true },
  { label: "Kaggle training notebook", href: site.kaggle, external: true },
  { label: "CLI reference", href: "/docs/cli", external: false },
];

export function Oss() {
  const cls =
    "group flex items-center justify-between border-t border-line py-6 text-[clamp(1.2rem,2.2vw,1.7rem)] tracking-[-0.04em] text-tx transition-[padding] duration-300 last:border-b hover:pl-3";
  return (
    <section id="oss" className="py-24 md:py-32">
      <div className="mx-auto grid max-w-7xl items-end gap-12 px-6 md:grid-cols-2 md:gap-16">
        <Reveal>
          <h2 className="max-w-[12ch] text-[clamp(2rem,4.8vw,3.8rem)] font-medium leading-[1.04] tracking-[-0.055em]">
            Open code. Open data. Open notebook.
          </h2>
        </Reveal>
        <Reveal delay={120}>
          <div>
            {LINKS.map((l) => {
              const inner = (
                <>
                  {l.label}
                  <span className="font-mono text-[13px] text-dim transition-transform group-hover:translate-x-1">
                    →
                  </span>
                </>
              );
              return l.external ? (
                <a
                  key={l.label}
                  href={l.href}
                  target="_blank"
                  rel="noreferrer"
                  className={cls}
                >
                  {inner}
                </a>
              ) : (
                <Link key={l.label} href={l.href} className={cls}>
                  {inner}
                </Link>
              );
            })}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
