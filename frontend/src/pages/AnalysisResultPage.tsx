import React, { useState } from 'react';
import { ShieldCheck, ShieldX, RotateCcw, ScanText, FileText, Layers, Clock } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { AnalysisResult, CLASS_NAMES, DOC_CLASSES, DocClass } from '../lib/api';

interface AnalysisResultPageProps {
  result: AnalysisResult | null;
  onAnalyzeAnother: () => void;
}

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

const ProbBars: React.FC<{ title: string; probs: Record<DocClass, number> | null; winner?: DocClass; note?: string }> = ({ title, probs, winner, note }) => (
  <div className="space-y-2">
    <div className="flex items-center justify-between">
      <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">{title}</span>
      {note && <span className="text-[11px] text-zinc-400">{note}</span>}
    </div>
    {probs ? (
      DOC_CLASSES.map((c) => {
        const relevant = c === 'CERTIFICATE' || c === 'ACADEMIC_RECORD';
        const isWin = c === winner;
        return (
          <div key={c} className="grid grid-cols-[120px_1fr_52px] items-center gap-2 text-xs">
            <span className={isWin ? 'font-semibold text-zinc-950' : 'text-zinc-600'}>{CLASS_NAMES[c]}</span>
            <div className="h-2.5 rounded-full bg-zinc-100 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${relevant ? 'bg-emerald-600' : 'bg-rose-500'} ${isWin ? '' : 'opacity-40'}`}
                style={{ width: `${Math.max(1, probs[c] * 100)}%` }}
              />
            </div>
            <span className="font-mono text-right text-zinc-700">{pct(probs[c])}</span>
          </div>
        );
      })
    ) : (
      <p className="text-xs text-zinc-400">Not used: fewer than 5 words of text were found.</p>
    )}
  </div>
);

export const AnalysisResultPage: React.FC<AnalysisResultPageProps> = ({ result, onAnalyzeAnother }) => {
  const [showBoxes, setShowBoxes] = useState(true);
  const [showText, setShowText] = useState(false);

  if (!result) {
    return (
      <div className="max-w-xl mx-auto text-center space-y-4 py-20">
        <p className="text-sm text-zinc-600">No document analysed yet.</p>
        <Button variant="primary" onClick={onAnalyzeAnother}>Upload a document</Button>
      </div>
    );
  }

  const { verdict, classification: cls, preview } = result;
  const good = verdict.is_relevant;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3 pb-4 border-b border-zinc-200/80">
        <div className="space-y-1.5 min-w-0">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-zinc-900" />
            <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Step 3 of 3: Result</span>
          </div>
          <h1 className="font-serif text-3xl md:text-4xl font-normal tracking-tight text-zinc-950">Analysis Result</h1>
          <p className="text-xs text-zinc-500 break-all">
            {result.document_name} | {result.file_type} | {result.page_count} page{result.page_count > 1 ? 's' : ''}
          </p>
        </div>
        <Button variant="secondary" onClick={onAnalyzeAnother} icon={<RotateCcw className="h-4 w-4" />}>Analyze another</Button>
      </div>

      {/* Verdict banner */}
      <div className={`rounded-3xl border p-6 flex flex-col sm:flex-row sm:items-center gap-4 shadow-card ${good ? 'border-emerald-200 bg-gradient-to-r from-emerald-50 to-white' : 'border-rose-200 bg-gradient-to-r from-rose-50 to-white'}`}>
        <div className={`h-14 w-14 shrink-0 rounded-2xl flex items-center justify-center ${good ? 'bg-emerald-600' : 'bg-rose-600'} text-white`}>
          {good ? <ShieldCheck className="h-8 w-8" /> : <ShieldX className="h-8 w-8" />}
        </div>
        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-serif text-2xl text-zinc-950">{cls.label}</span>
            <Badge variant={good ? 'genuine' : 'danger'}>{good ? 'Relevant credential' : 'Not relevant'}</Badge>
            <Badge variant="neutral" size="sm">{pct(cls.confidence)} confidence</Badge>
          </div>
          <p className="text-sm text-zinc-700">{verdict.headline}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* Document preview with OCR boxes */}
        <div className="depth-card-static rounded-3xl p-5 space-y-3 min-w-0">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-zinc-900 flex items-center gap-1.5"><FileText className="h-4 w-4" /> Document</span>
            <label className="flex items-center gap-2 text-xs text-zinc-600 cursor-pointer select-none">
              <input type="checkbox" checked={showBoxes} onChange={(e) => setShowBoxes(e.target.checked)} className="cursor-pointer accent-zinc-900" />
              Show OCR boxes ({preview.boxes.length})
            </label>
          </div>
          <div className="relative w-full rounded-xl overflow-hidden border border-zinc-200 bg-zinc-50">
            <img src={preview.image} alt="Uploaded document" className="w-full h-auto block" />
            {showBoxes && (
              <svg viewBox={`0 0 ${preview.width} ${preview.height}`} className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none">
                {preview.boxes.map((b, i) => (
                  <rect key={i} x={b.bbox[0]} y={b.bbox[1]} width={b.bbox[2] - b.bbox[0]} height={b.bbox[3] - b.bbox[1]}
                    fill="rgba(16,185,129,0.10)" stroke="rgb(5,150,105)" strokeWidth={Math.max(1, preview.width / 500)} />
                ))}
              </svg>
            )}
          </div>
          {result.pages.length > 1 && (
            <div className="space-y-1.5 pt-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5"><Layers className="h-3.5 w-3.5" /> Per page</span>
              {result.pages.map((p) => (
                <div key={p.page} className="flex items-center justify-between text-xs border-b border-zinc-100 py-1.5">
                  <span className="text-zinc-600">Page {p.page}</span>
                  <span className="flex items-center gap-2">
                    <Badge variant={p.is_relevant ? 'genuine' : 'danger'} size="sm">{p.label}</Badge>
                    <span className="font-mono text-zinc-500">{pct(p.confidence)}</span>
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-6 min-w-0">
          {/* Classification breakdown */}
          <div className="depth-card-static rounded-3xl p-5 space-y-5">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <span className="text-xs font-semibold text-zinc-900">Classification</span>
              <Badge variant="neural" size="sm">{cls.fusion_mode.split('+').length} models fused</Badge>
            </div>
            <ProbBars title="Final (fused)" probs={cls.class_probabilities} winner={cls.document_type} />
            <ProbBars title="Image model (fine-tuned)" probs={cls.image_probabilities} winner={cls.document_type} note="EfficientNet-B0" />
            <ProbBars title="Vision-language model (zero-shot)" probs={cls.clip_probabilities} winner={cls.document_type} note="CLIP ViT-B/32" />
            <ProbBars title="Text model (OCR)" probs={cls.text_probabilities} winner={cls.document_type} note="TF-IDF + LogReg" />
          </div>

          {/* Extracted fields */}
          <div className="depth-card-static rounded-3xl p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <span className="text-xs font-semibold text-zinc-900">Extracted fields</span>
              <Badge variant="neutral" size="sm">{result.fields.length} found</Badge>
            </div>
            {good ? (
              result.fields.length ? (
                <table className="w-full text-xs">
                  <tbody>
                    {result.fields.map((f) => (
                      <tr key={f.key} className="border-b border-zinc-100 last:border-0 align-top">
                        <td className="py-2 pr-3 text-zinc-500 whitespace-nowrap">{f.label}</td>
                        <td className="py-2 text-zinc-950 font-medium break-words">{f.value}</td>
                        <td className="py-2 pl-2 text-right font-mono text-[10px] text-zinc-400 whitespace-nowrap">{pct(f.confidence)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-xs text-zinc-500">No fields could be read from this document. The text may be too small or blurred.</p>
              )
            ) : (
              <p className="text-xs text-zinc-500">Field extraction runs only for certificates and academic records.</p>
            )}
          </div>
        </div>
      </div>

      {result.table && (
        <div className="depth-card-static rounded-3xl p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <span className="text-xs font-semibold text-zinc-900">Course table read from the document</span>
            <Badge variant="neutral" size="sm">{result.table.rows.length} rows</Badge>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs min-w-[480px]">
              <thead>
                <tr className="text-left text-zinc-500 border-b border-zinc-200">
                  {result.table.columns.map((c) => <th key={c} className="py-2 pr-3 font-semibold">{c}</th>)}
                </tr>
              </thead>
              <tbody>
                {result.table.rows.map((r, i) => (
                  <tr key={i} className="border-b border-zinc-100 last:border-0">
                    {r.map((v, j) => <td key={j} className="py-1.5 pr-3 text-zinc-900">{v || '-'}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        <div className="depth-card-static rounded-3xl p-5 space-y-3 min-w-0">
          <button type="button" onClick={() => setShowText((s) => !s)}
            className="w-full flex items-center justify-between text-xs font-semibold text-zinc-900 cursor-pointer">
            <span className="flex items-center gap-1.5"><ScanText className="h-4 w-4" /> OCR text ({result.ocr.word_count} words, {result.ocr.engine})</span>
            <span className="text-zinc-500 font-normal">{showText ? 'Hide' : 'Show'}</span>
          </button>
          {showText && (
            <pre className="text-[11px] leading-relaxed text-zinc-700 bg-zinc-50 border border-zinc-200 rounded-xl p-3 max-h-72 overflow-auto whitespace-pre-wrap">
              {result.ocr.text || '(no text found)'}
            </pre>
          )}
        </div>
        <div className="depth-card-static rounded-3xl p-5 space-y-2">
          <span className="text-xs font-semibold text-zinc-900 flex items-center gap-1.5"><Clock className="h-4 w-4" /> Pipeline timing</span>
          {Object.entries(result.timings_ms).map(([k, v]) => (
            <div key={k} className="flex justify-between text-xs border-b border-zinc-100 last:border-0 py-1">
              <span className="text-zinc-500 capitalize">{k.replace('_', ' ')}</span>
              <span className="font-mono text-zinc-900">{v} ms</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
