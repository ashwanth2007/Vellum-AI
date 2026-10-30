import React, { useState } from 'react';
import {
  Shield,
  UploadCloud,
  FileSearch,
  Grid3x3,
  Layers,
  Eye,
  ScanText,
  GitBranch,
  Menu,
  X,
  BookOpen,
} from 'lucide-react';

interface AppLayoutProps {
  currentScreen: string;
  onNavigate: (screen: string) => void;
  children: React.ReactNode;
}

type NavItem = { id: string; label: string; icon: React.ElementType; hint?: string };

const NAV_GROUPS: { title: string; items: NavItem[] }[] = [
  {
    title: 'Start here',
    items: [{ id: 'handbook', label: 'Handbook', icon: BookOpen }],
  },
  {
    title: 'Prototype',
    items: [
      { id: 'upload', label: 'Upload', icon: UploadCloud },
      { id: 'result', label: 'Result', icon: FileSearch },
    ],
  },
  {
    title: 'How the ML works',
    items: [
      { id: 'learn-foundations', label: 'Foundations', icon: Grid3x3 },
      { id: 'learn-cnn', label: 'EfficientNet-B0 CNN', icon: Layers },
      { id: 'learn-clip', label: 'CLIP ViT-B/32', icon: Eye },
      { id: 'learn-text', label: 'OCR + text model', icon: ScanText },
      { id: 'learn-cascade', label: 'How one model is picked', icon: GitBranch },
    ],
  },
];

export const AppLayout: React.FC<AppLayoutProps> = ({ currentScreen, onNavigate, children }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  // the processing screen belongs to the upload flow
  const activeId = currentScreen === 'processing' ? 'upload' : currentScreen;

  const go = (id: string) => {
    onNavigate(id);
    setDrawerOpen(false);
    window.scrollTo({ top: 0 });
  };

  const nav = (
    <nav className="flex flex-col gap-6" aria-label="Main">
      {NAV_GROUPS.map((g) => (
        <div key={g.title} className="space-y-1">
          <div className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">{g.title}</div>
          {g.items.map((item) => {
            const Icon = item.icon;
            const active = activeId === item.id;
            return (
              <button
                key={item.id}
                onClick={() => go(item.id)}
                aria-current={active ? 'page' : undefined}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-left text-sm transition-colors duration-200 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 ${
                  active ? 'bg-zinc-900 text-white' : 'text-zinc-700 hover:bg-white hover:text-zinc-950'
                }`}
              >
                <Icon className={`h-4 w-4 shrink-0 ${active ? 'text-white' : 'text-zinc-500'}`} />
                <span className="min-w-0">
                  <span className="block font-medium leading-tight truncate">{item.label}</span>
                  {item.hint && (
                    <span className={`block text-[11px] leading-tight truncate ${active ? 'text-zinc-300' : 'text-zinc-500'}`}>{item.hint}</span>
                  )}
                </span>
              </button>
            );
          })}
        </div>
      ))}
    </nav>
  );

  const brand = (
    <button onClick={() => go('upload')} className="flex items-center gap-2.5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 rounded-xl">
      <span className="h-8 w-8 rounded-xl bg-zinc-900 flex items-center justify-center text-white">
        <Shield className="h-4 w-4" />
      </span>
      <span className="text-lg font-semibold tracking-tight text-zinc-950">Vellum</span>
    </button>
  );

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-zinc-900">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-64 flex-col border-r border-zinc-200/80 bg-[#F6F3EE] px-4 py-5 gap-8 overflow-y-auto">
        {brand}
        {nav}
        <div className="mt-auto px-3 text-[11px] leading-relaxed text-zinc-500">
          BCSE306L Artificial Intelligence course project. Document type classification with three models.
        </div>
      </aside>

      {/* Mobile and tablet top bar */}
      <header className="lg:hidden sticky top-0 z-40 flex items-center justify-between h-14 px-4 border-b border-zinc-200/80 bg-[#FAF8F5]/95 backdrop-blur">
        {brand}
        <button
          onClick={() => setDrawerOpen(true)}
          aria-label="Open menu"
          className="h-10 w-10 flex items-center justify-center rounded-xl text-zinc-700 hover:bg-white cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900"
        >
          <Menu className="h-5 w-5" />
        </button>
      </header>

      {drawerOpen && (
        <div className="lg:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-zinc-900/30" onClick={() => setDrawerOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 max-w-[85vw] bg-[#F6F3EE] px-4 py-5 flex flex-col gap-8 overflow-y-auto shadow-xl">
            <div className="flex items-center justify-between">
              {brand}
              <button
                onClick={() => setDrawerOpen(false)}
                aria-label="Close menu"
                className="h-10 w-10 flex items-center justify-center rounded-xl text-zinc-700 hover:bg-white cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            {nav}
          </aside>
        </div>
      )}

      <main className="lg:pl-64 min-w-0 overflow-x-hidden">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">{children}</div>
      </main>
    </div>
  );
};
