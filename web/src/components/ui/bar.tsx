"use client";

import { useEffect, useRef, useState } from "react";

export function Bar({ width }: { width: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(width);
          io.unobserve(el);
        }
      },
      { threshold: 0.35 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [width]);

  return (
    <span ref={ref} className="block h-[3px] mt-2.5 rounded bg-white/[0.07] overflow-hidden">
      <span
        className="block h-full bg-gradient-to-r from-transparent to-blue transition-[width] duration-[1400ms] ease-out"
        style={{ width: `${visible}%` }}
      />
    </span>
  );
}
