'use client';

import { useState } from "react";

export function CodeBlock({
  code,
  language = "bash",
}: {
  code: string;
  language?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="mt-4 overflow-hidden rounded-2xl border border-line bg-[rgba(7,8,9,0.8)] backdrop-blur-md">
      <div className="flex items-center gap-1.5 border-b border-line px-3.5 py-2.5">
        <span className="h-2 w-2 rounded-full bg-white/[0.12]" />
        <span className="h-2 w-2 rounded-full bg-white/[0.12]" />
        <span className="h-2 w-2 rounded-full bg-white/[0.12]" />
        <span className="ml-2.5 font-mono text-[11px] uppercase tracking-[0.1em] text-dim">
          {language}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          className="ml-auto rounded-lg border border-line bg-white/5 px-2.5 py-1.5 font-mono text-[11px] uppercase tracking-[0.08em] text-mut transition-colors hover:bg-white/10 hover:text-tx"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto px-5 py-4 font-mono text-[13.5px] leading-[1.7] text-tx">
        <code>{code}</code>
      </pre>
    </div>
  );
}
