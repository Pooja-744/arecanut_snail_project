import React, { useState, useEffect } from 'react';
import {
  FileText,
  FileDown,
  Eye,
  Calendar,
  Bug,
  Activity,
  CheckCircle2,
  X,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function ReportsHistoryPage({ onNavigate, onViewAnalysis }) {
  const { token, lang, t } = useAuth();
  const [historyItems, setHistoryItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedItem, setSelectedItem] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, [token, statusFilter]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      const url = statusFilter === 'ALL' ? '/api/history/' : `/api/history/?status_filter=${statusFilter.toLowerCase()}`;
      const res = await fetch(url, { headers });
      if (res.ok) {
        const data = await res.json();
        setHistoryItems(data.items || []);
      }
    } catch (err) {
      console.warn('Could not fetch history:', err);
    } finally {
      setLoading(false);
    }
  };

  const downloadPdf = async (item) => {
    try {
      const res = await fetch(`/api/reports/${item.id}/pdf`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Arecanut_Report_${item.id.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Could not download report: ${err.message}`);
    }
  };

  return (
    <div style={{ maxWidth: '1120px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title & Filter Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#0f172a', margin: '0 0 6px' }}>
            {t.historyTitle}
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>
            {t.historySubtitle}
          </p>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: '8px', background: '#f1f5f9', padding: '4px', borderRadius: '10px' }}>
          {[
            { id: 'ALL', label: t.filterAll },
            { id: 'SNAIL_DETECTED', label: t.filterSnail },
            { id: 'DISEASE_DETECTED', label: t.filterDisease },
            { id: 'HEALTHY', label: t.filterHealthy }
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setStatusFilter(f.id)}
              style={{
                border: 'none',
                background: statusFilter === f.id ? '#ffffff' : 'transparent',
                color: statusFilter === f.id ? '#15803d' : '#64748b',
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: statusFilter === f.id ? '0 1px 4px rgba(0,0,0,0.06)' : 'none'
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Reports List */}
      <div style={{ background: '#ffffff', borderRadius: '16px', border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 2px 10px rgba(0,0,0,0.03)' }}>
        {loading ? (
          <div style={{ padding: '60px 20px', textAlign: 'center', color: '#64748b' }}>
            Loading surveillance history...
          </div>
        ) : historyItems.length === 0 ? (
          <div style={{ padding: '60px 20px', textAlign: 'center', color: '#94a3b8' }}>
            <FileText size={48} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
            <p style={{ fontSize: '0.9rem' }}>{t.noHistoryFound}</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {historyItems.map((item, idx) => {
              const isHealthy = item.is_healthy;
              const hasSnail = item.snail_detected;
              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '18px 24px',
                    borderBottom: idx < historyItems.length - 1 ? '1px solid #f1f5f9' : 'none',
                    gap: '16px',
                    flexWrap: 'wrap'
                  }}
                  className="hover:bg-slate-50"
                >
                  {/* Left: Thumbnail & Diagnosis */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', minWidth: '280px' }}>
                    <div style={{
                      width: '64px',
                      height: '64px',
                      borderRadius: '10px',
                      overflow: 'hidden',
                      background: '#0f172a',
                      flexShrink: 0,
                      border: '1px solid #cbd5e1'
                    }}>
                      <img
                        src={item.annotated_image || item.original_image}
                        alt="annotated"
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <span style={{
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          padding: '3px 8px',
                          borderRadius: '6px',
                          background: isHealthy && !hasSnail ? '#dcfce7' : '#fee2e2',
                          color: isHealthy && !hasSnail ? '#15803d' : '#b91c1c'
                        }}>
                          {item.overall_status?.replace('_', ' ').toUpperCase()}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                          ID: {item.id.slice(0, 8)}
                        </span>
                      </div>
                      <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#1e293b', margin: 0 }}>
                        {item.disease_class?.replace('_', ' ')}
                      </h4>
                      <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '2px 0 0' }}>
                        {new Date(item.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  {/* Middle: Key metrics */}
                  <div style={{ display: 'flex', gap: '24px', fontSize: '0.825rem' }}>
                    <div>
                      <span style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'block' }}>SNAILS</span>
                      <strong style={{ color: hasSnail ? '#dc2626' : '#15803d' }}>
                        {item.snail_count} Snail(s)
                      </strong>
                    </div>
                    <div>
                      <span style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'block' }}>SEVERITY</span>
                      <strong style={{ textTransform: 'capitalize' }}>
                        {item.damage_severity?.replace('_', ' ')}
                      </strong>
                    </div>
                  </div>

                  {/* Right: Actions */}
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      onClick={() => setSelectedItem(item)}
                      style={{
                        background: '#f8fafc',
                        border: '1px solid #cbd5e1',
                        borderRadius: '8px',
                        padding: '8px 14px',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        color: '#334155',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      <Eye size={16} />
                      {t.viewDetailsBtn}
                    </button>
                    <button
                      onClick={() => downloadPdf(item)}
                      style={{
                        background: '#15803d',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '8px',
                        padding: '8px 14px',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      <FileDown size={16} />
                      {t.downloadPdfShort}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedItem && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.6)',
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: '16px',
            maxWidth: '680px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '28px',
            boxShadow: '0 12px 36px rgba(0,0,0,0.2)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
                {selectedItem.disease_class?.replace('_', ' ')}
              </h3>
              <button
                onClick={() => setSelectedItem(null)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ borderRadius: '12px', overflow: 'hidden', background: '#0f172a', marginBottom: '18px' }}>
              <img
                src={selectedItem.annotated_image || selectedItem.original_image}
                alt="Modal annotated"
                style={{ width: '100%', maxHeight: '340px', objectFit: 'contain', display: 'block' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '18px' }}>
              <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>SNAILS DETECTED</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: selectedItem.snail_detected ? '#dc2626' : '#15803d' }}>
                  {selectedItem.snail_count} Snail(s)
                </div>
              </div>
              <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>DAMAGE SEVERITY</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, textTransform: 'capitalize', color: selectedItem.is_healthy || !selectedItem.damage_severity || selectedItem.damage_severity === 'none' ? '#15803d' : '#0f172a' }}>
                  {selectedItem.is_healthy || !selectedItem.damage_severity || selectedItem.damage_severity === 'none'
                    ? 'No Visible Damage'
                    : selectedItem.damage_severity?.replace('_', ' ')}
                </div>
              </div>
            </div>

            <div style={{ background: '#ecfdf5', padding: '16px', borderRadius: '10px', border: '1px solid #a7f3d0', fontSize: '0.85rem', lineHeight: '1.6', color: '#064e3b', marginBottom: '20px', whiteSpace: 'pre-line' }}>
              {selectedItem.recommendation}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                onClick={() => downloadPdf(selectedItem)}
                style={{
                  background: '#15803d',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '10px 18px',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <FileDown size={16} />
                Download PDF
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
