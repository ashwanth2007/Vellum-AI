import React, { useEffect, useState } from 'react';
import { CheckCircle2, ArrowRight, ArrowLeft, Loader2, AlertTriangle } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';

interface ProcessingPageProps {
  fileName: string;
  status: 'running' | 'done' | 'error';
  timings?: Record<string, number>;
  error?: string;
  onComplete: () => void;
  onBack: () => void;
}

const STAGES = [
  { key: 'decode', title: '1. File type check and decoding', desc: 'Magic-byte sniffing. Images decoded with EXIF rotation, PDF pages rendered at 200 DPI.' },
  { key: 'ocr', title: '2. OCR and layout analysis', desc: 'RapidOCR (PaddleOCR models on ONNX Runtime): text lines with bounding boxes.' },
  { key: 'classification', title: '3. Multi-modal document classification', desc: 'Fine-tuned EfficientNet-B0 + zero-shot CLIP on the pixels + TF-IDF model on the OCR text, fused.' },
  { key: 'field_extraction', title: '4. Field extraction', desc: 'Layout-aware rules pull the name, register number, CGPA, dates and the course table.' },
];

export const ProcessingPage: React.FC<ProcessingPageProps> = ({ fileName, status, timings, error, onComplete, onBack }) => {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (status !== 'running') return;
    setActiveStep(0);
    const timer = setInterval(() => setActiveStep((p) => (p < STAGES.length - 1 ? p + 1 : p)), 700);
    return () => clearInterval(timer);
  }, [status]);

  const doneCount = status === 'done' ? STAGES.length : activeStep;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="space-y-1.5 pb-4 border-b border-zinc-200/80">
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${status === 'error' ? 'bg-rose-600' : 'bg-emerald-600 animate-pulse'}`} />
          <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Step 2 of 3: Inference</span>
        </div>
        <h1 className="font-serif text-3xl md:text-4xl font-normal tracking-tight text-zinc-950">Multi-Modal Pipeline</h1>
        <p className="text-xs text-zinc-500 max-w-xl leading-relaxed break-all">Analysing {fileName}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-8 items-start">
        <div className="md:col-span-3 space-y-3">
          {STAGES.map((stage, idx) => {
            const isDone = idx < doneCount;
            const isCurrent = status === 'running' && idx === activeStep;
            const ms = status === 'done' && timings ? timings[stage.key] : undefined;
            return (
              <div
                key={stage.key}
                className={`flex items-center justify-between p-4 rounded-2xl border transition-all duration-300 ${
                  isDone ? 'depth-card border-zinc-200/90 text-zinc-950'
                    : isCurrent ? 'bg-white border-zinc-900 shadow-[0_4px_16px_rgba(0,0,0,0.08)] text-zinc-950'
                      : 'border-zinc-200/60 bg-zinc-50/40 text-zinc-400'
                }`}
              >
                <div className="flex items-center gap-3.5">
                  {isDone ? (
                    <div className="h-6 w-6 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
                      <CheckCircle2 className="h-4 w-4" />
                    </div>
                  ) : isCurrent ? (
                    <div className="h-6 w-6 rounded-full bg-zinc-900 flex items-center justify-center text-white">
                      <Loader2 className="h-3.5 w-3.5 animate-spin motion-reduce:animate-none" />
                    </div>
                  ) : (
                    <div className="h-6 w-6 rounded-full border border-zinc-300 bg-zinc-100 flex items-center justify-center text-[10px] font-mono text-zinc-500">{idx + 1}</div>
                  )}
                  <div>
                    <div className="text-xs font-semibold">{stage.title}</div>
                    <div className="text-[11px] text-zinc-500">{stage.desc}</div>
                  </div>
                </div>
                {ms !== undefined && (
                  <span className="font-mono text-[10px] text-zinc-700 bg-zinc-100 px-2.5 py-0.5 rounded-full border border-zinc-200/70 shrink-0 ml-3">{ms} ms</span>
                )}
              </div>
            );
          })}
        </div>

        <div className="md:col-span-2 depth-card-static rounded-3xl p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <span className="text-xs font-semibold text-zinc-900">Run status</span>
            {status === 'running' && <Badge variant="neural" size="sm" dot>Running</Badge>}
            {status === 'done' && <Badge variant="genuine" size="sm">Complete</Badge>}
            {status === 'error' && <Badge variant="danger" size="sm">Rejected</Badge>}
          </div>

          {status === 'error' ? (
            <div className="flex items-start gap-2 text-xs text-rose-900 bg-rose-50 border border-rose-200 rounded-xl p-3">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          ) : (
            <div className="text-xs font-mono text-zinc-600">
              <div className="flex justify-between items-center py-1">
                <span className="text-zinc-500 font-sans">Total time:</span>
                <span className="text-zinc-950 font-bold text-sm">{status === 'done' && timings ? `${timings.total} ms` : '...'}</span>
              </div>
            </div>
          )}

          {status === 'error' ? (
            <Button variant="secondary" size="lg" onClick={onBack} icon={<ArrowLeft className="h-4 w-4" />} className="w-full py-3">
              Try another file
            </Button>
          ) : (
            <Button variant="primary" size="lg" onClick={onComplete} icon={<ArrowRight className="h-4 w-4" />}
              className="w-full py-3" disabled={status !== 'done'}>
              {status === 'done' ? 'View results' : 'Running models...'}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
