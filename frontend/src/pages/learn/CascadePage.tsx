import React from 'react';
import { ArrowDown, CheckCircle2 } from 'lucide-react';
import { AnalysisResult } from '../../lib/api';
import { Card, Formula, PageHeader, PrevNext, Rows, Section } from './shared';

const STAGES = [
  { name: 'EfficientNet-B0 CNN', time: '~37 ms', rule: 'Accept if at least 90% sure', why: 'Fastest, and 100% on the test images' },
  { name: 'CLIP ViT-B/32', time: '~37 ms', rule: 'Accept if at least 90% sure', why: 'Strong on real-world scans the CNN has never seen' },
  { name: 'OCR + text model', time: '4 to 15 s', rule: 'Always accept (last resort)', why: 'Slowest, because OCR must run first' },
];

const REQUIREMENTS: [string, string][] = [
  ['Support multiple file types', 'PNG, JPG, WEBP, BMP, TIFF, GIF and PDF (first 5 pages). Anything else is refused with a message.'],
  ['Process files using three models', 'All three are available and wired in: CNN, CLIP and the text model.'],
  ['Return only the best and fastest result', 'Models are ordered fastest first. The first one confident enough answers.'],
  ['Do not compare all three models', 'The result page shows one model\'s answer only. The others\' outputs are never shown, and usually never computed.'],
  ['Stop once a suitable result is available', 'The cascade returns the moment a model clears its threshold. Later models do not run at all.'],
];

export const CascadePage: React.FC<{ result: AnalysisResult | null; onNavigate: (s: string) => void }> = ({ result, onNavigate }) => {
  const dec = result?.classification.decision;
  return (
    <div className="max-w-4xl mx-auto space-y-10">
      <PageHeader kicker="How the ML works, part 5 of 5" title="How one model is picked: the early-exit cascade">
        <p>
          Vellum has three models but returns one answer from one model. It asks them one at a time, fastest first, and stops as soon
          as one is confident. This pattern is called an <strong>early-exit cascade</strong>, the same idea as the classic Viola-Jones
          face detector: cheap tests first, expensive ones only when needed.
        </p>
      </PageHeader>

      <Section n={1} title="The flow">
        <div className="space-y-2">
          {STAGES.map((s, i) => (
            <React.Fragment key={s.name}>
              <Card className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-2 items-center">
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Try {i + 1}</div>
                  <div className="text-base font-semibold text-zinc-950">{s.name}</div>
                  <div className="text-xs text-zinc-600">{s.why}</div>
                </div>
                <div className="sm:text-right space-y-0.5">
                  <div className="font-mono text-xs text-zinc-700">{s.time}</div>
                  <div className="text-xs font-medium text-emerald-700 flex sm:justify-end items-center gap-1"><CheckCircle2 className="h-3.5 w-3.5" /> {s.rule}: answer and stop</div>
                </div>
              </Card>
              {i < STAGES.length - 1 && (
                <div className="flex items-center justify-center gap-2 text-[11px] text-zinc-500"><ArrowDown className="h-4 w-4" /> under 90% sure: ask the next model</div>
              )}
            </React.Fragment>
          ))}
        </div>
        <p>
          If no model reaches its threshold, the most confident answer seen is returned and marked as low confidence on the result page.
        </p>
      </Section>

      <Section n={2} title="Why the threshold is 90%">
        <p>
          The threshold was measured, not guessed. "Best" needs a way to judge quality without knowing the right answer, and the
          model's own confidence (its top softmax probability) is that signal, as long as a confident answer is a correct one. We
          checked exactly that on held-out data:
        </p>
        <Card>
          <Rows rows={[
            ['CNN, correct answers on 448 test images', 'lowest confidence 91.6%'],
            ['CNN, wrong answers on the real scans', 'highest confidence 88.9%'],
            ['So a threshold of 90%', 'keeps every correct CNN answer and rejects every wrong one, which then go to CLIP'],
            ['CLIP on the real scans', 'every answer correct and at least 94.7% sure'],
          ]} />
        </Card>
        <Formula>{'for model in [CNN, CLIP, text]:\n    p = model(page)\n    if max(p) >= threshold[model]:\n        return model, argmax(p)          # the remaining models never run\nreturn the most confident answer seen'}</Formula>
      </Section>

      <Section n={3} title="Measured result">
        <Card>
          <Rows rows={[
            ['448 test images', '448 correct (100%). All answered by the CNN, CLIP never needed.'],
            ['6 real-world scans', '6 correct (100%). 1 answered by the CNN, 5 passed on to CLIP.'],
            ['Text model', 'Never needed in either set'],
            ['A rejected photo', 'About 40 ms end to end, because OCR is skipped when the page is not a credential'],
          ]} />
        </Card>
        <p className="text-xs text-zinc-500">
          Source: <span className="font-mono">python -m ml.document_classifier.evaluate</span>, saved in models/document_classifier_metrics.json.
          This is the same accuracy as the earlier version that ran all three models and averaged them, at a fraction of the work.
          Caveat: the real-world set is only 6 scans, so the 90% rule should be re-checked as more real documents are added.
        </p>
      </Section>

      <Section n={4} title="Against ma'am's requirements">
        <Card>
          <Rows rows={REQUIREMENTS} />
        </Card>
      </Section>

      {dec && (
        <Section n={5} title="Your last run">
          <Card>
            <Rows rows={[
              ['File', result!.document_name],
              ['Answered by', dec.model_name],
              ['Confidence', `${(result!.classification.confidence * 100).toFixed(1)}% (threshold ${(dec.threshold * 100).toFixed(0)}%)`],
              ['Models that ran', String(dec.models_run.length)],
              ['Time to decide', `${dec.decision_ms.toFixed(0)} ms`],
            ]} />
          </Card>
        </Section>
      )}

      <PrevNext current="learn-cascade" onNavigate={onNavigate} />
    </div>
  );
};
