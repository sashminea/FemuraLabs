import type { ReactNode } from "react";

import { CodeBlock } from "@/components/ui/code-block";
import { Table } from "@/components/ui/table";

export type FlagRow = {
  flag: string;
  default?: string;
  description: string;
  required?: boolean;
};

export function CommandBlock({
  name,
  subcommand,
  description,
  example,
  flags,
  extra,
}: {
  name: string;
  subcommand?: string;
  description: string;
  example?: string;
  flags?: FlagRow[];
  extra?: ReactNode;
}) {
  const id = subcommand ? `${name}-${subcommand}` : name;
  return (
    <div id={id} className="mt-14 border-t border-line pt-7">
      <h3 className="!mt-0 font-mono text-[1.2rem] font-medium leading-tight tracking-[-0.02em]">
        femuralabs {name}
        {subcommand && (
          <span className="ml-2 text-dim">{subcommand}</span>
        )}
      </h3>
      <p className="mt-2 text-[14.5px] text-mut">{description}</p>
      {example && <CodeBlock language="bash" code={example} />}
      {flags && flags.length > 0 && (
        <Table
          headers={["Flag", "Default", "Description"]}
          rows={flags.map((f) => ({
            cells: [
              <>
                <code>{f.flag}</code>
                {f.required && (
                  <span className="ml-2 inline-block rounded-full border border-[rgba(255,214,140,0.3)] px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-amber">
                    required
                  </span>
                )}
              </>,
              f.default ?? "",
              f.description,
            ],
          }))}
        />
      )}
      {extra}
    </div>
  );
}
