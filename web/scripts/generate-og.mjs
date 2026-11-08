// Generates one 1200x630 PNG per page into public/og/.
// Left-aligned like the landing hero. Subtle 5% gradient on the right edge,
// compact terminal strip below the description.

import { createElement as h } from "react";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(__dirname, "..", "public", "og");

const FONTS = [
  {
    name: "Inter",
    weight: 400,
    url: "https://cdn.jsdelivr.net/fontsource/fonts/inter@latest/latin-400-normal.woff",
  },
  {
    name: "Inter",
    weight: 600,
    url: "https://cdn.jsdelivr.net/fontsource/fonts/inter@latest/latin-600-normal.woff",
  },
  {
    name: "JetBrains Mono",
    weight: 400,
    url: "https://cdn.jsdelivr.net/fontsource/fonts/jetbrains-mono@latest/latin-400-normal.woff",
  },
];

const CARDS = {
  landing: {
    title: "Lower-limb CT, measured automatically.",
    description: "Segmentation, meshes and alignment angles from one command.",
    command: "femuralabs ml infer --ct scan.nii",
    output: "✓ combined_seg.nii written",
  },
  docs: {
    title: "FemuraLabs documentation",
    description: "An open-source Python CLI and ML pipeline for lower-limb CT.",
    command: "femuralabs --help",
  },
  quickstart: {
    title: "Quickstart",
    description:
      "Install FemuraLabs, run SegResNet inference and the geometry pipeline.",
    command: "femuralabs doctor check",
  },
  cli: {
    title: "CLI reference",
    description: "Every femuralabs command, flag and default.",
    command: "femuralabs pipeline run --angles",
  },
  architecture: {
    title: "How it works",
    description:
      "SegResNet segmentation, mesh extraction, geometry rules and angles.",
    command: "femuralabs pipeline run --fill",
  },
  validation: {
    title: "Validation report",
    description:
      "Dice, landmark errors and HKA, mLDFA, MPTA angle errors on 8 subjects.",
    command: "femuralabs pipeline report",
  },
};

async function loadFont(url, retries = 3) {
  for (let i = 0; i <= retries; i++) {
    try {
      const res = await fetch(url);
      if (res.ok) return Buffer.from(await res.arrayBuffer());
      if (i < retries) await new Promise((r) => setTimeout(r, 500 * (i + 1)));
    } catch {
      if (i === retries) throw new Error(`Failed to load font: ${url}`);
    }
  }
  throw new Error(`Failed to load font: ${url}`);
}

function renderCard(card) {
  const terminalLines = [
    h(
      "div",
      { style: { display: "flex" }, key: "cmd" },
      h("span", { style: { color: "#10b981" } }, "$ "),
      h("span", { style: { color: "#ecebe6" } }, card.command),
    ),
  ];
  if (card.output) {
    terminalLines.push(
      h(
        "div",
        {
          style: { display: "flex", color: "rgba(236,235,230,0.38)" },
          key: "out",
        },
        card.output,
      ),
    );
  }

  return h(
    "div",
    {
      style: {
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        padding: "64px 72px",
        backgroundColor: "#0a0a0a",
        // Subtle 5% gradient anchored to the right edge
        backgroundImage:
          "radial-gradient(ellipse at 100% 50%, rgba(77,163,255,0.05), rgba(10,10,10,0) 55%)",
        color: "#ecebe6",
        fontFamily: "Inter",
      },
    },
    // Brand top-left
    h(
      "div",
      {
        style: {
          display: "flex",
          fontSize: 28,
          fontWeight: 600,
          letterSpacing: "-0.03em",
        },
      },
      "FemuraLabs",
    ),
    // Left-aligned hero content, flex-grow to push footer down
    h(
      "div",
      {
        style: {
          display: "flex",
          flex: 1,
          flexDirection: "column",
          justifyContent: "center",
        },
      },
      h(
        "div",
        {
          style: {
            fontSize: 76,
            fontWeight: 600,
            lineHeight: 1.04,
            letterSpacing: "-0.05em",
            maxWidth: 880,
          },
        },
        card.title,
      ),
      h(
        "div",
        {
          style: {
            marginTop: 24,
            fontSize: 26,
            fontWeight: 400,
            lineHeight: 1.4,
            color: "rgba(236,235,230,0.6)",
            maxWidth: 720,
          },
        },
        card.description,
      ),
      // Compact terminal strip, left-aligned, shrinks to content width
      h(
        "div",
        {
          style: {
            marginTop: 36,
            alignSelf: "flex-start",
            display: "flex",
            flexDirection: "column",
            gap: 4,
            padding: "16px 22px",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.08)",
            backgroundColor: "rgba(7,8,9,0.85)",
            fontFamily: "JetBrains Mono",
            fontSize: 18,
            lineHeight: 1.6,
          },
        },
        ...terminalLines,
      ),
    ),
    // Footer
    h(
      "div",
      {
        style: {
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: 18,
          fontWeight: 400,
          color: "rgba(236,235,230,0.38)",
          letterSpacing: "0.02em",
        },
      },
      h("div", { style: { display: "flex" } }, "sashminea.github.io/FemuraLabs"),
      h("div", { style: { display: "flex", color: "#4da3ff" } }, "→"),
    ),
  );
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });

  console.log("Loading fonts (Inter + JetBrains Mono)…");
  const fonts = await Promise.all(
    FONTS.map(async (f) => ({
      name: f.name,
      weight: f.weight,
      style: "normal",
      data: await loadFont(f.url),
    })),
  );

  for (const [slug, card] of Object.entries(CARDS)) {
    const svg = await satori(renderCard(card), {
      width: 1200,
      height: 630,
      fonts,
    });
    const png = new Resvg(svg).render().asPng();
    const out = join(OUT_DIR, `${slug}.png`);
    await writeFile(out, png);
    console.log(
      `  wrote public/og/${slug}.png (${(png.byteLength / 1024).toFixed(1)} KB)`,
    );
  }

  console.log("Done.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
