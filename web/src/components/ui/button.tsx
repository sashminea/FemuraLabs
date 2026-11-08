import Link from "next/link";
import type { ReactNode } from "react";

type Variant = "primary" | "ghost";
type Size = "sm" | "md";

const variants: Record<Variant, string> = {
  primary: "bg-tx text-bg hover:bg-white",
  ghost:
    "bg-white/[0.04] border border-line2 backdrop-blur-md hover:bg-tx hover:text-bg",
};

const sizes: Record<Size, string> = {
  sm: "h-[38px] px-4 text-sm",
  md: "h-12 px-6 text-[15px]",
};

export function Button({
  href,
  variant = "primary",
  size = "md",
  children,
  external,
  onClick,
}: {
  href?: string;
  variant?: Variant;
  size?: Size;
  children: ReactNode;
  external?: boolean;
  onClick?: () => void;
}) {
  const cls = `group inline-flex items-center justify-center rounded-full font-medium whitespace-nowrap transition-colors duration-300 ${variants[variant]} ${sizes[size]}`;

  const inner = (
    <span className="relative block overflow-hidden h-[1.2em] leading-[1.2em]">
      <span className="block transition-transform duration-300 group-hover:-translate-y-full">
        {children}
      </span>
      <span
        aria-hidden
        className="absolute left-0 top-0 block translate-y-full transition-transform duration-300 group-hover:translate-y-0"
      >
        {children}
      </span>
    </span>
  );

  if (href) {
    if (external) {
      return (
        <a
          href={href}
          target="_blank"
          rel="noreferrer"
          className={cls}
        >
          {inner}
        </a>
      );
    }
    return (
      <Link href={href} className={cls}>
        {inner}
      </Link>
    );
  }
  return (
    <button type="button" onClick={onClick} className={cls}>
      {inner}
    </button>
  );
}
