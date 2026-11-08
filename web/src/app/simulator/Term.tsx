"use client";

import { useState, useRef, useLayoutEffect, useId } from "react";
import { createPortal } from "react-dom";
import { GLOSSARY, GlossaryKey } from "./glossary";

/**
 * Glossary term with a hover/tap tooltip.
 * - default: dotted underline, opens on hover, focus or tap
 * - plain: no underline (for labels in dense lists)
 * - hoverOnly: opens on hover only and lets clicks pass through to a parent button
 */
export default function Term({
  term,
  children,
  plain,
  hoverOnly,
}: {
  term: GlossaryKey;
  children?: React.ReactNode;
  plain?: boolean;
  hoverOnly?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<{ x: number; y: number; flip: boolean } | null>(null);
  const [mounted, setMounted] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  const tipId = useId();

  useLayoutEffect(() => {
    setMounted(true);
  }, []);

  const computePos = () => {
    if (!ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const width = 320;
    const margin = 10;
    let x = r.left + r.width / 2 - width / 2;
    x = Math.max(margin, Math.min(window.innerWidth - width - margin, x));
    const above = r.top > 180;
    const y = above ? r.top - margin : r.bottom + margin;
    setPos({ x, y, flip: !above });
  };

  const show = () => {
    computePos();
    setOpen(true);
  };
  const hide = () => setOpen(false);

  return (
    <>
      <span
        ref={ref}
        onMouseEnter={show}
        onMouseLeave={hide}
        onClick={
          hoverOnly
            ? undefined
            : (e) => {
                e.stopPropagation();
                if (open) hide();
                else show();
              }
        }
        onFocus={hoverOnly ? undefined : show}
        onBlur={hoverOnly ? undefined : hide}
        tabIndex={hoverOnly ? undefined : 0}
        aria-describedby={open ? tipId : undefined}
        style={{
          borderBottom: plain ? "none" : "1px dotted rgba(77,163,255,.55)",
          cursor: hoverOnly ? "inherit" : "help",
          color: "inherit",
          outlineOffset: 2,
        }}
      >
        {children ?? term}
      </span>
      {mounted &&
        open &&
        pos &&
        createPortal(
          <div
            id={tipId}
            role="tooltip"
            style={{
              position: "fixed",
              left: pos.x,
              top: pos.y,
              transform: pos.flip ? "none" : "translateY(-100%)",
              width: 320,
              maxWidth: "calc(100vw - 20px)",
              padding: "12px 14px",
              background: "rgba(21,23,26,.98)",
              border: `1px solid var(--color-line2)`,
              borderRadius: 12,
              color: "rgba(236,235,230,.92)",
              fontFamily: "var(--font-sans)",
              fontSize: 12.5,
              lineHeight: 1.55,
              fontWeight: 400,
              letterSpacing: 0,
              textTransform: "none",
              textAlign: "left",
              zIndex: 9999,
              pointerEvents: "none",
              boxShadow: "0 12px 32px rgba(0,0,0,.7)",
              backdropFilter: "blur(14px)",
            }}
          >
            {GLOSSARY[term]}
          </div>,
          document.body
        )}
    </>
  );
}