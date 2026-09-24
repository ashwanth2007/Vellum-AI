import React, { useEffect, useState } from 'react';
import { AppLayout } from './layouts/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { DocumentUploadPage } from './pages/DocumentUploadPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { VerificationWorkspacePage } from './pages/VerificationWorkspacePage';
import { VerificationHistoryPage } from './pages/VerificationHistoryPage';
import { AuditTrailPage } from './pages/AuditTrailPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { AdministrationPage } from './pages/AdministrationPage';
import { SettingsPage } from './pages/SettingsPage';
import { AnalysisResultPage } from './pages/AnalysisResultPage';
import { analyzeFile, AnalysisResult, fetchSample } from './lib/api';
import { MOCK_DOSSIERS, INITIAL_USER } from './data/mockData';
import { Dossier, UserProfile, Verdict } from './types';

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);
  const [currentUser, setCurrentUser] = useState<UserProfile>(INITIAL_USER);
  const [currentScreen, setCurrentScreen] = useState<string>('upload');
  const [dossiers, setDossiers] = useState<Dossier[]>(MOCK_DOSSIERS);
  const [activeDossierId, setActiveDossierId] = useState<string>('case-001');

  const handleRecordDecision = (
    dossierId: string,
    verdict: Verdict,
    reason: string,
    notes: string
  ) => {
    setDossiers((prev) =>
      prev.map((d) =>
        d.id === dossierId
          ? {
              ...d,
              status: verdict,
              reasonCode: reason,
              reviewNotes: notes,
              reviewedBy: currentUser.name,
              reviewTimestamp: new Date().toISOString(),
            }
          : d
      )
    );
  };

  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [runStatus, setRunStatus] = useState<'running' | 'done' | 'error'>('running');
  const [runError, setRunError] = useState<string>('');
  const [runFile, setRunFile] = useState<string>('');

  const handleStartProcessing = async (file: File) => {
    setRunFile(file.name);
    setRunStatus('running');
    setRunError('');
    setCurrentScreen('processing');
    try {
      const res = await analyzeFile(file);
      setAnalysis(res);
      setRunStatus('done');
    } catch (e: any) {
      setRunError(e?.message || 'Analysis failed.');
      setRunStatus('error');
    }
  };

  // ?sample=<file in demo_samples> runs that file straight through the real pipeline (used for the live demo and screenshots)
  useEffect(() => {
    const name = new URLSearchParams(window.location.search).get('sample');
    if (!name) return;
    fetchSample(name)
      .then(async (f) => {
        await handleStartProcessing(f);
        setCurrentScreen('result');
      })
      .catch((e) => { setRunFile(name); setRunError(e.message); setRunStatus('error'); setCurrentScreen('processing'); });
  }, []);

  const handleProcessingComplete = () => {
    setCurrentScreen('result');
  };

  if (!isAuthenticated) {
    return (
      <LoginPage
        onLogin={(user) => {
          setCurrentUser(user);
          setIsAuthenticated(true);
          setCurrentScreen('dashboard');
        }}
      />
    );
  }

  return (
    <AppLayout
      currentScreen={currentScreen}
      onNavigate={setCurrentScreen}
      currentUser={currentUser}
      onSwitchUser={setCurrentUser}
      onLogout={() => setIsAuthenticated(false)}
    >
      {currentScreen === 'dashboard' && (
        <DashboardPage
          dossiers={dossiers}
          onSelectDossier={setActiveDossierId}
          onNavigate={setCurrentScreen}
        />
      )}

      {currentScreen === 'workspace' && (
        <VerificationWorkspacePage
          dossiers={dossiers}
          activeDossierId={activeDossierId}
          onSelectDossier={setActiveDossierId}
          onRecordDecision={handleRecordDecision}
        />
      )}

      {currentScreen === 'upload' && (
        <DocumentUploadPage onStartProcessing={handleStartProcessing} />
      )}

      {currentScreen === 'processing' && (
        <ProcessingPage
          fileName={runFile}
          status={runStatus}
          timings={analysis?.timings_ms}
          error={runError}
          onComplete={handleProcessingComplete}
          onBack={() => setCurrentScreen('upload')}
        />
      )}

      {currentScreen === 'result' && (
        <AnalysisResultPage result={analysis} onAnalyzeAnother={() => setCurrentScreen('upload')} />
      )}

      {currentScreen === 'history' && (
        <VerificationHistoryPage dossiers={dossiers} />
      )}

      {currentScreen === 'audit' && <AuditTrailPage />}

      {currentScreen === 'analytics' && <AnalyticsPage />}

      {currentScreen === 'administration' && <AdministrationPage />}

      {currentScreen === 'settings' && <SettingsPage />}
    </AppLayout>
  );
}

export default App;
