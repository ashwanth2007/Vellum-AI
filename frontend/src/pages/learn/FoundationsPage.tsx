import React from 'react';
import { Card, Formula, LiveStatus, PageHeader, PrevNext, Rows, Section, useCnnExplanation } from './shared';

// A 6x6 patch of a dark vertical stroke on white paper, and a vertical-edge kernel.
const PATCH = [
  [250, 250, 30, 30, 250, 250],
  [250, 250, 30, 30, 250, 250],
  [250, 250, 30, 30, 250, 250],
  [250, 250, 30, 30, 250, 250],
  [250, 250, 30, 30, 250, 250],
  [250, 250, 30, 30, 250, 250],
];
const KERNEL = [
  [-1, 0, 1],
  [-1, 0, 1],
  [-1, 0, 1],
];
const conv = (img: number[][], k: number[][]) => {
  const out: number[][] = [];
  for (let y = 0; y <= img.length - 3; y++) {
    const row: number[] = [];
    for (let x = 0; x <= img[0].length - 3; x++) {
      let s = 0;
      for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) s += img[y + i][x + j] * k[i][j];
      row.push(s);
    }
    out.push(row);
  }
  return out;
};
const OUT = conv(PATCH, KERNEL);

const Grid: React.FC<{ m: number[][]; scale: (v: number) => string; ink: (v: number) => string; title: string; highlight?: boolean }> = ({ m, scale, ink, title, highlight }) => (
  <div className="space-y-1.5">
    <div className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">{title}</div>
    <div className="inline-grid gap-0.5" style={{ gridTemplateColumns: `repeat(${m[0].length}, minmax(0, 1fr))` }}>
      {m.flatMap((row, y) => row.map((v, x) => (
        <div key={`${y}-${x}`}
          className={`w-10 h-10 sm:w-11 sm:h-11 flex items-center justify-center font-mono text-[10px] rounded ${highlight && y < 3 && x < 3 ? 'ring-2 ring-amber-500' : ''}`}
          style={{ background: scale(v), color: ink(v) }}>
          {v}
        </div>
      )))}
    </div>
  </div>
);

const STAGES_STATIC = [
  ['Input image (letterboxed)', '320 x 320 x 3', '307,200'],
  ['Stem convolution, stride 2', '160 x 160 x 32', '819,200'],
  ['After stages 1 to 3', '40 x 40 x 40', '64,000'],
  ['After stages 4 and 5', '20 x 20 x 112', '44,800'],
  ['After stages 6 and 7', '10 x 10 x 320', '32,000'],
  ['Final 1x1 convolution', '10 x 10 x 1280', '128,000'],
  ['Global average pooling', '1280', '1,280'],
  ['Dense layer + ReLU', '256', '256'],
  ['Output layer + softmax', '4 (one per bucket)', '4'],
];

export const FoundationsPage: React.FC<{ file: File | null; onNavigate: (s: string) => void }> = ({ file, onNavigate }) => {
  const { data, error, source } = useCnnExplanation(file);
  return (
    <div className="max-w-4xl mx-auto space-y-10">
      <PageHeader kicker="How the ML works, part 1 of 5" title="Foundations: from pixels to a prediction">
        <p>
          Every model in Vellum starts from the same thing: an image is just a grid of numbers. This page builds up, step by step,
          how a neural network turns that grid into one of four answers. It covers the Module 7 topics of perception, image
          formation and object recognition.
        </p>
      </PageHeader>

      <Section n={1} title="An image is a grid of numbers">
        <p>
          A digital image is made of pixels. Each pixel stores three numbers, the brightness of <strong>red</strong>,{' '}
          <strong>green</strong> and <strong>blue</strong> light, each from 0 (none) to 255 (full). So a colour image is really three
          grids stacked on top of each other. These grids are called <strong>channels</strong>.
        </p>
        <Card className="space-y-3">
          {data ? (
            <>
              <div className="text-xs text-zinc-500">Live: the document {source}, split into its three channels. Brighter means more of that colour.</div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <figure className="space-y-1">
                  <img src={data.input.image} alt="Input document" className="w-full rounded-lg border border-zinc-200" />
                  <figcaption className="text-[11px] text-zinc-600 text-center">Full colour</figcaption>
                </figure>
                {['Red', 'Green', 'Blue'].map((c, i) => (
                  <figure key={c} className="space-y-1">
                    <img src={data.input.channels[i]} alt={`${c} channel`} className="w-full rounded-lg border border-zinc-200" />
                    <figcaption className="text-[11px] text-zinc-600 text-center">{c} channel (0 to 255)</figcaption>
                  </figure>
                ))}
              </div>
            </>
          ) : <LiveStatus error={error} source={source} />}
        </Card>
        <p>
          In code this becomes a <strong>tensor</strong>: a block of numbers with a shape. Vellum resizes every page to 320 x 320
          (padding with grey so the document keeps its shape), giving a tensor of shape <strong>3 x 320 x 320 = 307,200 numbers</strong>.
          Before the network sees them, each value is scaled to 0 to 1 and normalised with the ImageNet statistics the CNN was
          originally trained with:
        </p>
        <Formula>{'x_normalised = (pixel / 255 - mean) / std\nmean = [0.485, 0.456, 0.406]   std = [0.229, 0.224, 0.225]   (one value per R, G, B)'}</Formula>
      </Section>

      <Section n={2} title="Machine learning and deep learning">
        <p>
          <strong>Machine learning</strong> means the program learns its rules from examples instead of a person writing them. It is
          shown thousands of labelled documents and adjusts numbers (weights) until its answers match the labels.
        </p>
        <Card>
          <Rows rows={[
            ['Classic machine learning', 'A person decides what to measure (the features), the algorithm learns how to weigh them. In Vellum: the text model. A person chose "count words and letter groups", logistic regression learned which ones matter.'],
            ['Deep learning', 'The network learns the features too, straight from the raw pixels, through many stacked layers. In Vellum: the EfficientNet-B0 CNN and CLIP. Nobody told them what a seal or a table looks like.'],
          ]} />
        </Card>
      </Section>

      <Section n={3} title="A neuron, and a network of them">
        <p>A single artificial neuron multiplies each input by a weight, adds them up with a bias, and passes the sum through an activation function:</p>
        <Formula>{'output = activation( w1*x1 + w2*x2 + ... + wn*xn + b )\nReLU(z) = max(0, z)        SiLU(z) = z * sigmoid(z)   (the one EfficientNet uses)'}</Formula>
        <p>
          A layer is many neurons side by side; a network is many layers in a row. The last layer of Vellum's CNN has 4 neurons,
          one per bucket. Their raw scores go through <strong>softmax</strong>, which turns them into probabilities that add up to 1:
        </p>
        <Formula>{'P(class i) = e^(score_i) / ( e^(score_1) + e^(score_2) + e^(score_3) + e^(score_4) )'}</Formula>
        <p>
          <strong>Training</strong> repeats three steps thousands of times: predict, measure how wrong the prediction was with the
          cross-entropy loss (<span className="font-mono">loss = -log P(correct class)</span>), then nudge every weight a little in the
          direction that lowers the loss. Working out that direction for every weight at once is called <strong>backpropagation</strong>;
          the nudging is <strong>gradient descent</strong> (Vellum uses the AdamW variant).
        </p>
      </Section>

      <Section n={4} title="Convolution: how a CNN looks at pixels">
        <p>
          A fully connected layer on 307,200 inputs would need millions of weights per neuron and would ignore the fact that nearby
          pixels belong together. A <strong>convolutional layer</strong> instead slides a small grid of weights, a <strong>kernel</strong>,
          across the image. At each position it multiplies the 3 x 3 pixels under it by the 9 weights and adds them up. The result is
          a new grid called a <strong>feature map</strong>.
        </p>
        <Card className="space-y-4">
          <div className="flex flex-wrap items-start gap-6">
            <Grid m={PATCH} title="Input: a dark stroke on paper" highlight scale={(v) => `rgb(${v},${v},${v})`} ink={(v) => (v < 128 ? '#fff' : '#18181b')} />
            <Grid m={KERNEL} title="Kernel: vertical edge detector" scale={(v) => (v > 0 ? '#bbf7d0' : v < 0 ? '#fecaca' : '#f4f4f5')} ink={() => '#18181b'} />
            <Grid m={OUT} title="Feature map (4 x 4)" scale={(v) => (v > 0 ? `rgba(5,150,105,${Math.min(1, v / 700)})` : v < 0 ? `rgba(225,29,72,${Math.min(1, -v / 700)})` : '#f4f4f5')} ink={(v) => (Math.abs(v) > 300 ? '#fff' : '#18181b')} />
          </div>
          <p className="text-xs text-zinc-600">
            Worked out by this page in your browser. The amber 3 x 3 window gives (30+30+30) - (250+250+250) = {OUT[0][0]}: a strong
            negative where paper turns to ink, a strong positive where ink turns back to paper, and 0 where nothing changes.
            The kernel has found the two edges of the stroke.
          </p>
        </Card>
        <p>
          In a real CNN the kernel weights are not written by hand: they are <strong>learned</strong> during training. Early layers end up
          detecting edges and corners, middle layers combine them into strokes, lines of text and table borders, and deep layers
          respond to whole layouts such as a certificate's border and seal. A layer runs many kernels at once, and each kernel
          produces one channel of the output. That is why the channel count grows (3, then 32, then up to 1280) while the image shrinks.
        </p>
      </Section>

      <Section n={5} title="How 307,200 numbers become 4">
        <p>
          A convolution with <strong>stride 2</strong> moves its kernel two pixels at a time, so its output is half as wide and half as
          tall. EfficientNet-B0 does this five times, so 320 pixels become 320 / 2^5 = <strong>10</strong>. Meanwhile the number of
          channels grows. So the network trades <em>where</em> things are for <em>what</em> they are. Finally, <strong>global average
          pooling</strong> takes the mean of each 10 x 10 channel, leaving one number per channel, and two dense layers map those 1280
          numbers to the 4 buckets.
        </p>
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wider text-zinc-500 border-b border-zinc-200">
                <th className="py-2 pr-3 font-semibold">Step</th><th className="py-2 pr-3 font-semibold">Shape (H x W x channels)</th><th className="py-2 font-semibold text-right">Numbers</th>
              </tr>
            </thead>
            <tbody>
              {STAGES_STATIC.map(([a, b, c]) => (
                <tr key={a} className="border-b border-zinc-100 last:border-0">
                  <td className="py-2 pr-3 text-zinc-700">{a}</td>
                  <td className="py-2 pr-3 font-mono text-zinc-900">{b}</td>
                  <td className="py-2 font-mono text-right text-zinc-900">{c}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-zinc-500 pt-3">These shapes are read from the trained model, not from a textbook. The next tab shows what each stage actually produces.</p>
        </Card>
      </Section>

      <PrevNext current="learn-foundations" onNavigate={onNavigate} />
    </div>
  );
};
