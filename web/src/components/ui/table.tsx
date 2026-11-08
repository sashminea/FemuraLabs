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
    <div className="mt-6 overflow-x-auto rounded-[20px] border border-line bg-white/[0.03] px-4 py-2.5 backdrop-blur-md [scrollbar-width:thin] [scrollbar-color:rgba(255,255,255,0.2)_transparent] sm:px-5 sm:py-3.5 [&::-webkit-scrollbar]:h-1 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:rounded-sm [&::-webkit-scrollbar-thumb]:bg-white/20">
      <table className="w-full min-w-[420px] border-collapse sm:min-w-[480px]">
        <thead>
          <tr>
            {headers.map((h) => (
              <th
                key={h}
                className="whitespace-nowrap px-3 pt-3 pb-2.5 text-left font-mono text-[10px] font-medium uppercase tracking-[0.1em] text-dim first:pl-0 last:pr-0 sm:px-5 sm:pt-4 sm:pb-3.5 sm:text-[11px]"
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
                  className="px-3 py-3 align-top text-[13px] text-mut first:pl-0 last:pr-0 first:text-tx sm:px-5 sm:py-4 sm:text-[14.5px]"
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
