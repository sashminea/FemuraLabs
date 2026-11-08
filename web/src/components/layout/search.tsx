"use client";

import { Command } from "cmdk";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { searchGroups } from "@/lib/docs";

export function Search() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
        return;
      }
      if (e.key === "Escape" && open) {
        e.preventDefault();
        setOpen(false);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const original = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = original;
    };
  }, [open]);

  const onSelect = (href: string) => {
    setOpen(false);
    router.push(href);
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open search"
        className="inline-flex h-9 items-center justify-center rounded-full border border-line bg-white/[0.03] text-mut transition-colors hover:border-line2 hover:text-tx md:h-10 md:gap-2.5 md:pl-3.5 md:pr-1.5"
        style={{ width: "auto" }}
      >
        <span className="grid h-9 w-9 place-items-center md:h-auto md:w-auto">
          <SearchIcon />
        </span>
        <span className="hidden text-sm md:inline">Search</span>
        <kbd className="hidden h-6 items-center rounded-md border border-line bg-white/5 px-1.5 font-mono text-[10px] uppercase tracking-widest text-dim mx-2 md:inline-flex">
          ⌘K
        </kbd>
      </button>

      {open && (
        <div
          className="fixed inset-0 z-[100] flex items-start justify-center px-4 pt-[12vh]"
          onClick={() => setOpen(false)}
        >
          <div className="absolute inset-0 bg-bg/80 backdrop-blur-sm" />
          <Command
            onClick={(e) => e.stopPropagation()}
            className="relative w-full max-w-lg overflow-hidden rounded-2xl border border-line bg-s1 shadow-[0_24px_64px_rgba(0,0,0,0.6)]"
          >
            <div className="flex items-center gap-3 border-b border-line px-4">
              <span className="text-dim">
                <SearchIcon />
              </span>
              <Command.Input
                autoFocus
                placeholder="Search documentation..."
                className="h-14 flex-1 bg-transparent text-[15px] text-tx outline-none placeholder:text-dim"
              />
              <kbd className="inline-flex h-6 items-center rounded border border-line bg-white/5 px-1.5 font-mono text-[10px] uppercase tracking-widest text-dim">
                esc
              </kbd>
            </div>

            <Command.List className="max-h-[420px] overflow-y-auto p-2 [scrollbar-width:thin] [scrollbar-color:rgba(255,255,255,0.2)_transparent] [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:rounded-sm [&::-webkit-scrollbar-thumb]:bg-white/20">
              <Command.Empty className="px-4 py-8 text-center text-[13.5px] text-mut">
                No results found.
              </Command.Empty>

              {searchGroups.map((group) => (
                <Command.Group
                  key={group.title}
                  heading={group.title}
                  className="mb-1 [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:pb-1.5 [&_[cmdk-group-heading]]:pt-3 [&_[cmdk-group-heading]]:font-mono [&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-[0.1em] [&_[cmdk-group-heading]]:text-dim"
                >
                  {group.items.map((item) => (
                    <Command.Item
                      key={item.href}
                      value={`${item.title} ${item.parent ?? ""} ${item.group}`}
                      onSelect={() => onSelect(item.href)}
                      className="flex cursor-pointer items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-[14px] text-mut transition-colors aria-selected:bg-white/[0.06] aria-selected:text-tx hover:bg-white/[0.04]"
                    >
                      <span>{item.title}</span>
                      {item.parent && (
                        <span className="font-mono text-[11px] text-dim">
                          {item.parent}
                        </span>
                      )}
                    </Command.Item>
                  ))}
                </Command.Group>
              ))}
            </Command.List>

            <div className="flex items-center justify-between gap-3 border-t border-line px-4 py-2.5 font-mono text-[10px] uppercase tracking-widest text-dim">
              <span className="flex items-center gap-3">
                <span>
                  <span className="mr-1">↑↓</span>
                  navigate
                </span>
                <span>
                  <span className="mr-1">↵</span>
                  select
                </span>
              </span>
              <span>
                <span className="mr-1">esc</span>
                close
              </span>
            </div>
          </Command>
        </div>
      )}
    </>
  );
}

function SearchIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
    >
      <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.4" />
      <path
        d="M11 11L14 14"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}
