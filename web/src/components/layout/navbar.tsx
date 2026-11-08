"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { docsNav, marketingNav } from "@/lib/nav";
import { site } from "@/lib/site";

export function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const isDocs = pathname.startsWith("/docs");
  const links = isDocs ? docsNav : marketingNav;

  useEffect(() => {
    if (!open) return;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-50 border-b border-line bg-bg/70 backdrop-blur-md">
        <div className="mx-auto flex h-16 w-full max-w-7xl items-center gap-7 px-6">
          <Link
            href="/"
            className="mr-auto text-xl font-medium tracking-tight text-tx"
          >
            {site.name}
          </Link>

          <nav className="hidden gap-6 md:flex">
            {links.map((l) => {
              const active =
                pathname === l.href ||
                (l.href !== "/" && !l.href.includes("#") && pathname.startsWith(l.href));
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  className={`text-sm transition-colors ${
                    active ? "text-tx" : "text-mut hover:text-tx"
                  }`}
                >
                  {l.name}
                </Link>
              );
            })}
          </nav>

          {!isDocs && (
            <Button href="/docs" size="sm">
              Read Docs
            </Button>
          )}

          <a
            href={site.github}
            target="_blank"
            rel="noreferrer"
            aria-label="GitHub"
            className="hidden text-mut transition-colors hover:text-tx md:block"
          >
            <GitHubIcon />
          </a>

          <button
            type="button"
            aria-label="Toggle navigation"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
            className="grid h-9 w-9 place-items-center rounded-full border border-line2 bg-white/5 text-tx md:hidden"
          >
            {open ? <CloseIcon /> : <MenuIcon />}
          </button>
        </div>
      </header>

      {open && (
        <div className="fixed inset-x-0 top-16 bottom-0 z-40 overflow-y-auto bg-bg/95 backdrop-blur-lg md:hidden">
          <nav className="flex flex-col gap-1 p-6">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="rounded-lg px-3 py-3 text-lg text-tx transition-colors hover:bg-white/5"
              >
                {l.name}
              </Link>
            ))}
            {!isDocs && (
              <Link
                href="/docs"
                className="mt-4 rounded-full bg-tx px-4 py-3 text-center text-base font-medium text-bg"
              >
                Read Docs
              </Link>
            )}
            <a
              href={site.github}
              target="_blank"
              rel="noreferrer"
              className="mt-4 rounded-lg px-3 py-3 text-sm text-mut transition-colors hover:text-tx"
            >
              GitHub
            </a>
          </nav>
        </div>
      )}
    </>
  );
}

function MenuIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <path
        d="M1 3h12M1 7h12M1 11h12"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <path
        d="M1 1l12 12M13 1L1 13"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function GitHubIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 .3a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2c-3.3.7-4-1.6-4-1.6-.5-1.4-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.1.1 1.7 1.1 1.7 1.1 1 1.8 2.8 1.3 3.4 1 .1-.8.4-1.3.7-1.6-2.7-.3-5.4-1.3-5.4-6a4.7 4.7 0 0 1 1.2-3.2c-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.2 1.2a11 11 0 0 1 5.8 0c2.2-1.5 3.2-1.2 3.2-1.2.6 1.6.2 2.8.1 3.1a4.7 4.7 0 0 1 1.2 3.2c0 4.7-2.7 5.7-5.4 6 .4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A12 12 0 0 0 12 .3z" />
    </svg>
  );
}
