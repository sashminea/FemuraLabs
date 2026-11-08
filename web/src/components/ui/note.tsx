import type { ReactNode } from "react";

export function Note({
  children,
  warn = false,
}: {
  children: ReactNode;
  warn?: boolean;
}) {
  const base =
    "mt-6 rounded-xl border bg-s1 px-4 py-3 text-[13.5px] leading-relaxed sm:px-5 sm:py-3.5 sm:text-[14.5px]";
  const cls = warn
    ? `${base} border-[rgba(255,214,140,0.25)] text-amber`
    : `${base} border-line text-mut`;
  return <div className={cls}>{children}</div>;
}
