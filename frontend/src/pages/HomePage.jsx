import React, { useState, useEffect } from 'react';
import {
  Sprout,
  ShieldAlert,
  Bug,
  Activity,
  FileText,
  ArrowRight,
  TrendingUp,
  Cpu,
  Clock,
  CheckCircle2,
  Bot
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function HomePage({ onNavigate }) {
  const { user, token, lang, t } = useAuth();
  const [stats, setStats] = useState({
    total_analyses: 0,
    healthy_count: 0,
    disease_count: 0,
    snail_count: 0,
    both_count: 0,
    recent_analyses: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        const res = await fetch('/api/dashboard/stats', { headers });
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (err) {
        console.warn('Could not load stats:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [token]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Welcome Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #14532d 0%, #15803d 100%)',
        borderRadius: '20px',
        padding: '32px 36px',
        color: '#ffffff',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 8px 24px rgba(20,83,45,0.2)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{ position: 'relative', zIndex: 2, maxWidth: '640px' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.15)', padding: '4px 12px', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 700, marginBottom: '12px' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e' }}></span>
            {lang === 'kn' ? 'ನೈಜ AI ಕಣ್ಗಾವಲು ಸಕ್ರಿಯವಾಗಿದೆ' : 'Active Field Surveillance'}
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0 0 8px' }}>
            {t.welcomeUser}, {user?.name || 'Grower'}!
          </h2>
          <p style={{ fontSize: '0.9rem', opacity: 0.9, lineHeight: '1.6', margin: '0 0 20px' }}>
            {t.overviewSubtitle}
          </p>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              onClick={() => onNavigate('capture')}
              style={{
                background: '#ffffff',
                color: '#14532d',
                border: 'none',
                borderRadius: '10px',
                padding: '12px 20px',
                fontWeight: 700,
                fontSize: '0.875rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}
            >
              <ShieldAlert size={18} color="#15803d" />
              {t.startNewScan}
            </button>
            <button
              onClick={() => onNavigate('history')}
              style={{
                background: 'rgba(255,255,255,0.2)',
                color: '#ffffff',
                border: '1px solid rgba(255,255,255,0.35)',
                borderRadius: '10px',
                padding: '12px 20px',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <FileText size={18} />
              {t.viewReports}
            </button>
          </div>
        </div>
        <div style={{ display: 'none', position: 'relative', zIndex: 1, opacity: 0.2 }} className="md:block">
          <Sprout size={160} strokeWidth={1.5} />
        </div>
      </div>

      {/* 4 Core Aggregate Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
        <div style={{ background: '#ffffff', borderRadius: '16px', padding: '22px', border: '1px solid #e2e8f0', boxShadow: '0 2px 10px rgba(0,0,0,0.03)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#64748b' }}>{t.statTotalAnalyses}</span>
            <div style={{ background: '#f1f5f9', padding: '8px', borderRadius: '8px' }}>
              <TrendingUp size={18} color="#0f172a" />
            </div>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a' }}>
            {loading ? '...' : stats.total_analyses}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#15803d', marginTop: '4px', fontWeight: 600 }}>
            {lang === 'kn' ? 'ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ನೋಂದಾಯಿತ' : 'Persisted in database'}
          </div>
        </div>

        <div style={{ background: '#ffffff', borderRadius: '16px', padding: '22px', border: '1px solid #e2e8f0', boxShadow: '0 2px 10px rgba(0,0,0,0.03)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#64748b' }}>{t.statSnailsFound}</span>
            <div style={{ background: '#fef3c7', padding: '8px', borderRadius: '8px' }}>
              <Bug size={18} color="#d97706" />
            </div>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#d97706' }}>
            {loading ? '...' : (stats.snail_count + stats.both_count)}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
            {lang === 'kn' ? 'YOLOv8n ಮೂಲಕ ದೃಢಪಟ್ಟಿದೆ' : 'Validated by YOLOv8n'}
          </div>
        </div>

        <div style={{ background: '#ffffff', borderRadius: '16px', padding: '22px', border: '1px solid #e2e8f0', boxShadow: '0 2px 10px rgba(0,0,0,0.03)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#64748b' }}>{t.statDiseasesFound}</span>
            <div style={{ background: '#fee2e2', padding: '8px', borderRadius: '8px' }}>
              <Activity size={18} color="#dc2626" />
            </div>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#dc2626' }}>
            {loading ? '...' : (stats.disease_count + stats.both_count)}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
            {lang === 'kn' ? 'ಕೊಳೆರೋಗ, ಸುಳಿಕೊಳೆ ಇತ್ಯಾದಿ' : 'Koleroga, Bud Rot, YLD, etc.'}
          </div>
        </div>

        <div style={{ background: '#ffffff', borderRadius: '16px', padding: '22px', border: '1px solid #e2e8f0', boxShadow: '0 2px 10px rgba(0,0,0,0.03)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#64748b' }}>{t.statHealthyPalms}</span>
            <div style={{ background: '#dcfce7', padding: '8px', borderRadius: '8px' }}>
              <CheckCircle2 size={18} color="#15803d" />
            </div>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#15803d' }}>
            {loading ? '...' : stats.healthy_count}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#15803d', marginTop: '4px' }}>
            {lang === 'kn' ? 'ಯಾವುದೇ ರೋಗ ಅಥವಾ ಕೀಟವಿಲ್ಲ' : 'Clear of infection'}
          </div>
        </div>
      </div>

      {/* Two Column Section: Quick Features & Recent Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        {/* Quick Actions List */}
        <div style={{ background: '#ffffff', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', marginBottom: '16px' }}>
            {t.quickActions}
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              {
                title: t.startNewScan,
                desc: lang === 'kn' ? 'ಚಿತ್ರ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಅಥವಾ ಕ್ಯಾಮೆರಾ ಬಳಸಿ' : 'Capture or upload plant photo for immediate detection',
                icon: ShieldAlert,
                page: 'capture',
                color: '#15803d'
              },
              {
                title: t.viewReports,
                desc: lang === 'kn' ? 'ಹಿಂದಿನ ಎಲ್ಲಾ ತಪಾಸಣಾ ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ' : 'Access your history and download PDF prescriptions',
                icon: FileText,
                page: 'history',
                color: '#d97706'
              },
              {
                title: t.exploreModels,
                desc: lang === 'kn' ? 'AI ಮಾದರಿಗಳು ಮತ್ತು ಡೆವಲಪರ್ Quick Test' : 'Inspect active weights, metrics, and test sample photos',
                icon: Cpu,
                page: 'admin',
                color: '#7c3aed'
              }
            ].map((act, idx) => {
              const Icon = act.icon;
              return (
                <div
                  key={idx}
                  onClick={() => onNavigate(act.page)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '14px 16px',
                    borderRadius: '12px',
                    border: '1px solid #e2e8f0',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    background: '#f8fafc'
                  }}
                  className="hover:border-green-600 hover:bg-green-50"
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{
                      background: '#ffffff',
                      padding: '10px',
                      borderRadius: '10px',
                      boxShadow: '0 2px 6px rgba(0,0,0,0.04)'
                    }}>
                      <Icon size={20} color={act.color} />
                    </div>
                    <div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1e293b' }}>{act.title}</div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{act.desc}</div>
                    </div>
                  </div>
                  <ArrowRight size={16} color="#94a3b8" />
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Detection Activity */}
        <div style={{ background: '#ffffff', borderRadius: '16px', padding: '24px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              {t.recentActivity}
            </h3>
            <button
              onClick={() => onNavigate('history')}
              style={{ background: 'none', border: 'none', color: '#15803d', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer' }}
            >
              {lang === 'kn' ? 'ಎಲ್ಲವನ್ನೂ ನೋಡಿ' : 'View All'} →
            </button>
          </div>

          {stats.recent_analyses.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 16px', color: '#94a3b8' }}>
              <Clock size={36} color="#cbd5e1" style={{ margin: '0 auto 8px' }} />
              <p style={{ fontSize: '0.85rem' }}>{t.noRecentScans}</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {stats.recent_analyses.map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    borderRadius: '10px',
                    border: '1px solid #f1f5f9',
                    background: '#f8fafc'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {item.annotated_image ? (
                      <img
                        src={item.annotated_image}
                        alt="thumb"
                        style={{ width: '48px', height: '48px', objectFit: 'cover', borderRadius: '8px' }}
                      />
                    ) : (
                      <div style={{ width: '48px', height: '48px', borderRadius: '8px', background: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Sprout size={20} color="#64748b" />
                      </div>
                    )}
                    <div>
                      <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#1e293b' }}>
                        {item.disease_class?.replace('_', ' ')}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        {item.snail_count > 0 ? `${item.snail_count} Snails Detected` : 'No Snails'} • {new Date(item.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>

                  <span style={{
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '4px 8px',
                    borderRadius: '6px',
                    background: item.is_healthy ? '#dcfce7' : '#fee2e2',
                    color: item.is_healthy ? '#15803d' : '#b91c1c'
                  }}>
                    {item.overall_status?.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
