import React, { useState, useEffect } from 'react';
import { Cpu, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function AnalysisLoadingPage({ imageFile, previewUrl, onAnalysisComplete, onCancel }) {
  const { token, lang, t } = useAuth();
  const [currentStage, setCurrentStage] = useState(1);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    let timer1, timer2, timer3;

    // Simulate multi-stage visual progress while actual backend executes
    timer1 = setTimeout(() => setCurrentStage(2), 500);
    timer2 = setTimeout(() => setCurrentStage(3), 1100);
    timer3 = setTimeout(() => setCurrentStage(4), 1700);

    // Call actual backend inference API
    const runInference = async () => {
      const formData = new FormData();
      formData.append('file', imageFile);
      formData.append('save_to_history', 'true');

      try {
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        const res = await fetch('/api/analysis/analyze', {
          method: 'POST',
          headers,
          body: formData,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Model inference failed on server.');
        }

        const data = await res.json();
        // Allow user to see final stage briefly before transitioning
        setTimeout(() => {
          onAnalysisComplete(data, previewUrl);
        }, 600);
      } catch (err) {
        console.error('Inference error:', err);
        setErrorMsg(err.message || 'Failed to analyze image with deep learning models.');
      }
    };

    runInference();

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [imageFile, token]);

  return (
    <div style={{
      maxWidth: '640px',
      margin: '40px auto',
      background: '#ffffff',
      borderRadius: '20px',
      padding: '40px 32px',
      border: '1px solid #e2e8f0',
      boxShadow: '0 8px 30px rgba(0,0,0,0.06)',
      textAlign: 'center'
    }}>
      <div style={{
        width: '72px',
        height: '72px',
        borderRadius: '50%',
        background: '#dcfce7',
        color: '#15803d',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto 20px'
      }}>
        <Cpu size={36} className="animate-spin" />
      </div>

      <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f172a', margin: '0 0 8px' }}>
        {t.analyzingTitle}
      </h2>
      <p style={{ fontSize: '0.85rem', color: '#64748b', margin: '0 0 32px' }}>
        {t.analyzingSubtitle}
      </p>

      {/* Image thumbnail */}
      {previewUrl && (
        <div style={{
          width: '120px',
          height: '120px',
          borderRadius: '12px',
          overflow: 'hidden',
          margin: '0 auto 28px',
          border: '2px solid #bbf7d0',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
        }}>
          <img src={previewUrl} alt="Target" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </div>
      )}

      {/* Error Display */}
      {errorMsg ? (
        <div style={{
          background: '#fee2e2',
          color: '#b91c1c',
          padding: '16px',
          borderRadius: '12px',
          fontSize: '0.9rem',
          marginBottom: '20px',
          textAlign: 'left',
          display: 'flex',
          gap: '12px'
        }}>
          <AlertCircle size={20} flexShrink={0} />
          <div>
            <strong>Error:</strong> {errorMsg}
            <div style={{ marginTop: '10px' }}>
              <button
                onClick={onCancel}
                style={{
                  background: '#b91c1c',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '6px 14px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Back to Image Selection
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Multi-Stage Visual Pipeline */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', textAlign: 'left', maxWidth: '440px', margin: '0 auto' }}>
          {[
            { stage: 1, label: t.stage1 },
            { stage: 2, label: t.stage2 },
            { stage: 3, label: t.stage3 },
            { stage: 4, label: t.stage4 },
          ].map((s) => {
            const isDone = currentStage > s.stage;
            const isCurrent = currentStage === s.stage;
            return (
              <div
                key={s.stage}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  background: isCurrent ? '#f0fdf4' : (isDone ? '#f8fafc' : '#ffffff'),
                  border: isCurrent ? '1px solid #86efac' : '1px solid #f1f5f9',
                  transition: 'all 0.2s'
                }}
              >
                {isDone ? (
                  <CheckCircle2 size={18} color="#16a34a" />
                ) : isCurrent ? (
                  <RefreshCw size={18} className="animate-spin" color="#15803d" />
                ) : (
                  <div style={{ width: 18, height: 18, borderRadius: '50%', border: '2px solid #cbd5e1' }} />
                )}
                <span style={{
                  fontSize: '0.825rem',
                  fontWeight: isCurrent ? 700 : 500,
                  color: isCurrent ? '#14532d' : (isDone ? '#334155' : '#94a3b8')
                }}>
                  {s.label}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
