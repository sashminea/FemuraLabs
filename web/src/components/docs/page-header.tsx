export function PageHeader({
  crumb,
  title,
  lead,
}: {
  crumb: string;
  title: string;
  lead: string;
}) {
  return (
    <header>
      <span className="font-mono text-[11px] uppercase tracking-[0.1em] text-dim">
        {crumb}
      </span>
      <h1 className="mt-5 text-[clamp(2.4rem,5.4vw,4.2rem)] font-medium leading-none tracking-[-0.065em]">
        {title}
      </h1>
      <p className="mt-6 max-w-[56ch] text-[clamp(1rem,1.4vw,1.2rem)] leading-relaxed text-mut">
        {lead}
      </p>
    </header>
  );
}
