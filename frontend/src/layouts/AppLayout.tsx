import { ReactNode } from 'react';
import Sidebar from '../components/Sidebar';

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-full bg-[#080d17] text-slate-100">
      <div className="flex min-h-[calc(100vh-4rem)]">
        <Sidebar />
        <main className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-5xl space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
