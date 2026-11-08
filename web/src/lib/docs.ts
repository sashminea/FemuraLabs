export type DocsAnchor = {
  title: string;
  href: string;
};

export type DocsPage = {
  title: string;
  href: string;
  anchors: DocsAnchor[];
};

export type DocsGroup = {
  title: string;
  items: DocsPage[];
};

export const docsConfig: DocsGroup[] = [
  {
    title: "Getting Started",
    items: [
      {
        title: "Overview",
        href: "/docs",
        anchors: [
          { title: "What it does", href: "/docs#what" },
          { title: "Command groups", href: "/docs#commands" },
          { title: "Before you rely on it", href: "/docs#limits" },
        ],
      },
      {
        title: "Quickstart",
        href: "/docs/quickstart",
        anchors: [
          { title: "Install", href: "/docs/quickstart#install" },
          { title: "Run inference", href: "/docs/quickstart#infer" },
          { title: "Run the geometry pipeline", href: "/docs/quickstart#geometry" },
          { title: "Read the outputs", href: "/docs/quickstart#outputs" },
          { title: "Reproduce from the dataset", href: "/docs/quickstart#reproduce" },
        ],
      },
    ],
  },
  {
    title: "Reference",
    items: [
      {
        title: "CLI",
        href: "/docs/cli",
        anchors: [
          { title: "doctor", href: "/docs/cli#doctor" },
          { title: "data", href: "/docs/cli#data" },
          { title: "pipeline", href: "/docs/cli#pipeline" },
          { title: "ml", href: "/docs/cli#ml" },
          { title: "volume", href: "/docs/cli#volume" },
          { title: "version", href: "/docs/cli#version" },
        ],
      },
      {
        title: "Architecture",
        href: "/docs/architecture",
        anchors: [
          { title: "Pipeline flow", href: "/docs/architecture#flow" },
          { title: "Coordinate frame", href: "/docs/architecture#frame" },
          { title: "SegResNet", href: "/docs/architecture#model" },
          { title: "Geometry rules", href: "/docs/architecture#geometry" },
          { title: "Angles", href: "/docs/architecture#angles" },
        ],
      },
      {
        title: "Simulator",
        href: "/docs/simulator",
        anchors: [
          { title: "What it models", href: "/docs/simulator#what" },
          { title: "Controls", href: "/docs/simulator#controls" },
          { title: "Reading the results", href: "/docs/simulator#results" },
          { title: "Layers and the 3D view", href: "/docs/simulator#layers" },
          { title: "Explainer", href: "/docs/simulator#explainer" },
          { title: "Case data", href: "/docs/simulator#case" },
          { title: "What it does not model", href: "/docs/simulator#limits" },
        ],
      },
    ],
  },
  {
    title: "Validation",
    items: [
      {
        title: "Validation Report",
        href: "/docs/validation",
        anchors: [
          { title: "Segmentation", href: "/docs/validation#seg" },
          { title: "Landmarks", href: "/docs/validation#landmarks" },
          { title: "Angles", href: "/docs/validation#angles" },
          { title: "Baseline", href: "/docs/validation#baseline" },
          { title: "Limitations", href: "/docs/validation#limits" },
        ],
      },
    ],
  },
];

/** Ordered flat list — used by prev/next pager. */
export const docsFlat = docsConfig.flatMap((group) =>
  group.items.map((page) => ({
    title: page.title,
    href: page.href,
    section: group.title,
  })),
);

/** Search index — pages plus their in-page anchors. */
export type SearchItem = {
  title: string;
  href: string;
  group: string;
  parent?: string;
};

export const searchGroups: { title: string; items: SearchItem[] }[] =
  docsConfig.map((group) => ({
    title: group.title,
    items: group.items.flatMap((page): SearchItem[] => [
      { title: page.title, href: page.href, group: group.title },
      ...page.anchors.map((a) => ({
        title: a.title,
        href: a.href,
        group: group.title,
        parent: page.title,
      })),
    ]),
  }));
