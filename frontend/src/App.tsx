import React, { useEffect, useState } from 'react';
import { AppLayout } from './layouts/AppLayout';
import { DocumentUploadPage } from './pages/DocumentUploadPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { AnalysisResultPage } from './pages/AnalysisResultPage';
import { HandbookPage } from './pages/HandbookPage';
import { FoundationsPage } from './pages/learn/FoundationsPage';
import { CnnPage } from './pages/learn/CnnPage';
import { ClipPage } from './pages/learn/ClipPage';
import { TextModelPage } from './pages/learn/TextModelPage';
import { CascadePage } from './pages/learn/CascadePage';
import { analyzeFile, AnalysisResult, fetchSample } from './lib/api';

export function App() {
  const [currentScreen, setCurrentScreen] = useState<string>('upload');
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [runStatus, setRunStatus] = useState<'running' | 'done' | 'error'>('running');
  const [runError, setRunError] = useState<string>('');
  const [runFile, setRunFile] = useState<string>('');
  // the last uploaded file, so the explainer tabs can run the real models on the user's own document
  const [lastFile, setLastFile] = useState<File | null>(null);

  const handleStartProcessing = async (file: File) => {
    setRunFile(file.name);
    setLastFile(file);
    setRunStatus('running');
    setRunError('');
    setCurrentScreen('processing');
    try {
      const res = await analyzeFile(file);
      setAnalysis(res);
      setRunStatus('done');
      return true;
    } catch (e: any) {
      setRunError(e?.message || 'Analysis failed.');
      setRunStatus('error');
      return false;
    }
  };

  // ?sample=<file in demo_samples> runs that file straight through the real pipeline (live demo and screenshots)
  // ?screen=<id> opens a tab directly
  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    const screen = q.get('screen');
    if (screen) setCurrentScreen(screen);
    const name = q.get('sample');
    if (!name) return;
    fetchSample(name)
      .then(async (f) => {
        if ((await handleStartProcessing(f)) && !screen) setCurrentScreen('result');
        else if (screen) setCurrentScreen(screen);
      })
      .catch((e) => { setRunFile(name); setRunError(e.message); setRunStatus('error'); setCurrentScreen('processing'); });
  }, []);

  return (
    <AppLayout currentScreen={currentScreen} onNavigate={setCurrentScreen}>
      {currentScreen === 'handbook' && <HandbookPage onNavigate={setCurrentScreen} />}

      {currentScreen === 'upload' && <DocumentUploadPage onStartProcessing={handleStartProcessing} />}

      {currentScreen === 'processing' && (
        <ProcessingPage
          fileName={runFile}
          status={runStatus}
          result={analysis}
          error={runError}
          onComplete={() => setCurrentScreen('result')}
          onBack={() => setCurrentScreen('upload')}
        />
      )}

      {currentScreen === 'result' && (
        <AnalysisResultPage result={analysis} onAnalyzeAnother={() => setCurrentScreen('upload')} onLearn={setCurrentScreen} />
      )}

      {currentScreen === 'learn-foundations' && <FoundationsPage file={lastFile} onNavigate={setCurrentScreen} />}
      {currentScreen === 'learn-cnn' && <CnnPage file={lastFile} onNavigate={setCurrentScreen} />}
      {currentScreen === 'learn-clip' && <ClipPage file={lastFile} onNavigate={setCurrentScreen} />}
      {currentScreen === 'learn-text' && <TextModelPage onNavigate={setCurrentScreen} />}
      {currentScreen === 'learn-cascade' && <CascadePage result={analysis} onNavigate={setCurrentScreen} />}

      {/* ?screen=learn-all stacks the five "How the ML works" tabs into one printable document */}
      {currentScreen === 'learn-all' && (
        <div className="learn-all space-y-16">
          <FoundationsPage file={lastFile} onNavigate={setCurrentScreen} />
          <div className="print-break"><CnnPage file={lastFile} onNavigate={setCurrentScreen} /></div>
          <div className="print-break"><ClipPage file={lastFile} onNavigate={setCurrentScreen} /></div>
          <div className="print-break"><TextModelPage onNavigate={setCurrentScreen} /></div>
          <div className="print-break"><CascadePage result={analysis} onNavigate={setCurrentScreen} /></div>
        </div>
      )}

    </AppLayout>
  );
}

export default App;
