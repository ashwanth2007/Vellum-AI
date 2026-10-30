import React, { useEffect, useRef, useState } from 'react';
import { fetchSample } from '../../lib/api';
import { Card, DEFAULT_SAMPLE, Formula, PageHeader, PrevNext, Rows, Section } from './shared';

// the exact prompts in ml/document_classifier/clip_branch.py
const PROMPTS: Record<string, string[]> = {
  Certificate: [
    'a scan of a university degree certificate', 'a photo of a diploma', 'a certificate of completion with a signature and a seal',
    'an award certificate with a decorative border', 'an academic diploma written in latin or another language',
    'a framed graduation diploma', 'a course completion certificate',
  ],
  'Academic record': [
    'a university grade sheet with a table of courses and grades', 'a student mark sheet with subjects and marks',
    'an academic transcript of records', 'a report card with grades', 'a student record book with handwritten grades',
    'a letter of recommendation from a professor on university letterhead', 'a letter from a university registrar',
  ],
  'Unrelated document': [
    'a scanned invoice or receipt', 'a filled in paper form', 'a newspaper page', 'a business memo or email printout',
    'a bank statement', 'a restaurant menu', 'a page of a scientific paper', 'an advertisement flyer',
  ],
  'Not a document': [
    'a photo of a person', 'a photo of an animal', 'a photo of a landscape', 'a photo of a street or a city',
    'a photo of food', 'a photo of an object', 'a selfie', 'a photo of a vehicle',
  ],
};

// CLIP's own preprocessing: shortest side to 224, centre crop 224 x 224, then 7 x 7 patches of 32 x 32
const PatchGrid: React.FC<{ file: File | null }> = ({ file }) => {
  const ref = useRef<HTMLCanvasElement>(null);
  const [label, setLabel] = useState('');
  useEffect(() => {
    let url = '';
    const usable = file && file.type.startsWith('image/');
    (usable ? Promise.resolve(file as File) : fetchSample(DEFAULT_SAMPLE)).then((f) => {
      setLabel(usable ? f.name : `the sample ${DEFAULT_SAMPLE}${file ? ' (your file is a PDF)' : ''}`);
      url = URL.createObjectURL(f);
      const img = new Image();
      img.onload = () => {
        const c = ref.current;
        if (!c) return;
        const ctx = c.getContext('2d')!;
        const s = 224 / Math.min(img.width, img.height);
        const w = img.width * s, h = img.height * s;
        ctx.fillStyle = '#fff';
        ctx.fillRect(0, 0, 224, 224);
        ctx.drawImage(img, (224 - w) / 2, (224 - h) / 2, w, h);
        ctx.strokeStyle = 'rgba(217,119,6,0.95)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 7; i++) {
          ctx.beginPath(); ctx.moveTo(i * 32, 0); ctx.lineTo(i * 32, 224); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(0, i * 32); ctx.lineTo(224, i * 32); ctx.stroke();
        }
        ctx.fillStyle = 'rgba(217,119,6,0.95)';
        ctx.font = '9px Inter, sans-serif';
        for (let r = 0; r < 7; r++) for (let q = 0; q < 7; q++) ctx.fillText(String(r * 7 + q + 1), q * 32 + 2, r * 32 + 10);
      };
      img.src = url;
    });
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [file]);
  return (
    <figure className="space-y-2">
      <canvas ref={ref} width={224} height={224} className="w-full max-w-[336px] rounded-lg border border-zinc-200" />
      <figcaption className="text-[11px] text-zinc-500">Live: {label || 'loading...'}, cropped to 224 x 224 and cut into 49 patches.</figcaption>
    </figure>
  );
};

export const ClipPage: React.FC<{ file: File | null; onNavigate: (s: string) => void }> = ({ file, onNavigate }) => (
  <div className="max-w-4xl mx-auto space-y-10">
    <PageHeader kicker="How the ML works, part 3 of 5" title="Model 2: CLIP ViT-B/32, a vision-language model">
      <p>
        The second model in the cascade. It runs only when the CNN is less than 90% sure, which in practice means real-world scans
        that look unlike our training data. CLIP was <strong>never trained on our documents at all</strong>. It classifies by comparing
        the image with sentences describing each bucket. This is called <strong>zero-shot</strong> classification.
      </p>
    </PageHeader>

    <Section n={1} title="What CLIP is">
      <p>
        CLIP (Contrastive Language-Image Pre-training, OpenAI 2021) is two networks trained together: one turns an image into a
        list of 512 numbers, the other turns a sentence into a list of 512 numbers. The weights we use were trained by LAION on
        about 2 billion image and caption pairs from the internet. Training pulled the vectors of each matching image and
        caption together and pushed non-matching ones apart, so <strong>an image and a sentence that describe the same thing end up
        pointing in the same direction</strong>.
      </p>
      <Card>
        <Rows rows={[
          ['Total parameters', <span className="font-mono">151,277,313</span>],
          ['Image encoder', <span className="font-mono">87,456,000 (Vision Transformer, ViT-B/32)</span>],
          ['Text encoder', <span className="font-mono">63,165,952 (Transformer)</span>],
          ['Shared embedding size', <span className="font-mono">512</span>],
          ['Trained on our data', 'No. Zero-shot.'],
        ]} />
      </Card>
    </Section>

    <Section n={2} title="The image side: a Vision Transformer">
      <p>
        A Vision Transformer has no convolutions. It cuts the image into square patches and treats each patch like a word in a
        sentence.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 items-start">
        <PatchGrid file={file} />
        <ol className="list-decimal pl-5 space-y-1.5">
          <li>The image is resized so its short side is 224 pixels and the centre 224 x 224 is kept.</li>
          <li>It is cut into a 7 x 7 grid of <strong>49 patches</strong>, each 32 x 32 pixels x 3 channels = 3,072 numbers ("/32" in ViT-B/32).</li>
          <li>Each patch is flattened and multiplied by a learned matrix to become a 768-number vector, a <strong>token</strong>.</li>
          <li>A learned position vector is added to each token so the model knows where the patch was, and one extra <strong>CLS</strong> token is put in front: 50 tokens.</li>
          <li><strong>12 transformer layers</strong> follow. In each, every token looks at every other token through <strong>self-attention</strong> (12 heads), so a patch with a seal can learn that a patch with a signature line sits below it.</li>
          <li>The CLS token's final vector is projected to 512 numbers. That is the image's embedding.</li>
        </ol>
      </div>
      <Formula>{'Attention(Q, K, V) = softmax( Q K^T / sqrt(d) ) V\nQ, K, V: three learned projections of the tokens.  Each token gets a weighted mix of all the others.'}</Formula>
    </Section>

    <Section n={3} title="The text side: describing each bucket in words">
      <p>
        Instead of training a classifier, we wrote 7 or 8 plain-English descriptions per bucket. Each is split into sub-word tokens
        (a vocabulary of 49,408, at most 77 tokens), run through the 12-layer text transformer, and turned into a 512-number vector.
        The vectors of one bucket are averaged into a single vector for that bucket (<strong>prompt ensembling</strong>), which is more
        robust than any single sentence. These are computed once when the server starts.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {Object.entries(PROMPTS).map(([k, ps]) => (
          <Card key={k} className="space-y-1.5">
            <div className="text-sm font-semibold text-zinc-950">{k}</div>
            <ul className="text-xs text-zinc-600 space-y-0.5 list-disc pl-4">
              {ps.map((p) => <li key={p}>"{p}"</li>)}
            </ul>
          </Card>
        ))}
      </div>
    </Section>

    <Section n={4} title="Making the decision">
      <p>
        Both kinds of vector are scaled to length 1, so their dot product is the <strong>cosine similarity</strong>: 1 when they point
        the same way, 0 when unrelated. The image is compared with the four bucket vectors, the similarities are multiplied by CLIP's
        learned temperature of 100, and softmax turns them into probabilities.
      </p>
      <Formula>{'similarity_k = (image_vector . bucket_vector_k)          both of length 1\nP(bucket k)  = softmax( 100 x similarity_k )'}</Formula>
    </Section>

    <Section n={5} title="Strengths and weaknesses">
      <Card>
        <Rows rows={[
          ['Real-world scans', '6 of 6 correct, including a 1969 diploma, a Spanish diploma and a handwritten record book'],
          ['Our 448 test images', '87.1%. It sometimes confuses our generated layouts, and can be wrong while 99% sure.'],
          ['Speed', 'About 37 ms per page on the GPU. The first request after the server starts is slow (about 20 s measured) while the weights load.'],
          ['Role in Vellum', 'The backup for the CNN. It is only asked when the CNN is unsure, which is exactly where it is strong.'],
        ]} />
      </Card>
    </Section>

    <PrevNext current="learn-clip" onNavigate={onNavigate} />
  </div>
);
