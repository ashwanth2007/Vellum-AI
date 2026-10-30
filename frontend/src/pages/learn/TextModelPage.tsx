import React from 'react';
import { Card, Formula, PageHeader, PrevNext, Rows, Section } from './shared';

// the highest-weighted single words per class in models/document_text_model.joblib
const TOP_WORDS: [string, string][] = [
  ['Certificate', 'certificate'],
  ['Academic record', 'pass, grade, student, programme'],
];

export const TextModelPage: React.FC<{ onNavigate: (s: string) => void }> = ({ onNavigate }) => (
  <div className="max-w-4xl mx-auto space-y-10">
    <PageHeader kicker="How the ML works, part 4 of 5" title="Model 3: OCR and the TF-IDF text model">
      <p>
        The third model classifies a document from the <strong>words</strong> on it rather than its pixels. To get the words, the page
        first goes through OCR (optical character recognition). The same OCR output is also what the field extractor reads to pull
        out the name, register number and CGPA, so OCR runs for every relevant document even when this model is not needed.
      </p>
    </PageHeader>

    <Section n={1} title="OCR: from pixels to text">
      <p>Vellum uses RapidOCR, which runs Baidu's PP-OCRv4 models through ONNX Runtime on the CPU. It is three neural networks in a row:</p>
      <ol className="list-decimal pl-5 space-y-1.5">
        <li><strong>Text detection.</strong> A convolutional network (DBNet style) outputs, for every pixel, the probability that it is part of text. Pixels above 0.3 are grouped into regions and each region becomes a box around one line of text.</li>
        <li><strong>Direction check.</strong> A small classifier looks at each line crop (48 x 192 pixels) and decides whether it is upright or upside down (0 or 180 degrees), and flips it if needed.</li>
        <li><strong>Text recognition.</strong> Each line is resized to 48 pixels tall and read left to right by a recognition network that outputs a probability for every character at every horizontal position. <strong>CTC decoding</strong> then merges repeated characters and removes blanks to give the final string, with a confidence score.</li>
      </ol>
      <Card>
        <Rows rows={[
          ['Output', 'Every text line, its box on the page and its confidence. These are the green boxes on the result page.'],
          ['Speed', '4 to 15 s per page measured on the 6 real scans. By far the slowest step, which is why it runs only when needed.'],
          ['Weak on', 'Handwriting, very small print, heavy blur'],
        ]} />
      </Card>
    </Section>

    <Section n={2} title="TF-IDF: turning text into numbers">
      <p>
        A classifier needs numbers, not words. TF-IDF gives each word a score that is high when the word appears often in
        <em> this</em> document but rarely across all documents. So "certificate" on a certificate scores high, while "the" scores
        near zero because it is everywhere.
      </p>
      <Formula>{'tf-idf(t, d) = (1 + log tf(t, d)) x idf(t)          tf: count of term t in document d\nidf(t)       = log( (1 + N) / (1 + df(t)) ) + 1     N: documents, df: documents containing t\nthen the whole vector is scaled to length 1'}</Formula>
      <p>Two vocabularies are learned from the training text and joined into one vector of <strong>32,597</strong> numbers per document:</p>
      <Card>
        <Rows rows={[
          ['Word features', '5,517 single words and two-word phrases ("grade sheet"), kept if they appear in at least 2 documents'],
          ['Character features', '27,080 groups of 3 to 5 letters ("cert", "grad"). These still match when OCR misreads one letter of a word.'],
        ]} />
      </Card>
    </Section>

    <Section n={3} title="Logistic regression: the classifier">
      <p>
        Multinomial logistic regression learns one weight per feature per bucket: 4 x 32,597 weights. For a document it adds up
        weight x feature for each bucket and softmax turns the four sums into probabilities. A large positive weight means "this
        word is evidence for this bucket".
      </p>
      <Formula>{'score_k = w_k . x + b_k        x: the 32,597 TF-IDF numbers\nP(bucket k) = softmax(score)_k'}</Formula>
      <Card>
        <div className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 mb-2">Strongest word evidence the model learned</div>
        <Rows rows={TOP_WORDS} />
      </Card>
      <p>
        It was trained with class balancing (so a class with fewer examples counts as much) and a regularisation strength of C = 4.
        It is used only if OCR finds at least 5 words, so it never runs on a photo with no text.
      </p>
    </Section>

    <Section n={4} title="How well it works, honestly">
      <Card>
        <Rows rows={[
          ['Test images with text (362)', '96.7% correct'],
          ['Real-world scans (6)', '0 of 6. Their text (old print, handwriting, a Spanish diploma) looks nothing like the text of our training documents.'],
          ['Role in Vellum', 'The last resort: it is reached only if both image models are under 90% sure. In our evaluation that never happened.'],
        ]} />
      </Card>
    </Section>

    <PrevNext current="learn-text" onNavigate={onNavigate} />
  </div>
);
