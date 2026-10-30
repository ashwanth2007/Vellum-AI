import React, { useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight, Loader2 } from 'lucide-react';
import { CnnExplanation, explainCnn, fetchSample } from '../../lib/api';

// order of the "How the ML works" tabs, used for the previous / next links at the bottom of each
export const LEARN_ORDER = [
  { id: 'learn-foundations', label: 'Foundations' },
  { id: 'learn-cnn', label: 'EfficientNet-B0 CNN' },
  { id: 'learn-clip', label: 'CLIP ViT-B/32' },
  { id: 'learn-text', label: 'OCR + text model' },
  { id: 'learn-cascade', label: 'How one model is picked' },
];

export const DEFAULT_SAMPLE = '01_certificate_course_completion.png';

export const PageHeader: React.FC<{ kicker: string; title: string; children: React.ReactNode }> = ({ kicker, title, children }) => (
  <header className="space-y-3 pb-6 border-b border-zinc-200/80">
    <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">{kicker}</span>
    <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-950">{title}</h1>
    <div className="text-base text-zinc-700 leading-relaxed space-y-2">{children}</div>
  </header>
);

export const Section: React.FC<{ n: number; title: string; children: React.ReactNode }> = ({ n, title, children }) => (
  <section className="space-y-3">
    <h2 className="text-xl font-semibold text-zinc-950">{n}. {title}</h2>
    <div className="text-sm text-zinc-700 leading-relaxed space-y-3">{children}</div>
  </section>
);

export const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`depth-card-static rounded-2xl p-5 ${className}`}>{children}</div>
);

export const Formula: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="font-mono text-[13px] text-zinc-900 bg-white border border-zinc-200 rounded-xl px-4 py-3 overflow-x-auto whitespace-pre">{children}</div>
);

export const Rows: React.FC<{ rows: [string, React.ReactNode][] }> = ({ rows }) => (
  <table className="w-full text-sm">
    <tbody>
      {rows.map(([k, v]) => (
        <tr key={k} className="border-b border-zinc-100 last:border-0 align-top">
          <td className="py-2 pr-4 text-zinc-500 sm:whitespace-nowrap w-2/5 sm:w-auto">{k}</td>
          <td className="py-2 text-zinc-900">{v}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

export const PrevNext: React.FC<{ current: string; onNavigate: (s: string) => void }> = ({ current, onNavigate }) => {
  const i = LEARN_ORDER.findIndex((p) => p.id === current);
  const prev = LEARN_ORDER[i - 1];
  const next = LEARN_ORDER[i + 1];
  return (
    <div className="no-print flex flex-wrap justify-between gap-3 pt-6 border-t border-zinc-200/80">
      {prev ? (
        <button onClick={() => onNavigate(prev.id)} className="flex items-center gap-2 px-4 py-2 rounded-xl border border-zinc-300 bg-white text-sm font-medium text-zinc-900 cursor-pointer hover:bg-zinc-50 transition-colors duration-200">
          <ArrowLeft className="h-4 w-4" /> {prev.label}
        </button>
      ) : <span />}
      {next ? (
        <button onClick={() => onNavigate(next.id)} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-900 text-white text-sm font-medium cursor-pointer hover:bg-zinc-800 transition-colors duration-200">
          {next.label} <ArrowRight className="h-4 w-4" />
        </button>
      ) : (
        <button onClick={() => onNavigate('upload')} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-900 text-white text-sm font-medium cursor-pointer hover:bg-zinc-800 transition-colors duration-200">
          Try it on a document <ArrowRight className="h-4 w-4" />
        </button>
      )}
    </div>
  );
};

// One CNN run per file, shared by the Foundations and CNN tabs so switching tabs does not re-run it.
const cache = new Map<string, Promise<CnnExplanation>>();

export function useCnnExplanation(file: File | null) {
  const [data, setData] = useState<CnnExplanation | null>(null);
  const [error, setError] = useState('');
  const name = file ? `${file.name}:${file.size}` : DEFAULT_SAMPLE;
  useEffect(() => {
    let live = true;
    if (!cache.has(name)) {
      cache.set(name, (file ? Promise.resolve(file) : fetchSample(DEFAULT_SAMPLE)).then(explainCnn));
    }
    cache.get(name)!
      .then((d) => live && setData(d))
      .catch((e) => { cache.delete(name); if (live) setError(e.message || 'Could not run the model.'); });
    return () => { live = false; };
  }, [name]);
  return { data, error, source: file ? file.name : `the sample ${DEFAULT_SAMPLE}` };
}

export const LiveStatus: React.FC<{ error: string; source: string }> = ({ error, source }) =>
  error ? (
    <p className="text-sm text-rose-700">The live model run failed: {error}</p>
  ) : (
    <p className="text-sm text-zinc-500 flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" /> Running the real model on {source}...</p>
  );
