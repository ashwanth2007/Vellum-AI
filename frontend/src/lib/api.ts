// Client for the Vellum FastAPI backend. Vite proxies /api to http://127.0.0.1:8000 in dev.

export type DocClass = 'CERTIFICATE' | 'ACADEMIC_RECORD' | 'OTHER_DOCUMENT' | 'RANDOM_PHOTO';

export const DOC_CLASSES: DocClass[] = ['CERTIFICATE', 'ACADEMIC_RECORD', 'OTHER_DOCUMENT', 'RANDOM_PHOTO'];

export const CLASS_NAMES: Record<DocClass, string> = {
  CERTIFICATE: 'Certificate',
  ACADEMIC_RECORD: 'Academic record',
  OTHER_DOCUMENT: 'Unrelated document',
  RANDOM_PHOTO: 'Not a document',
};

export interface Classification {
  document_type: DocClass;
  label: string;
  is_relevant: boolean;
  confidence: number;
  class_probabilities: Record<DocClass, number>;
  image_probabilities: Record<DocClass, number>;
  text_probabilities: Record<DocClass, number> | null;
  fusion_mode: 'image' | 'image+text';
}

export interface ExtractedField {
  key: string;
  label: string;
  value: string;
  confidence: number;
}

export interface OcrBox {
  bbox: [number, number, number, number];
  text: string;
  confidence: number;
}

export interface AnalysisResult {
  document_name: string;
  file_type: string;
  page_count: number;
  pages_analyzed: number;
  verdict: { is_relevant: boolean; label: string; headline: string };
  classification: Classification;
  fields: ExtractedField[];
  table: { columns: string[]; rows: string[][] } | null;
  ocr: { engine: string; word_count: number; average_confidence: number; text: string };
  preview: { image: string; width: number; height: number; boxes: OcrBox[] };
  pages: { page: number; document_type: DocClass; label: string; confidence: number; is_relevant: boolean }[];
  experimental: { tampering?: { status: string; is_tampered: boolean; tampering_probability: number } } | null;
  timings_ms: Record<string, number>;
}

export async function analyzeFile(file: File): Promise<AnalysisResult> {
  const body = new FormData();
  body.append('file', file);
  let res: Response;
  try {
    res = await fetch('/api/analyze', { method: 'POST', body });
  } catch {
    throw new Error('Cannot reach the analysis server. Start the backend on port 8000.');
  }
  if (!res.ok) {
    let detail = `Server returned ${res.status}`;
    try {
      const j = await res.json();
      if (j?.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function sha256Hex(file: File): Promise<string> {
  const buf = await file.arrayBuffer();
  const hash = await crypto.subtle.digest('SHA-256', buf);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
}

export interface SampleFile {
  name: string;
  size: number;
}

export async function listSamples(): Promise<SampleFile[]> {
  try {
    const r = await fetch('/api/samples');
    return r.ok ? r.json() : [];
  } catch {
    return [];
  }
}

export async function fetchSample(name: string): Promise<File> {
  const r = await fetch(`/api/samples/${encodeURIComponent(name)}`);
  if (!r.ok) throw new Error(`Sample ${name} not found`);
  const blob = await r.blob();
  return new File([blob], name, { type: blob.type });
}
