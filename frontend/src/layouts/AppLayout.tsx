import React, { useState, useEffect } from 'react';
import {
  Shield,
  LayoutDashboard,
  FileCheck2,
  UploadCloud,
  FileSearch,
  History,
  Lock,
  BarChart3,
  Sliders,
  LogOut,
  Command,
  CheckCircle2,
  ChevronDown,
  Type,
  Sparkles,
} from 'lucide-react';
import { Badge, KbdBadge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { UserProfile } from '../types';

interface AppLayoutProps {
  currentScreen: string;
  onNavigate: (screen: string) => void;
  currentUser: UserProfile;
  onSwitchUser: (user: UserProfile) => void;
  onLogout: () => void;
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  currentScreen,
  onNavigate,
  currentUser,
  onSwitchUser,
  onLogout,
  children,
}) => {
  const [showShortcutsModal, setShowShortcutsModal] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showFontMenu, setShowFontMenu] = useState(false);
  const [fontPreset, setFontPreset] = useState<string>('clarvos');

  const fontOptions = [
    { id: 'clarvos', name: 'Instrument Serif (Clarvos)', desc: 'High-contrast luxury editorial' },
    { id: 'newsreader', name: 'Newsreader (Academic)', desc: 'Literary & archival proportion' },
    { id: 'cormorant', name: 'Cormorant (Vogue Editorial)', desc: 'Classical high-fashion hairline' },
    { id: 'fraunces', name: 'Fraunces (Warm Contemporary)', desc: 'Organic soft-serif luxury' },
  ];

  useEffect(() => {
    document.documentElement.setAttribute('data-font-preset', fontPreset);
  }, [fontPreset]);

  const navItems = [
    { id: 'upload', label: 'Intake', icon: UploadCloud },
    { id: 'result', label: 'Result', icon: FileSearch },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'workspace', label: 'Workspace', icon: Shield, badge: 'Live' },
    { id: 'history', label: 'History', icon: History },
    { id: 'audit', label: 'Audit', icon: Lock },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Sliders },
  ];

  const availablePersonas: UserProfile[] = [
    {
      id: 'usr-810',
      name: 'Dr. Sarah Jenkins',
      email: 'lead.forensics@vellum.security',
      role: 'Senior Fraud Investigator',
      department: 'Forensic Review Unit',
      avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80',
    },
    {
      id: 'usr-441',
      name: 'Arun Kumar',
      email: 'arun.officer@apex-admissions.edu',
      role: 'Admissions Reviewer',
      department: 'Undergraduate Admissions',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    },
    {
      id: 'usr-001',
      name: 'Alex Rivera',
      email: 'admin@vellum.internal',
      role: 'Platform Admin',
      department: 'Infrastructure & AI',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
    },
  ];

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-zinc-900 flex flex-col selection:bg-zinc-900 selection:text-white bg-subtle-mesh">
      {/* Floating Layered Header */}
      <header className="sticky top-0 z-40 w-full border-b border-zinc-200/80 bg-[#FAF8F5]/90 backdrop-blur-xl shadow-[0_4px_24px_-4px_rgba(28,25,23,0.03)]">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between gap-4">
          {/* Brand Identity */}
          <div className="flex items-center gap-6 shrink-0">
            <div
              onClick={() => onNavigate('dashboard')}
              className="flex items-center gap-2.5 cursor-pointer group shrink-0"
            >
              <div className="h-8 w-8 rounded-xl bg-zinc-900 flex items-center justify-center text-white shadow-[0_2px_8px_rgba(0,0,0,0.15),inset_0_1px_0_rgba(255,255,255,0.2)] transition-transform group-hover:scale-105">
                <Shield className="h-4.5 w-4.5 text-zinc-100" />
              </div>
              <span className="font-serif text-2xl font-bold tracking-tight text-zinc-950 whitespace-nowrap">
                Vellum
              </span>
            </div>

            {/* Navigation Tabs with Tactile Depth */}
            <nav className="hidden md:flex items-center gap-1.5 p-1 rounded-full bg-zinc-200/40 border border-zinc-200/60 shadow-inner overflow-x-auto">
              {navItems.map((item) => {
                const isActive = currentScreen === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onNavigate(item.id)}
                    className={`px-3.5 py-1 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer select-none whitespace-nowrap ${
                      isActive
                        ? 'bg-zinc-900 text-white shadow-[0_2px_8px_rgba(0,0,0,0.15),inset_0_1px_0_rgba(255,255,255,0.15)] font-semibold'
                        : 'text-zinc-600 hover:text-zinc-950 hover:bg-white/60'
                    }`}
                  >
                    <span>{item.label}</span>
                    {item.badge && !isActive && (
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Right Controls: Font Preset Switcher + Keys + User Profile */}
          <div className="flex items-center gap-2.5 shrink-0">
            {/* Live Typography Preset Switcher */}
            <div className="relative">
              <button
                onClick={() => {
                  setShowFontMenu(!showFontMenu);
                  setShowUserMenu(false);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-zinc-700 hover:text-zinc-950 rounded-xl bg-white border border-zinc-200/90 hover:border-zinc-300 shadow-[0_1px_3px_rgba(0,0,0,0.04),inset_0_1px_0_rgba(255,255,255,1)] hover:-translate-y-0.5 active:translate-y-0 transition-all cursor-pointer"
                title="Change Typography Preset"
              >
                <Type className="h-3.5 w-3.5 text-zinc-600" />
                <span className="font-serif font-semibold text-sm hidden sm:inline">Aa</span>
                <span className="text-[11px] text-zinc-500 hidden lg:inline">Font</span>
                <ChevronDown className="h-3 w-3 text-zinc-400" />
              </button>

              {showFontMenu && (
                <div className="absolute right-0 mt-2 w-72 rounded-2xl border border-zinc-200/90 bg-white p-2 shadow-floating-dock z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="p-2.5 border-b border-zinc-100 flex items-center justify-between">
                    <div>
                      <span className="text-xs font-semibold text-zinc-900 block">Typography Presets</span>
                      <span className="text-[10px] text-zinc-400">Live editorial font pairing</span>
                    </div>
                    <Badge variant="genuine" size="sm">Live</Badge>
                  </div>

                  <div className="py-1 space-y-1">
                    {fontOptions.map((opt) => {
                      const isSelected = fontPreset === opt.id;
                      return (
                        <button
                          key={opt.id}
                          onClick={() => {
                            setFontPreset(opt.id);
                            setShowFontMenu(false);
                          }}
                          className={`w-full text-left p-2.5 rounded-xl text-xs transition-all flex items-center justify-between cursor-pointer ${
                            isSelected
                              ? 'bg-zinc-900 text-white shadow-subtle'
                              : 'text-zinc-700 hover:bg-zinc-50'
                          }`}
                        >
                          <div>
                            <div className={`font-medium ${isSelected ? 'text-white' : 'text-zinc-900'}`}>
                              {opt.name}
                            </div>
                            <div className={`text-[10px] ${isSelected ? 'text-zinc-300' : 'text-zinc-400'}`}>
                              {opt.desc}
                            </div>
                          </div>
                          {isSelected && <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 ml-2" />}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() => setShowShortcutsModal(true)}
              className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 text-xs text-zinc-500 hover:text-zinc-900 rounded-xl hover:bg-white border border-transparent hover:border-zinc-200/80 hover:shadow-subtle transition-all cursor-pointer"
            >
              <Command className="h-3.5 w-3.5" />
              <span>Keys</span>
              <KbdBadge kbd="?" />
            </button>

            <div className="h-4 w-px bg-zinc-200 mx-1 hidden lg:block" />

            {/* Operator Menu */}
            <div className="relative">
              <button
                onClick={() => {
                  setShowUserMenu(!showUserMenu);
                  setShowFontMenu(false);
                }}
                className="flex items-center gap-2.5 p-1 pl-2.5 pr-1.5 rounded-full border border-zinc-200/90 hover:border-zinc-300 bg-white hover:bg-zinc-50/80 transition-all cursor-pointer shadow-[0_1px_4px_rgba(0,0,0,0.04),inset_0_1px_0_rgba(255,255,255,1)] hover:-translate-y-0.5 active:translate-y-0"
              >
                <div className="text-left hidden sm:block">
                  <div className="text-xs font-semibold text-zinc-900 leading-none">
                    {currentUser.name}
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-0.5 leading-none">
                    {currentUser.role}
                  </div>
                </div>
                <img
                  src={currentUser.avatar}
                  alt={currentUser.name}
                  className="h-7 w-7 rounded-full object-cover border border-zinc-200 shadow-sm"
                />
              </button>

              {/* User Dropdown */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-64 rounded-2xl border border-zinc-200/90 bg-white p-2 shadow-floating-dock z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="p-3 border-b border-zinc-100">
                    <div className="text-xs font-semibold text-zinc-900">{currentUser.name}</div>
                    <div className="text-[11px] text-zinc-500 truncate">{currentUser.email}</div>
                    <div className="mt-1.5">
                      <Badge variant="genuine" size="sm" dot>Active Session</Badge>
                    </div>
                  </div>

                  <div className="py-1">
                    <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                      Switch Persona
                    </div>
                    {availablePersonas.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => {
                          onSwitchUser(p);
                          setShowUserMenu(false);
                        }}
                        className="w-full text-left px-3 py-2 text-xs text-zinc-700 hover:bg-zinc-50 rounded-xl transition-colors flex items-center justify-between cursor-pointer"
                      >
                        <div>
                          <div className="font-medium text-zinc-900">{p.name}</div>
                          <div className="text-[10px] text-zinc-500">{p.role}</div>
                        </div>
                        {currentUser.id === p.id && (
                          <CheckCircle2 className="h-4 w-4 text-zinc-900" />
                        )}
                      </button>
                    ))}
                  </div>

                  <div className="pt-1 border-t border-zinc-100">
                    <button
                      onClick={() => {
                        setShowUserMenu(false);
                        onLogout();
                      }}
                      className="w-full text-left px-3 py-2 text-xs text-rose-600 hover:bg-rose-50 rounded-xl transition-colors flex items-center gap-2 cursor-pointer"
                    >
                      <LogOut className="h-3.5 w-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        {children}
      </main>

      {/* Subtle Footer */}
      <footer className="border-t border-zinc-200/60 py-6 text-center text-xs text-zinc-400">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Vellum &mdash; Intelligent Document &amp; Credential Verification</span>
          <span className="font-mono text-[11px] text-zinc-400">Multi-Modal AI Pipeline v2.4</span>
        </div>
      </footer>

      {/* Shortcuts Modal */}
      <Modal
        isOpen={showShortcutsModal}
        onClose={() => setShowShortcutsModal(false)}
        title="Keyboard Navigation Shortcuts"
        maxWidth="md"
      >
        <div className="space-y-3 text-xs">
          <p className="text-zinc-600">
            Execute verification decisions and layer toggles instantly:
          </p>
          <div className="grid grid-cols-2 gap-2.5 pt-2">
            <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-50/80 border border-zinc-200/80 shadow-subtle">
              <span className="text-zinc-800 font-medium">Approve Credential</span>
              <KbdBadge kbd="A" />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-50/80 border border-zinc-200/80 shadow-subtle">
              <span className="text-zinc-800 font-medium">Escalate to Review</span>
              <KbdBadge kbd="E" />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-50/80 border border-zinc-200/80 shadow-subtle">
              <span className="text-zinc-800 font-medium">Reject / Flag Fraud</span>
              <KbdBadge kbd="R" />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-50/80 border border-zinc-200/80 shadow-subtle">
              <span className="text-zinc-800 font-medium">Pristine Scan</span>
              <KbdBadge kbd="1" />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-50/80 border border-zinc-200/80 shadow-subtle">
              <span className="text-zinc-800 font-medium">Tampering Layer</span>
              <KbdBadge kbd="2" />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-50/80 border border-zinc-200/80 shadow-subtle">
              <span className="text-zinc-800 font-medium">OCR Spatial Anchors</span>
              <KbdBadge kbd="3" />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-50/80 border border-zinc-200/80 shadow-subtle">
              <span className="text-zinc-800 font-medium">2.5x Optical Loupe</span>
              <KbdBadge kbd="4" />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-50/80 border border-zinc-200/80 shadow-subtle">
              <span className="text-zinc-800 font-medium">Next Dossier</span>
              <KbdBadge kbd="J" />
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
};
