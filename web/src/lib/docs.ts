export type DocsGroup = {
  title: string;
  items: { title: string; href: string }[];
};

export const docsConfig: DocsGroup[] = [
  {
    title: "Getting Started",
    items: [
      { title: "Overview", href: "/docs" },
      { title: "Quickstart", href: "/docs/quickstart" },
    ],
  },
  {
    title: "Reference",
    items: [
      { title: "CLI", href: "/docs/cli" },
      { title: "Architecture", href: "/docs/architecture" },
    ],
  },
  {
    title: "Validation",
    items: [{ title: "Validation Report", href: "/docs/validation" }],
  },
];
