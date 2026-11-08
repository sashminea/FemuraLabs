"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { docsConfig } from "@/lib/docs";

const normalize = (p: string) => p.replace(/^\/+|\/+$/g, "");

export function DocsSidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-16 hidden h-[calc(100vh-4rem)] w-64 shrink-0 overflow-y-auto border-r border-line py-10 pr-6 md:block">
      <nav>
        {docsConfig.map((group) => (
          <div key={group.title} className="mb-8">
            <h3 className="mb-2 px-3 font-mono text-[11px] font-medium uppercase tracking-[0.1em] text-dim">
              {group.title}
            </h3>
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const active = normalize(pathname) === normalize(item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`block rounded-lg px-3 py-2 text-sm transition-colors ${
                        active
                          ? "bg-blue/10 text-tx shadow-[inset_2px_0_0_var(--color-blue)]"
                          : "text-mut hover:bg-white/5 hover:text-tx"
                      }`}
                    >
                      {item.title}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  );
}
