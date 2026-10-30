import React from 'react';
import { CLASS_NAMES, DOC_CLASSES } from '../../lib/api';
import { Card, Formula, LiveStatus, PageHeader, PrevNext, Rows, Section, useCnnExplanation } from './shared';

// torchvision efficientnet_b0 .features, index by index
const STAGE_INFO = [
  { name: 'Stem', op: '3 x 3 convolution, stride 2, BatchNorm, SiLU', blocks: 1 },
  { name: 'Stage 1', op: 'MBConv1, 3 x 3 depthwise', blocks: 1 },
  { name: 'Stage 2', op: 'MBConv6, 3 x 3 depthwise, stride 2', blocks: 2 },
  { name: 'Stage 3', op: 'MBConv6, 5 x 5 depthwise, stride 2', blocks: 2 },
  { name: 'Stage 4', op: 'MBConv6, 3 x 3 depthwise, stride 2', blocks: 3 },
  { name: 'Stage 5', op: 'MBConv6, 5 x 5 depthwise', blocks: 3 },
  { name: 'Stage 6', op: 'MBConv6, 5 x 5 depthwise, stride 2', blocks: 4 },
  { name: 'Stage 7', op: 'MBConv6, 3 x 3 depthwise', blocks: 1 },
  { name: 'Head conv', op: '1 x 1 convolution to 1280 channels, BatchNorm, SiLU', blocks: 1 },
];

const n = (v: number) => v.toLocaleString('en-US');

export const CnnPage: React.FC<{ file: File | null; onNavigate: (s: string) => void }> = ({ file, onNavigate }) => {
  const { data, error, source } = useCnnExplanation(file);
  return (
    <div className="max-w-5xl mx-auto space-y-10">
      <PageHeader kicker="How the ML works, part 2 of 5" title="Model 1: EfficientNet-B0, a convolutional neural network">
        <p>
          The first model in the cascade, and the one that answers most documents. It is a CNN that looks only at the pixels. It is
          the fastest of the three (about 37 ms per page on the RTX 4060 laptop GPU) and it scored 100% on the 448 held-out test images.
        </p>
      </PageHeader>

      <Section n={1} title="Why this network">
        <p>
          EfficientNet-B0 (Tan and Le, Google, 2019) is the smallest member of a family designed by scaling depth, width and input
          resolution together instead of making one of them huge. It reaches high accuracy with only about 4 million weights, small
          enough to train on a laptop GPU in minutes. We did not train it from scratch: we started from weights already trained on
          ImageNet (1.28 million photos, 1,000 classes), so it already knew edges, textures and shapes, and then
          <strong> fine-tuned</strong> every layer on our documents. This is called <strong>transfer learning</strong>.
        </p>
        <Card>
          <Rows rows={[
            ['Total parameters', <span className="font-mono">4,336,512</span>],
            ['Convolutional part', <span className="font-mono">4,007,548</span>],
            ['Our classification head', <span className="font-mono">328,964</span>],
            ['Input', '320 x 320 RGB, letterboxed (resized keeping the aspect ratio, padded with grey)'],
            ['Output', '4 probabilities, one per bucket'],
          ]} />
        </Card>
      </Section>

      <Section n={2} title="The building block: MBConv">
        <p>Every stage after the stem is a stack of <strong>MBConv</strong> (mobile inverted bottleneck) blocks. Each block does four things in order:</p>
        <ol className="list-decimal pl-5 space-y-1.5">
          <li><strong>Expand:</strong> a 1 x 1 convolution multiplies the channel count by 6 (MBConv6), giving the block more room to work.</li>
          <li><strong>Depthwise convolution:</strong> a 3 x 3 or 5 x 5 kernel filters each channel on its own. This is far cheaper than a normal convolution, which mixes all channels at every position.</li>
          <li><strong>Squeeze and excitation:</strong> the block averages each channel to one number, passes those through a tiny two-layer network, and uses the result to scale each channel up or down. It learns which channels matter for this image.</li>
          <li><strong>Project:</strong> a 1 x 1 convolution shrinks the channels back down. If the shape did not change, the block's input is added to its output (a <strong>skip connection</strong>), which keeps training stable in deep networks.</li>
        </ol>
      </Section>

      <Section n={3} title="Live: what each stage sees in your document">
        <p>
          Below, the document is run through the real trained network. For every stage you see its output shape and the 6 channels
          (feature maps) that fired most strongly. Bright means high activation. Watch the resolution fall and the patterns become
          more abstract: early maps still look like the page, late maps are coarse 10 x 10 grids that encode "certificate-like
          layout here".
        </p>
        {data ? (
          <div className="space-y-3">
            <Card className="flex flex-wrap items-center gap-4">
              <img src={data.input.image} alt="Network input" className="w-28 h-28 rounded-lg border border-zinc-200" />
              <div className="text-sm text-zinc-700 space-y-1">
                <div><strong>Input:</strong> {source}</div>
                <div className="font-mono text-xs">320 x 320 x 3 = 307,200 numbers</div>
              </div>
            </Card>
            {data.stages.map((st) => {
              const info = STAGE_INFO[st.index];
              const [c, h, w] = st.shape;
              return (
                <Card key={st.index} className="space-y-3">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <div>
                      <span className="text-sm font-semibold text-zinc-950">{info.name}</span>
                      <span className="text-xs text-zinc-500"> {info.op}{info.blocks > 1 ? `, ${info.blocks} blocks` : ''}</span>
                    </div>
                    <span className="font-mono text-xs text-zinc-700">
                      {h} x {w} x {c} = {n(h * w * c)} numbers, {n(st.params)} weights
                    </span>
                  </div>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                    {st.maps.map((m) => (
                      <figure key={m.channel} className="space-y-0.5">
                        <img src={m.image} alt={`Channel ${m.channel}`} className="w-full aspect-square rounded border border-zinc-200 [image-rendering:pixelated]" />
                        <figcaption className="text-[10px] text-zinc-500 text-center font-mono">ch {m.channel}</figcaption>
                      </figure>
                    ))}
                  </div>
                </Card>
              );
            })}
            <Card className="space-y-3">
              <div className="text-sm font-semibold text-zinc-950">Global average pooling, then the head</div>
              <p className="text-xs text-zinc-600">
                Each of the 1280 final 10 x 10 maps is averaged to a single number, giving a vector of {data.pooled.length}. The strongest 12 for this page:
              </p>
              <div className="flex flex-wrap gap-1.5">
                {data.pooled.top.map((t) => (
                  <span key={t.index} className="font-mono text-[11px] bg-zinc-100 border border-zinc-200 rounded px-2 py-0.5">#{t.index}: {t.value}</span>
                ))}
              </div>
              <Formula>{`1280  ->  Linear(1280, 256) + ReLU  ->  Dropout(0.3)  ->  Linear(256, 4)  ->  softmax`}</Formula>
              <div className="space-y-1.5">
                {DOC_CLASSES.map((k) => (
                  <div key={k} className="grid grid-cols-[130px_1fr_60px] items-center gap-2 text-xs">
                    <span className="text-zinc-700">{CLASS_NAMES[k]}</span>
                    <div className="h-2.5 rounded-full bg-zinc-100 overflow-hidden">
                      <div className="h-full rounded-full bg-zinc-900" style={{ width: `${Math.max(1, data.probabilities[k] * 100)}%` }} />
                    </div>
                    <span className="font-mono text-right">{(data.probabilities[k] * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        ) : <Card><LiveStatus error={error} source={source} /></Card>}
      </Section>

      <Section n={4} title="How it was trained">
        <Card>
          <Rows rows={[
            ['Data', '1,944 training, 407 validation, 448 test images: generated certificates, grade sheets, letters and LORs, plus RVL-CDIP and FUNSD scanned documents and Flickr and Imagenette photos'],
            ['Augmentation', 'Random rotation up to 4 degrees, shifts, zoom 0.9 to 1.08, colour jitter, 15% turned grey. So the model does not memorise exact pixels.'],
            ['Loss', 'Cross-entropy, weighted by class frequency, label smoothing 0.05'],
            ['Optimiser', 'AdamW, learning rate 0.0006 with a one-cycle schedule, weight decay 0.0001'],
            ['Schedule', '12 epochs, batch size 32, mixed precision on the GPU, about 13 s per epoch'],
            ['Result', '100% on the 448 test images (all four classes)'],
          ]} />
        </Card>
      </Section>

      <Section n={5} title="Its weakness, and why it does not work alone">
        <p>
          On 6 genuine scans from Wikimedia Commons that look nothing like the training data (a 1969 PhD diploma, a Spanish diploma,
          a handwritten record book), it got only <strong>1 of 6</strong> right. It learned the look of our training documents too
          well. But it was never more than 89% sure on those mistakes, while every correct test answer was at least 91.6% sure. So
          the cascade only trusts it at 90% or above, and passes everything else to CLIP.
        </p>
      </Section>

      <PrevNext current="learn-cnn" onNavigate={onNavigate} />
    </div>
  );
};
