import React, { useState } from 'react';
import { User, Mail, Shield, Volume2, Bell, LogOut, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function ProfilePage() {
  const { user, lang, t, logout } = useAuth();
  const [speechRate, setSpeechRate] = useState(1.0);
  const [speechPitch, setSpeechPitch] = useState(1.0);
  const [monsoonAlerts, setMonsoonAlerts] = useState(true);
  const [pestAlerts, setPestAlerts] = useState(true);
  const [savedMsg, setSavedMsg] = useState(false);

  const handleTestVoice = () => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const testText = lang === 'kn'
      ? 'ನಮಸ್ಕಾರ! ಅಡಿಕಾಗಾರ್ಡ್ ಧ್ವನಿ ಸಹಾಯಕ ಸರಿಯಾಗಿ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತಿದೆ.'
      : 'Hello! ArecaGuard voice assistant is configured and operational.';
    const utterance = new SpeechSynthesisUtterance(testText);
    utterance.lang = lang === 'kn' ? 'kn-IN' : 'en-US';
    utterance.rate = parseFloat(speechRate);
    utterance.pitch = parseFloat(speechPitch);
    window.speechSynthesis.speak(utterance);
  };

  const handleSave = () => {
    setSavedMsg(true);
    setTimeout(() => setSavedMsg(false), 3000);
  };

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title */}
      <div>
        <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#0f172a', margin: '0 0 6px' }}>
          {t.profileTitle}
        </h2>
        <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>
          {t.profileSubtitle}
        </p>
      </div>

      {savedMsg && (
        <div style={{
          background: '#dcfce7',
          color: '#15803d',
          padding: '12px 18px',
          borderRadius: '10px',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <CheckCircle2 size={18} />
          {t.settingsSaved}
        </div>
      )}

      {/* Account Info Card */}
      <div style={{ background: '#ffffff', borderRadius: '16px', padding: '28px', border: '1px solid #e2e8f0', boxShadow: '0 2px 10px rgba(0,0,0,0.03)' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <User size={20} color="#15803d" />
          {t.accountDetails}
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
          <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #f1f5f9' }}>
            <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', marginBottom: '4px' }}>{t.fullName}</span>
            <strong style={{ fontSize: '0.95rem', color: '#1e293b' }}>{user?.name || 'Arecanut Grower'}</strong>
          </div>

          <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #f1f5f9' }}>
            <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', marginBottom: '4px' }}>{t.email}</span>
            <strong style={{ fontSize: '0.95rem', color: '#1e293b' }}>{user?.email || 'farmer@plantation.org'}</strong>
          </div>

          <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #f1f5f9' }}>
            <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', marginBottom: '4px' }}>Role / Status</span>
            <strong style={{ fontSize: '0.95rem', color: '#15803d', textTransform: 'capitalize' }}>{user?.role || 'Verified Plantation Grower'}</strong>
          </div>

          <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #f1f5f9' }}>
            <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', marginBottom: '4px' }}>Active Session Language</span>
            <strong style={{ fontSize: '0.95rem', color: '#1e293b' }}>{lang === 'kn' ? 'ಕನ್ನಡ (Kannada)' : 'English'}</strong>
          </div>
        </div>
      </div>

      {/* Voice Assistant Configuration Card */}
      <div style={{ background: '#ffffff', borderRadius: '16px', padding: '28px', border: '1px solid #e2e8f0', boxShadow: '0 2px 10px rgba(0,0,0,0.03)' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Volume2 size={20} color="#0284c7" />
          {t.voiceSettings}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155' }}>{t.speechRate}</label>
              <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>{speechRate}x</span>
            </div>
            <input
              type="range"
              min="0.7"
              max="1.5"
              step="0.1"
              value={speechRate}
              onChange={(e) => setSpeechRate(e.target.value)}
              style={{ width: '100%', accentColor: '#15803d' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155' }}>{t.speechPitch}</label>
              <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>{speechPitch}</span>
            </div>
            <input
              type="range"
              min="0.8"
              max="1.3"
              step="0.1"
              value={speechPitch}
              onChange={(e) => setSpeechPitch(e.target.value)}
              style={{ width: '100%', accentColor: '#15803d' }}
            />
          </div>

          <div>
            <button
              onClick={handleTestVoice}
              style={{
                background: '#f0fdf4',
                color: '#15803d',
                border: '1px solid #bbf7d0',
                borderRadius: '8px',
                padding: '8px 16px',
                fontSize: '0.825rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {t.testVoiceBtn}
            </button>
          </div>
        </div>
      </div>

      {/* Advisory Notifications Card */}
      <div style={{ background: '#ffffff', borderRadius: '16px', padding: '28px', border: '1px solid #e2e8f0', boxShadow: '0 2px 10px rgba(0,0,0,0.03)' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Bell size={20} color="#d97706" />
          {t.notifications}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.875rem', color: '#334155', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={monsoonAlerts}
              onChange={(e) => setMonsoonAlerts(e.target.checked)}
              style={{ accentColor: '#15803d', width: '16px', height: '16px' }}
            />
            {t.monsoonAlerts}
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.875rem', color: '#334155', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={pestAlerts}
              onChange={(e) => setPestAlerts(e.target.checked)}
              style={{ accentColor: '#15803d', width: '16px', height: '16px' }}
            />
            {t.pestOutbreakAlerts}
          </label>
        </div>
      </div>

      {/* Save and Logout Action Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <button
          onClick={handleSave}
          style={{
            background: '#15803d',
            color: '#ffffff',
            border: 'none',
            borderRadius: '10px',
            padding: '12px 24px',
            fontSize: '0.9rem',
            fontWeight: 700,
            cursor: 'pointer',
            boxShadow: '0 2px 8px rgba(21,128,61,0.2)'
          }}
        >
          {t.saveSettingsBtn}
        </button>

        <button
          onClick={logout}
          style={{
            background: '#fee2e2',
            color: '#b91c1c',
            border: 'none',
            borderRadius: '10px',
            padding: '12px 20px',
            fontSize: '0.9rem',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <LogOut size={18} />
          {t.logout}
        </button>
      </div>
    </div>
  );
}
