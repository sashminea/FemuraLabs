import { withOg } from "@/lib/og";
import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/docs/page-header";
import { Note } from "@/components/ui/note";
import { Table } from "@/components/ui/table";
import { site } from "@/lib/site";

export const metadata = withOg(
  "docs",
  "Documentation",
  "Documentation for FemuraLabs, an open-source lower-limb CT analysis CLI and ML pipeline.",
);

const CARD_LINKS = [
  {
    href: "/docs/quickstart",
    mono: "Start here",
    title: "Installation",
    desc: "Set up the CLI and check your environment.",
    external: false,
  },
  {
    href: "/docs/cli",
    mono: "Reference",
    title: "CLI reference",
    desc: "Every command, flag and default.",
    external: false,
  },
  {
    href: site.github,
    mono: "Source",
    title: "GitHub",
    desc: "Code, issues, releases and the Dockerfile.",
    external: true,
  },
];

const COMMANDS: [string, string][] = [
  ["doctor", "Check dependencies, GPU and environment."],
  ["data", "Dataset inventory, segmentation merging and full-body preprocessing."],
  ["pipeline", "Meshes, landmarks, angles and report tables."],
  ["ml", "Weights, dataset preparation, training, validation, inference and cross-validation."],
  ["volume", "Volume geometry and synthetic data."],
];

export default function DocsOverviewPage() {
  return (
    <article className="prose-docs max-w-3xl">
      <PageHeader
        crumb="Getting started"
        title="FemuraLabs documentation"
        lead="An open-source Python CLI and ML pipeline for lower-limb CT. Go from a CT volume to bone masks, 3D meshes, joint centres and alignment angles with one tool."
      />

      <div className="mt-12 grid gap-4 md:grid-cols-3">
        {CARD_LINKS.map((c) => {
          const cls =
            "flex flex-col rounded-[20px] border border-line bg-s1 p-6 transition-colors hover:border-line2 hover:bg-s2";
          const inner = (
            <>
              <span className="font-mono text-[11px] uppercase tracking-[0.1em] text-dim">
                {c.mono}
              </span>
              <h3 className="!mt-4 mb-2 text-[1.3rem] font-medium">{c.title}</h3>
              <p className="text-[15px] text-mut">{c.desc}</p>
            </>
          );
          return c.external ? (
            <a key={c.title} href={c.href} target="_blank" rel="noreferrer" className={cls}>
              {inner}
            </a>
          ) : (
            <Link key={c.title} href={c.href} className={cls}>
              {inner}
            </Link>
          );
        })}
      </div>

      <h2 id="what">What it does</h2>
      <p>
        Limb alignment is usually measured by clicking points on images by hand, which is slow and varies from person to person. FemuraLabs automates the geometric part. It rebuilds the femur, tibia, fibula and talus as watertight 3D surfaces, finds the hip, knee and ankle centres from the shape of those surfaces, and computes the mechanical axes and the angles a surgeon asks for.
      </p>
      <p>
        Every automatic result can be compared against landmarks placed by hand, so you can see how close the rules get to a person. The{" "}
        <Link href="/docs/validation" className="l">
          validation report
        </Link>{" "}
        shows the numbers.
      </p>

      <h2 id="commands">Command groups</h2>
      <p>
        The <code>femuralabs</code> command is split into five groups plus{" "}
        <code>version</code>.
      </p>
      <Table
        headers={["Group", "What it does"]}
        rows={COMMANDS.map(([cmd, desc]) => ({
          cells: [<code key={cmd}>{cmd}</code>, desc],
        }))}
      />
      <p>
        The{" "}
        <Link href="/docs/cli" className="l">
          CLI reference
        </Link>{" "}
        lists the flags for each command.
      </p>

      <h2 id="limits">Before you rely on it</h2>
      <Note warn>
        <p>Research prototype. Not for clinical use or diagnosis.</p>
      </Note>
      <ul>
        <li>
          Evaluated on <b>eight cadaveric subjects</b> with a single annotator, so results are descriptive.
        </li>
        <li>Scans are post-mortem and supine, which differs from a standing, weight-bearing patient.</li>
        <li>The model has not been tested on external hospital data.</li>
      </ul>
      <p>
        The full list is on the{" "}
        <Link href="/docs/validation#limits" className="l">
          validation page
        </Link>
        .
      </p>
    </article>
  );
}
