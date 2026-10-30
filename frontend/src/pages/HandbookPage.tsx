import React from 'react';
import { FileInput, Filter, ScanText, ListChecks, ArrowDown, ArrowRight, CheckCircle2, XCircle } from 'lucide-react';

interface HandbookPageProps {
  onNavigate: (screen: string) => void;
}

const BUCKETS = [
  { name: 'Certificate', ex: 'Degree, course completion, internship, participation', relevant: true },
  { name: 'Academic record', ex: 'Grade sheet, CGPA, transcript, completion or bonafide letter, LOR', relevant: true },
  { name: 'Unrelated document', ex: 'A real document that is not a credential: invoice, form, memo, article', relevant: false },
  { name: 'Not a document', ex: 'A photo of a person, an animal, a street, food', relevant: false },
];

const FIELDS = [
  'Document title', 'Holder name', 'Register number', 'Institution', 'Programme', 'Course', 'Semester',
  'Exam session', 'CGPA / GPA / percentage', 'Class awarded', 'Certificate number', 'Issue date', 'Signatories',
  'Course and grade table',
];

const STEPS = [
  {
    n: 0, icon: FileInput, title: 'Input and decoding', time: '2 to 60 ms',
    what: 'The file type is checked from its first bytes, not its name. Images are decoded and turned upright using the EXIF rotation a phone writes. Each PDF page (up to 5) is rendered to an image at 300 DPI.',
    out: 'One RGB image per page: a grid of pixels, each pixel three numbers (red, green, blue) from 0 to 255.',
  },
  {
    n: 1, icon: Filter, title: 'Classification: which of the four buckets', time: '~40 ms, or ~80 ms if CLIP is needed',
    what: 'Three models are available. They run one at a time, fastest first: the EfficientNet-B0 CNN, then CLIP, then the text model. The first one that is at least 90% sure gives the answer and the others never run.',
    out: 'One class out of four, its confidence, and the name of the model that decided. Certificates and academic records are relevant; the other two are rejected here and the pipeline stops.',
    link: 'learn-cascade', linkLabel: 'How one model is picked',
  },
  {
    n: 2, icon: ScanText, title: 'Text recognition (OCR)', time: '4 to 15 s',
    what: 'Only for relevant documents. RapidOCR runs two neural networks: a detection network finds every line of text and draws a box round it, then a recognition network reads the characters inside each box.',
    out: 'Every text line with its position on the page and a confidence score. These are the green boxes on the result page.',
    link: 'learn-text', linkLabel: 'How OCR and the text model work',
  },
  {
    n: 3, icon: ListChecks, title: 'Field extraction: the parameters', time: 'under 10 ms',
    what: 'Rules that know the document type look through the OCR lines by content and by position: a line under a "Name" label, a pattern like 19BEC8572, a number after "CGPA", a table with course codes and grades.',
    out: 'The named fields below. Every value is copied from the text that was read; a field that is not on the page is left out, never guessed.',
  },
];

export const HandbookPage: React.FC<HandbookPageProps> = ({ onNavigate }) => (
  <div className="max-w-4xl mx-auto space-y-10">
    <header className="space-y-3 pb-6 border-b border-zinc-200/80">
      <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Handbook</span>
      <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-950">What Vellum is and how it works</h1>
      <p className="text-base text-zinc-700 leading-relaxed">
        Vellum takes any uploaded file and answers three questions in order. <strong>Is this an academic credential?</strong>{' '}
        <strong>What text is on it?</strong> <strong>What are its details</strong> (name, register number, CGPA, dates, courses)?
        Anything that is not a credential is rejected at the first question, in about 40 milliseconds.
      </p>
    </header>

    {/* Inputs */}
    <section className="space-y-3">
      <h2 className="text-xl font-semibold text-zinc-950">1. What goes in</h2>
      <ul className="text-sm text-zinc-700 space-y-1.5 list-disc pl-5">
        <li>Images: PNG, JPG, WEBP, BMP, TIFF, GIF. Scans and phone photos both work.</li>
        <li>PDF files: the first 5 pages are analysed, each rendered at 300 DPI.</li>
        <li>Up to 25 MB. Anything else (a .txt file, a Word file, an empty file) is refused with a clear message.</li>
      </ul>
    </section>

    {/* Four buckets */}
    <section className="space-y-3">
      <h2 className="text-xl font-semibold text-zinc-950">2. The four buckets</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {BUCKETS.map((b) => (
          <div key={b.name} className="depth-card-static rounded-2xl p-4 flex gap-3">
            {b.relevant ? <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" /> : <XCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />}
            <div className="min-w-0">
              <div className="text-sm font-semibold text-zinc-950">{b.name}</div>
              <div className="text-xs text-zinc-600 leading-relaxed">{b.ex}</div>
              <div className={`text-[11px] font-medium mt-1 ${b.relevant ? 'text-emerald-700' : 'text-rose-700'}`}>
                {b.relevant ? 'Relevant: continues to OCR and fields' : 'Rejected: pipeline stops'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>

    {/* Workflow */}
    <section className="space-y-4">
      <h2 className="text-xl font-semibold text-zinc-950">3. The workflow, step by step</h2>
      <div className="space-y-2">
        {STEPS.map((s, i) => {
          const Icon = s.icon;
          return (
            <React.Fragment key={s.n}>
              <div className="depth-card-static rounded-2xl p-5 space-y-3">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="h-9 w-9 rounded-xl bg-zinc-900 text-white flex items-center justify-center shrink-0"><Icon className="h-4.5 w-4.5" /></span>
                  <div className="min-w-0 flex-1">
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">{s.n === 0 ? 'Before step 1' : `Step ${s.n}`}</div>
                    <div className="text-base font-semibold text-zinc-950">{s.title}</div>
                  </div>
                  <span className="font-mono text-[11px] text-zinc-600 bg-zinc-100 border border-zinc-200 rounded-full px-2.5 py-0.5">{s.time}</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div>
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 mb-1">What happens</div>
                    <p className="text-zinc-700 leading-relaxed">{s.what}</p>
                  </div>
                  <div>
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 mb-1">What comes out</div>
                    <p className="text-zinc-700 leading-relaxed">{s.out}</p>
                  </div>
                </div>
                {s.link && (
                  <button onClick={() => onNavigate(s.link!)} className="flex items-center gap-1.5 text-xs font-medium text-zinc-900 hover:underline cursor-pointer">
                    {s.linkLabel} <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
              {i < STEPS.length - 1 && (
                <div className="flex items-center justify-center gap-2 text-[11px] text-zinc-500">
                  <ArrowDown className="h-4 w-4" />
                  {s.n === 1 && <span>only if relevant</span>}
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </section>

    {/* Outputs */}
    <section className="space-y-3">
      <h2 className="text-xl font-semibold text-zinc-950">4. What comes out</h2>
      <ul className="text-sm text-zinc-700 space-y-1.5 list-disc pl-5">
        <li><strong>A verdict:</strong> relevant or not, the bucket, the confidence, and which model decided.</li>
        <li><strong>The document with OCR boxes</strong> drawn over every line of text that was read.</li>
        <li><strong>The fields</strong> it could find, each with the OCR confidence of the text it came from:</li>
      </ul>
      <div className="flex flex-wrap gap-1.5 pl-5">
        {FIELDS.map((f) => (
          <span key={f} className="text-xs text-zinc-700 bg-white border border-zinc-200 rounded-full px-2.5 py-1">{f}</span>
        ))}
      </div>
      <ul className="text-sm text-zinc-700 space-y-1.5 list-disc pl-5">
        <li><strong>The time each step took</strong>, so the speed claim can be checked on every run.</li>
      </ul>
    </section>

    {/* Limits */}
    <section className="space-y-3">
      <h2 className="text-xl font-semibold text-zinc-950">5. What it does not do</h2>
      <ul className="text-sm text-zinc-700 space-y-1.5 list-disc pl-5">
        <li>It does not say whether a certificate is <em>genuine</em>. It says what kind of document it is and what it says.</li>
        <li>It recognises the document as a whole image. It does not draw boxes around seals, logos or signatures.</li>
        <li>Handwriting and very blurred text are read poorly by OCR, so fields from them may be missing.</li>
      </ul>
    </section>

    <div className="flex flex-wrap gap-3 pt-2">
      <button onClick={() => onNavigate('upload')} className="px-4 py-2 rounded-xl bg-zinc-900 text-white text-sm font-medium cursor-pointer hover:bg-zinc-800 transition-colors duration-200">
        Try it: upload a document
      </button>
      <button onClick={() => onNavigate('learn-foundations')} className="px-4 py-2 rounded-xl border border-zinc-300 bg-white text-sm font-medium text-zinc-900 cursor-pointer hover:bg-zinc-50 transition-colors duration-200">
        Learn the ML behind it
      </button>
    </div>
  </div>
);
