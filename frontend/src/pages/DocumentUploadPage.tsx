import React, { useCallback, useEffect, useRef, useState } from 'react';
import { UploadCloud, CheckCircle2, ArrowRight, FileText, Image as ImageIcon, AlertTriangle, X } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { fetchSample, formatBytes, listSamples, SampleFile, sha256Hex } from '../lib/api';

interface DocumentUploadPageProps {
  onStartProcessing: (file: File) => void;
}

const SUPPORTED = /\.(png|jpe?g|webp|bmp|tiff?|gif|pdf)$/i;

const CLASS_GUIDE = [
  { name: 'Certificate', desc: 'Degree, course completion, internship, participation', tone: 'genuine' as const },
  { name: 'Academic record', desc: 'Grade sheet, CGPA, transcript, completion or bonafide letter, LOR', tone: 'genuine' as const },
  { name: 'Unrelated document', desc: 'A real document that is not a credential: invoice, form, memo', tone: 'warning' as const },
  { name: 'Not a document', desc: 'A random photo, a selfie, a scene', tone: 'danger' as const },
];

export const DocumentUploadPage: React.FC<DocumentUploadPageProps> = ({ onStartProcessing }) => {
  const [file, setFile] = useState<File | null>(null);
  const [hash, setHash] = useState<string>('');
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [dims, setDims] = useState<string>('');
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const [samples, setSamples] = useState<SampleFile[]>([]);

  useEffect(() => { listSamples().then(setSamples); }, []);

  const pick = useCallback(async (f: File | undefined | null) => {
    if (!f) return;
    setFile(f);
    setHash('');
    setDims('');
    setPreviewUrl(f.type.startsWith('image/') ? URL.createObjectURL(f) : '');
    setHash(await sha256Hex(f));
  }, []);

  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  const isPdf = file ? /\.pdf$/i.test(file.name) || file.type === 'application/pdf' : false;
  const looksSupported = file ? SUPPORTED.test(file.name) : false;

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="space-y-1.5 pb-4 border-b border-zinc-200/80">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-zinc-900" />
          <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Step 1 of 3: Intake</span>
        </div>
        <h1 className="font-serif text-3xl md:text-4xl font-normal tracking-tight text-zinc-950">Document Intake Gateway</h1>
        <p className="text-xs text-zinc-500 max-w-xl leading-relaxed">
          Upload an image or a PDF. The model decides whether it is an academic credential, then reads the fields out of it.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-8 items-start">
        <div className="md:col-span-3 space-y-5">
          <div
            role="button"
            tabIndex={0}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => { e.preventDefault(); setDragging(false); pick(e.dataTransfer.files?.[0]); }}
            className={`depth-card rounded-3xl p-10 text-center space-y-4 border-2 border-dashed transition-all duration-200 cursor-pointer group focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 ${
              dragging ? 'border-zinc-900 bg-zinc-50' : 'border-zinc-200/90 hover:border-zinc-400/90'
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              onChange={(e) => { pick(e.target.files?.[0]); e.target.value = ''; }}
            />
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Selected file preview"
                onLoad={(e) => setDims(`${(e.target as HTMLImageElement).naturalWidth} x ${(e.target as HTMLImageElement).naturalHeight} px`)}
                className="mx-auto max-h-64 rounded-xl border border-zinc-200 shadow-subtle object-contain"
              />
            ) : (
              <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-zinc-100 text-zinc-800 shadow-[inset_0_1px_2px_rgba(0,0,0,0.05)] group-hover:scale-105 transition-transform duration-200">
                {isPdf ? <FileText className="h-7 w-7" /> : <UploadCloud className="h-7 w-7" />}
              </div>
            )}
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-zinc-900">
                {file ? file.name : 'Drag and drop an image or PDF here, or click to browse'}
              </h3>
              <p className="text-xs text-zinc-400">PNG, JPG, WEBP, BMP, TIFF or PDF, up to 25 MB. PDFs: first 5 pages are analysed.</p>
            </div>
          </div>

          {samples.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs text-zinc-500 font-medium block">Or pick a test file from the demo_samples folder:</span>
              <div className="flex flex-wrap gap-2">
                {samples.map((s) => (
                  <button
                    key={s.name}
                    type="button"
                    onClick={async () => pick(await fetchSample(s.name))}
                    className={`px-3 py-1.5 rounded-xl text-[11px] font-mono transition-colors duration-150 cursor-pointer border ${
                      file?.name === s.name.split('/').pop() ? 'bg-zinc-900 text-white border-zinc-900' : 'bg-zinc-50/80 text-zinc-700 border-zinc-200 hover:bg-white'
                    }`}
                  >
                    {s.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {file && (
            <div className={`rounded-3xl border p-5 space-y-2 shadow-card ${looksSupported ? 'border-emerald-200/80 bg-gradient-to-b from-emerald-50/70 via-white to-white' : 'border-amber-200/80 bg-gradient-to-b from-amber-50/70 via-white to-white'}`}>
              <div className={`flex items-center justify-between text-xs font-semibold pb-2 border-b ${looksSupported ? 'text-emerald-950 border-emerald-100' : 'text-amber-950 border-amber-100'}`}>
                <span className="flex items-center gap-1.5">
                  {looksSupported
                    ? <><CheckCircle2 className="h-4 w-4 text-emerald-600" /> File ready</>
                    : <><AlertTriangle className="h-4 w-4 text-amber-600" /> Unusual file type: the server will check it</>}
                </span>
                <button type="button" aria-label="Clear file" onClick={() => { setFile(null); setPreviewUrl(''); setHash(''); }}
                  className="p-1 rounded-lg hover:bg-white cursor-pointer transition-colors duration-150">
                  <X className="h-4 w-4 text-zinc-500" />
                </button>
              </div>
              <div className="text-xs text-zinc-800 space-y-1 font-mono pt-1 break-all">
                <div className="flex items-center gap-1.5">
                  {isPdf ? <FileText className="h-3.5 w-3.5" /> : <ImageIcon className="h-3.5 w-3.5" />}
                  {file.type || 'unknown type'} | {formatBytes(file.size)}{dims ? ` | ${dims}` : ''}
                </div>
                <div>SHA-256: {hash ? hash : 'computing...'}</div>
              </div>
            </div>
          )}
        </div>

        <div className="md:col-span-2 depth-card-static rounded-3xl p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <span className="text-xs font-semibold text-zinc-900">What the model decides</span>
            <Badge variant="neutral" size="sm">4 classes</Badge>
          </div>
          <ul className="space-y-3">
            {CLASS_GUIDE.map((c) => (
              <li key={c.name} className="flex items-start gap-3">
                <Badge variant={c.tone} size="sm" className="shrink-0 mt-0.5">{c.name}</Badge>
                <span className="text-xs text-zinc-600 leading-relaxed">{c.desc}</span>
              </li>
            ))}
          </ul>
          <p className="text-[11px] text-zinc-500 leading-relaxed border-t border-zinc-100 pt-3">
            The first two count as relevant. For those, the name, register number, institution, CGPA, dates and the course table are extracted.
          </p>
          <Button
            variant="primary"
            size="lg"
            onClick={() => file && onStartProcessing(file)}
            disabled={!file}
            icon={<ArrowRight className="h-4 w-4" />}
            className="w-full"
          >
            Analyze document
          </Button>
        </div>
      </div>
    </div>
  );
};
