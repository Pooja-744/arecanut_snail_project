import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import Layout from './pages/Layout';
import HomePage from './pages/HomePage';
import CaptureUploadPage from './pages/CaptureUploadPage';
import AnalysisLoadingPage from './pages/AnalysisLoadingPage';
import ResultsPage from './pages/ResultsPage';
import ReportsHistoryPage from './pages/ReportsHistoryPage';
import ModelAdminPage from './pages/ModelAdminPage';
import ProfilePage from './pages/ProfilePage';

function AppContent() {
  const { isAuthenticated } = useAuth();
  const [currentPage, setCurrentPage] = useState('overview'); // overview, capture, analyzing, results, history, admin, profile
  const [pageHistory, setPageHistory] = useState(['overview']);
  const [activeImageFile, setActiveImageFile] = useState(null);
  const [activePreviewUrl, setActivePreviewUrl] = useState(null);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);

  // If unauthenticated, show professional Login Page
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const navigateTo = (page) => {
    if (page === currentPage) return;
    setPageHistory((prev) => [...prev, page]);
    setCurrentPage(page);
  };

  const handleGoBack = () => {
    if (pageHistory.length > 1) {
      const nextHistory = [...pageHistory];
      nextHistory.pop(); // remove current
      const prev = nextHistory[nextHistory.length - 1];
      setPageHistory(nextHistory);
      setCurrentPage(prev);
    } else {
      setCurrentPage('overview');
    }
  };

  // Handle workflow step: Image ready -> Go to Analysis
  const handleProceedToAnalysis = (file, previewUrl) => {
    setActiveImageFile(file);
    setActivePreviewUrl(previewUrl);
    navigateTo('analyzing');
  };

  // Handle workflow step: Analysis complete -> Go to Results
  const handleAnalysisComplete = (data, previewUrl) => {
    setCurrentAnalysis(data);
    setActivePreviewUrl(previewUrl);
    navigateTo('results');
  };

  const handleCancelAnalysis = () => {
    navigateTo('capture');
  };

  return (
    <Layout
      currentPage={currentPage}
      onNavigate={navigateTo}
      onGoBack={handleGoBack}
      currentAnalysis={currentAnalysis}
    >
      {currentPage === 'overview' && (
        <HomePage onNavigate={navigateTo} />
      )}

      {currentPage === 'capture' && (
        <CaptureUploadPage onProceedToAnalysis={handleProceedToAnalysis} />
      )}

      {currentPage === 'analyzing' && (
        <AnalysisLoadingPage
          imageFile={activeImageFile}
          previewUrl={activePreviewUrl}
          onAnalysisComplete={handleAnalysisComplete}
          onCancel={handleCancelAnalysis}
        />
      )}

      {currentPage === 'results' && (
        <ResultsPage
          analysisData={currentAnalysis}
          originalPreview={activePreviewUrl}
          onNavigate={navigateTo}
        />
      )}

      {currentPage === 'history' && (
        <ReportsHistoryPage
          onNavigate={navigateTo}
          onViewAnalysis={(item) => {
            setCurrentAnalysis(item);
            navigateTo('results');
          }}
        />
      )}

      {currentPage === 'admin' && (
        <ModelAdminPage />
      )}

      {currentPage === 'profile' && (
        <ProfilePage />
      )}
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
