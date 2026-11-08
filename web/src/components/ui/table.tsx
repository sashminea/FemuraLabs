import type { ReactNode } from "react";

export type TableRow = {
  cells: ReactNode[];
  total?: boolean;
};

export function Table({
  headers,
  rows,
}: {
  headers: string[];
  rows: TableRow[];
}) {
  return (
    <div className="mt-6 overflow-x-auto rounded-[20px] border border-line bg-white/[0.03] px-5 py-3.5 backdrop-blur-md">
      <table className="w-full min-w-[480px] border-collapse">
        <thead>
          <tr>
            {headers.map((h) => (
              <th
                key={h}
                className="whitespace-nowrap px-5 pt-4 pb-3.5 text-left font-mono text-[11px] font-medium uppercase tracking-[0.1em] text-dim first:pl-0 last:pr-0"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className={
                row.total ? "border-t-2 border-line2" : "border-t border-line"
              }
            >
              {row.cells.map((cell, j) => (
                <td
                  key={j}
                  className="px-5 py-4 align-top text-[14.5px] text-mut first:pl-0 last:pr-0 first:text-tx"
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
