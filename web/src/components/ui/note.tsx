import type { ReactNode } from "react";

export function Note({
  children,
  warn = false,
}: {
  children: ReactNode;
  warn?: boolean;
}) {
  const base =
    "mt-6 rounded-xl border bg-s1 px-5 py-3.5 text-[14.5px] leading-relaxed";
  const cls = warn
    ? `${base} border-[rgba(255,214,140,0.25)] text-amber`
    : `${base} border-line text-mut`;
  return <div className={cls}>{children}</div>;
}
