import { DocsSidebar } from "@/components/layout/docs-sidebar";

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-1 px-4 pt-16 sm:px-6">
      <DocsSidebar />
      <main className="min-w-0 flex-1 py-8 sm:py-12 md:pl-12">
        {children}
      </main>
    </div>
  );
}
