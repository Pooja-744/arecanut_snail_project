import React, { useState } from 'react';
import {
  Sprout,
  Home,
  Camera,
  CheckCircle2,
  FileText,
  User,
  Cpu,
  LogOut,
  Menu,
  X,
  ChevronRight,
  ShieldCheck
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Chatbot from '../components/Chatbot';
import VoiceAssistant from '../components/VoiceAssistant';

export default function Layout({ currentPage, onNavigate, onGoBack, currentAnalysis, children }) {
  const { user, lang, t, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [voiceQueryForChat, setVoiceQueryForChat] = useState('');

  const navItems = [
    { id: 'overview', label: t.navOverview, icon: Home },
    { id: 'capture', label: t.navCapture, icon: Camera },
    ...(currentAnalysis ? [{ id: 'results', label: t.navResults, icon: ShieldCheck }] : []),
    { id: 'history', label: t.navHistory, icon: FileText },
    { id: 'admin', label: t.navAdmin, icon: Cpu },
    { id: 'profile', label: t.navProfile, icon: User },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#f8fafc' }}>
      {/* Top Navbar */}
      <header style={{
        background: 'linear-gradient(135deg, #14532d 0%, #15803d 100%)',
        color: '#ffffff',
        padding: '14px 28px',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        boxShadow: '0 4px 16px rgba(0,0,0,0.1)'
      }}>
        <div style={{ maxWidth: '1360px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {/* Brand & Mobile Hamburger */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden"
              style={{ background: 'none', border: 'none', color: '#ffffff', cursor: 'pointer', padding: '4px' }}
            >
              {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>

            <div
              onClick={() => onNavigate('overview')}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
            >
              <div style={{
                background: '#22c55e',
                color: '#14532d',
                padding: '7px',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Sprout size={22} />
              </div>
              <div>
                <h1 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0, letterSpacing: '-0.3px' }}>
                  {t.appName}
                </h1>
                <p style={{ fontSize: '0.7rem', opacity: 0.85, margin: 0 }}>
                  {t.appSubtitle}
                </p>
              </div>
            </div>
          </div>

          {/* Right Section: Status badge, user greeting, profile, logout */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span style={{
              background: 'rgba(34,197,94,0.2)',
              border: '1px solid #22c55e',
              color: '#dcfce7',
              padding: '5px 12px',
              borderRadius: '20px',
              fontSize: '0.75rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#22c55e' }}></span>
              3 Models Active
            </span>

            <div
              onClick={() => onNavigate('profile')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'rgba(255,255,255,0.12)',
                padding: '6px 12px',
                borderRadius: '20px',
                cursor: 'pointer'
              }}
            >
              <User size={15} />
              <span style={{ fontSize: '0.8rem', fontWeight: 700 }}>{user?.name?.split(' ')[0] || 'Farmer'}</span>
            </div>

            <button
              onClick={logout}
              title={t.logout}
              style={{
                background: 'rgba(239,68,68,0.2)',
                border: '1px solid rgba(239,68,68,0.4)',
                color: '#fecaca',
                padding: '6px',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Body with Sidebar + Content */}
      <div style={{ flex: 1, display: 'flex', maxWidth: '1360px', width: '100%', margin: '0 auto' }}>
        {/* Sidebar Navigation */}
        <aside style={{
          width: '240px',
          background: '#ffffff',
          borderRight: '1px solid #e2e8f0',
          padding: '24px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          flexShrink: 0
        }}
        className={`lg:block ${sidebarOpen ? 'block fixed inset-y-0 left-0 z-40 shadow-2xl' : 'hidden'}`}
        >
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onNavigate(item.id);
                  setSidebarOpen(false);
                }}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '11px 14px',
                  borderRadius: '10px',
                  border: 'none',
                  background: active ? '#f0fdf4' : 'transparent',
                  color: active ? '#15803d' : '#475569',
                  fontWeight: active ? 700 : 500,
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  textAlign: 'left'
                }}
                className="hover:bg-slate-50"
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Icon size={18} color={active ? '#15803d' : '#64748b'} />
                  {item.label}
                </div>
                {active && <ChevronRight size={14} color="#15803d" />}
              </button>
            );
          })}

          {/* Sidebar Footer Model Note */}
          <div style={{ marginTop: 'auto', background: '#f8fafc', padding: '12px', borderRadius: '10px', fontSize: '0.725rem', color: '#64748b' }}>
            <div style={{ fontWeight: 700, color: '#14532d', marginBottom: '2px' }}>YOLOv8 & MobileNetV2</div>
            <div>Multi-Task Vision Architecture</div>
          </div>
        </aside>

        {/* Dynamic Page Content */}
        <main style={{ flex: 1, padding: '28px 24px', minWidth: 0 }}>
          {children}
        </main>
      </div>

      {/* Global Persistent Voice Assistant */}
      <VoiceAssistant
        onNavigate={onNavigate}
        onGoBack={onGoBack}
        onAskChatbot={(text) => setVoiceQueryForChat(text)}
        currentAnalysis={currentAnalysis}
      />

      {/* Global Persistent AI Chatbot */}
      <Chatbot
        externalTriggerText={voiceQueryForChat}
        onClearExternalTrigger={() => setVoiceQueryForChat('')}
        currentAnalysis={currentAnalysis}
      />
    </div>
  );
}
