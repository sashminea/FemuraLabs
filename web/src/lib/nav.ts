export type NavLink = { name: string; href: string };

export const marketingNav: NavLink[] = [
  { name: "Pipeline", href: "/#pipeline" },
  { name: "Models", href: "/#bento" },
  { name: "Results", href: "/#proof" },
  { name: "CLI", href: "/#cli" },
];

export const docsNav: NavLink[] = [
  { name: "Overview", href: "/docs" },
  { name: "Quickstart", href: "/docs/quickstart" },
  { name: "CLI", href: "/docs/cli" },
  { name: "Architecture", href: "/docs/architecture" },
  { name: "Validation", href: "/docs/validation" },
];
