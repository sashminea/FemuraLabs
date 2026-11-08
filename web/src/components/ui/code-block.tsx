"use client";

import { useEffect, useRef, useState } from "react";

export function CodeBlock({
  code,
  language = "bash",
}: {
  code: string;
  language?: string;
}) {
  const [copied, setCopied] = useState(false);
  const [overflow, setOverflow] = useState(false);
  const preRef = useRef<HTMLPreElement>(null);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  useEffect(() => {
    const el = preRef.current;
    if (!el) return;
    const check = () => setOverflow(el.scrollWidth > el.clientWidth + 1);
    check();
    const io = new ResizeObserver(check);
    io.observe(el);
    return () => io.disconnect();
  }, [code]);

  return (
    <div className="mt-4 overflow-hidden rounded-2xl border border-line bg-[rgba(7,8,9,0.8)] backdrop-blur-md">
      <div className="flex items-center gap-1.5 border-b border-line px-3 py-2 sm:px-3.5 sm:py-2.5">
        <span className="h-2 w-2 rounded-full bg-white/[0.12]" />
        <span className="h-2 w-2 rounded-full bg-white/[0.12]" />
        <span className="h-2 w-2 rounded-full bg-white/[0.12]" />
        <span className="ml-2.5 font-mono text-[10px] uppercase tracking-[0.1em] text-dim sm:text-[11px]">
          {language}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          className="ml-auto rounded-lg border border-line bg-white/5 px-2 py-1 font-mono text-[10px] uppercase tracking-[0.08em] text-mut transition-colors hover:bg-white/10 hover:text-tx sm:px-2.5 sm:py-1.5 sm:text-[11px]"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <div className="relative">
        <pre
          ref={preRef}
          className="overflow-x-auto px-3 py-3 font-mono text-[11.5px] leading-[1.65] text-tx [scrollbar-width:thin] [scrollbar-color:rgba(255,255,255,0.2)_transparent] sm:px-5 sm:py-4 sm:text-[13.5px] sm:leading-[1.7] [&::-webkit-scrollbar]:h-1 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:rounded-sm [&::-webkit-scrollbar-thumb]:bg-white/20"
        >
          <code>{code}</code>
        </pre>
        {overflow && (
          <div
            aria-hidden
            className="pointer-events-none absolute inset-y-0 right-0 w-6 bg-gradient-to-l from-[rgba(7,8,9,0.95)] to-transparent"
          />
        )}
      </div>
    </div>
  );
}
