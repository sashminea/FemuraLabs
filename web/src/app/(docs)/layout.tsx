import { DocsSidebar } from "@/components/layout/docs-sidebar";

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-1 px-6 pt-16">
      <DocsSidebar />
      <main className="min-w-0 flex-1 py-12 pl-6 md:pl-12">
        {children}
      </main>
    </div>
  );
}
