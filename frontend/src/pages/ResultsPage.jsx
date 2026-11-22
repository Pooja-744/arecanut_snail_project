import React, { useState } from 'react';
import {
  ShieldAlert,
  Bug,
  Activity,
  AlertTriangle,
  FileDown,
  RefreshCw,
  CheckCircle2,
  Sliders,
  Sparkles,
  Home,
  Droplet,
  ShieldCheck,
  HeartHandshake
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function ResultsPage({ analysisData, originalPreview, onNavigate }) {
  const { lang, t } = useAuth();
  const [viewMode, setViewMode] = useState('sideBySide'); // 'annotated' | 'original' | 'sideBySide'
  const [downloading, setDownloading] = useState(false);

  if (!analysisData) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px' }}>
        <h3>No analysis results loaded.</h3>
        <button
          onClick={() => onNavigate('capture')}
          style={{
            marginTop: '12px',
            background: '#15803d',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            padding: '10px 18px',
            cursor: 'pointer'
          }}
        >
          {t.scanAnotherImage}
        </button>
      </div>
    );
  }

  const {
    analysis_id,
    overall_status,
    overall_status_text,
    snail_detection,
    disease_classification,
    damage_assessment,
    combined_recommendation,
    smart_recommendations,
    annotated_image,
    original_image,
  } = analysisData;

  const originalImgSrc = original_image || originalPreview;
  const annotatedImgSrc = annotated_image || originalPreview;

  const isHealthy = disease_classification?.is_healthy || ['HEALTHY', 'HEALTHY LEAF', 'HEALTHY NUT', 'NO_DISEASE'].includes(disease_classification?.predicted_class);
  const isUncertain = disease_classification?.predicted_class === 'UNCERTAIN';
  const hasGenuineDisease = !isHealthy && !isUncertain && Boolean(disease_classification?.predicted_class) && !['HEALTHY', 'HEALTHY LEAF', 'HEALTHY NUT', 'NO_DISEASE', 'UNCERTAIN'].includes(disease_classification?.predicted_class);
  const snailFound = Boolean(snail_detection?.detected) && (snail_detection?.count > 0);
  const hasDamage = Boolean(damage_assessment?.has_damage) && Boolean(damage_assessment?.severity) && ['low_damage', 'moderate_damage', 'severe_damage'].includes(damage_assessment?.severity);
  const damageSeverity = hasDamage ? damage_assessment?.severity : null;

  const handleDownloadPdf = async () => {
    setDownloading(true);
    try {
      const payload = {
        analysis_id: analysis_id || `rep_${Date.now()}`,
        overall_status: overall_status || 'healthy',
        snail_count: snail_detection?.count || 0,
        snail_confidence: snail_detection?.confidence || 0,
        disease_class: disease_classification?.predicted_class || 'HEALTHY',
        disease_confidence: disease_classification?.confidence || 0,
        is_healthy: Boolean(isHealthy),
        damage_severity: hasDamage && damageSeverity ? damageSeverity : 'none',
        recommendation: combined_recommendation || 'Continue routine surveillance.',
        farmer_name: 'Arecanut Plantation Farmer',
        plantation_location: 'Field Site',
      };

      const res = await fetch('/api/reports/generate-direct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('PDF generation failed');

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Arecanut_Diagnostic_Report_${payload.analysis_id.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Could not download PDF report: ${err.message}`);
    } finally {
      setDownloading(false);
    }
  };

  // Determine overall status colors strictly matching backend states
  let statusBadgeBg = '#dcfce7';
  let statusBadgeText = '#15803d';
  if (overall_status === 'both_detected') {
    statusBadgeBg = '#fecdd3';
    statusBadgeText = '#9f1239';
  } else if (overall_status === 'disease_detected') {
    statusBadgeBg = '#fee2e2';
    statusBadgeText = '#b91c1c';
  } else if (overall_status === 'snail_damage_detected') {
    statusBadgeBg = '#ffedd5';
    statusBadgeText = '#c2410c';
  } else if (overall_status === 'snail_detected' || snailFound) {
    statusBadgeBg = '#fef3c7';
    statusBadgeText = '#b45309';
  } else if (overall_status === 'further_inspection' || isUncertain) {
    statusBadgeBg = '#f1f5f9';
    statusBadgeText = '#475569';
  }

  return (
    <div style={{ maxWidth: '1180px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner with Overall Status & Actions (Weather Completely Removed) */}
      <div style={{
        background: '#ffffff',
        borderRadius: '16px',
        padding: '24px 28px',
        border: '1px solid #e2e8f0',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '16px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.03)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span style={{
              fontSize: '0.8rem',
              fontWeight: 800,
              padding: '6px 14px',
              borderRadius: '20px',
              background: statusBadgeBg,
              color: statusBadgeText,
              letterSpacing: '0.3px'
            }}>
              {overall_status_text || overall_status?.replace('_', ' ').toUpperCase()}
            </span>
            <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Report ID: {analysis_id?.slice(0, 8)}...
            </span>
          </div>
          <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
            {overall_status_text || overall_status?.replace('_', ' ').toUpperCase()}
          </h2>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={handleDownloadPdf}
            disabled={downloading}
            style={{
              background: 'linear-gradient(135deg, #15803d, #16a34a)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '10px',
              padding: '10px 18px',
              fontSize: '0.85rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 2px 8px rgba(21,128,61,0.25)'
            }}
          >
            <FileDown size={18} />
            {downloading ? 'Preparing PDF...' : t.downloadPdfBtn}
          </button>

          <button
            onClick={() => onNavigate('capture')}
            style={{
              background: '#f8fafc',
              color: '#334155',
              border: '1px solid #cbd5e1',
              borderRadius: '10px',
              padding: '10px 16px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <RefreshCw size={16} />
            {t.scanAnotherImage}
          </button>
        </div>
      </div>

      {/* Visual Image Inspection Section (Actual Model Bounding Boxes) */}
      <div style={{
        background: '#ffffff',
        borderRadius: '16px',
        padding: '24px',
        border: '1px solid #e2e8f0',
        boxShadow: '0 2px 10px rgba(0,0,0,0.03)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: '0 0 4px', color: '#0f172a' }}>
              {lang === 'kn' ? 'ದೃಶ್ಯ ತಪಾಸಣೆ (YOLOv8n ಬೌಂಡಿಂಗ್ ಬಾಕ್ಸ್‌ಗಳು)' : 'Visual Inspection (Actual Model Bounding Boxes)'}
            </h3>
            <p style={{ fontSize: '0.8rem', color: '#64748b', margin: 0 }}>
              {snail_detection?.count > 0 
                ? `${snail_detection.count} Giant African Snail(s) localized with bounding boxes & confidence scores.`
                : 'No Giant African Snail detected in this field frame.'}
            </p>
          </div>

          {/* View Mode Switcher */}
          <div style={{ display: 'flex', gap: '6px', background: '#f1f5f9', padding: '4px', borderRadius: '10px' }}>
            <button
              onClick={() => setViewMode('sideBySide')}
              style={{
                border: 'none',
                background: viewMode === 'sideBySide' ? '#ffffff' : 'transparent',
                color: viewMode === 'sideBySide' ? '#15803d' : '#64748b',
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: viewMode === 'sideBySide' ? '0 1px 4px rgba(0,0,0,0.08)' : 'none'
              }}
            >
              {t.toggleSideBySide}
            </button>
            <button
              onClick={() => setViewMode('annotated')}
              style={{
                border: 'none',
                background: viewMode === 'annotated' ? '#ffffff' : 'transparent',
                color: viewMode === 'annotated' ? '#15803d' : '#64748b',
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: viewMode === 'annotated' ? '0 1px 4px rgba(0,0,0,0.08)' : 'none'
              }}
            >
              {t.viewAnnotated}
            </button>
            <button
              onClick={() => setViewMode('original')}
              style={{
                border: 'none',
                background: viewMode === 'original' ? '#ffffff' : 'transparent',
                color: viewMode === 'original' ? '#15803d' : '#64748b',
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: viewMode === 'original' ? '0 1px 4px rgba(0,0,0,0.08)' : 'none'
              }}
            >
              {t.viewOriginal}
            </button>
          </div>
        </div>

        {/* Image Containers */}
        {viewMode === 'sideBySide' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            <div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', display: 'block', marginBottom: '6px' }}>
                {t.viewOriginal}
              </span>
              <div style={{ borderRadius: '12px', overflow: 'hidden', background: '#0f172a', border: '1px solid #cbd5e1' }}>
                <img src={originalImgSrc} alt="Original" style={{ width: '100%', maxHeight: '380px', objectFit: 'contain', display: 'block' }} />
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#15803d', display: 'block', marginBottom: '6px' }}>
                {t.viewAnnotated} (YOLOv8n Detections)
              </span>
              <div style={{ borderRadius: '12px', overflow: 'hidden', background: '#0f172a', border: '2px solid #22c55e' }}>
                <img src={annotatedImgSrc} alt="Model Annotated" style={{ width: '100%', maxHeight: '380px', objectFit: 'contain', display: 'block' }} />
              </div>
            </div>
          </div>
        )}

        {viewMode === 'annotated' && (
          <div style={{ borderRadius: '12px', overflow: 'hidden', background: '#0f172a', border: '2px solid #22c55e', maxWidth: '720px', margin: '0 auto' }}>
            <img src={annotatedImgSrc} alt="Annotated" style={{ width: '100%', maxHeight: '480px', objectFit: 'contain', display: 'block' }} />
          </div>
        )}

        {viewMode === 'original' && (
          <div style={{ borderRadius: '12px', overflow: 'hidden', background: '#0f172a', border: '1px solid #cbd5e1', maxWidth: '720px', margin: '0 auto' }}>
            <img src={originalImgSrc} alt="Original" style={{ width: '100%', maxHeight: '480px', objectFit: 'contain', display: 'block' }} />
          </div>
        )}
      </div>

      {/* DYNAMIC DIAGNOSTIC RESULT CARDS (Condition-Based Conditional Rendering) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
        {/* CARD 1: Giant African Snail Detection (Always displayed) */}
        <div style={{ background: '#ffffff', borderRadius: '16px', padding: '22px', border: '1px solid #e2e8f0', boxShadow: '0 2px 10px rgba(0,0,0,0.03)', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.775rem', fontWeight: 800, color: '#64748b' }}>{t.cardSnailTitle}</span>
            <div style={{ background: snailFound ? '#fee2e2' : '#f0fdf4', padding: '8px', borderRadius: '8px' }}>
              <Bug size={20} color={snailFound ? '#dc2626' : '#15803d'} />
            </div>
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: snailFound ? '#dc2626' : '#15803d', marginBottom: '4px' }}>
            {snailFound ? `${snail_detection?.count} ${t.snailDetected}` : t.noSnailDetected}
          </div>
          <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '0 0 12px 0' }}>
            {snail_detection?.explanation || (snailFound ? 'Live specimens localized on plant.' : 'Palm is free of snail infestation.')}
          </p>
          <div style={{ marginTop: 'auto', fontSize: '0.775rem', color: '#475569', display: 'flex', flexDirection: 'column', gap: '3px', borderTop: '1px solid #f1f5f9', paddingTop: '10px' }}>
            <div><strong>{t.confidence}:</strong> {((snail_detection?.confidence || 0) * 100).toFixed(1)}%</div>
            <div><strong>Latency:</strong> {snail_detection?.inference_ms || 0} ms (CPU)</div>
            <div><strong>Model:</strong> Ultralytics YOLOv8n (conf &ge; 0.45)</div>
          </div>
        </div>

        {/* CARD 2: Arecanut Disease Classification (Displayed ONLY when a genuine disease is diagnosed) */}
        {hasGenuineDisease && (
          <div style={{ background: '#ffffff', borderRadius: '16px', padding: '22px', border: '1px solid #e2e8f0', boxShadow: '0 2px 10px rgba(0,0,0,0.03)', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.775rem', fontWeight: 800, color: '#64748b' }}>{t.cardDiseaseTitle}</span>
              <div style={{ background: '#fee2e2', padding: '8px', borderRadius: '8px' }}>
                <Activity size={20} color="#dc2626" />
              </div>
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#dc2626', marginBottom: '4px' }}>
              {disease_classification?.predicted_class?.replace('_', ' ')}
            </div>
            <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '0 0 12px 0' }}>
              {disease_classification?.explanation || 'Pathogen detected on foliage/bunches.'}
            </p>
            <div style={{ marginTop: 'auto', fontSize: '0.775rem', color: '#475569', display: 'flex', flexDirection: 'column', gap: '3px', borderTop: '1px solid #f1f5f9', paddingTop: '10px' }}>
              <div><strong>{t.confidence}:</strong> {((disease_classification?.confidence || 0) * 100).toFixed(1)}%</div>
              <div><strong>Status:</strong> Infected - Treatment Required</div>
              <div><strong>Model:</strong> MobileNetV2 (Decoupled from Snail)</div>
            </div>
          </div>
        )}

        {/* CARD 3: Snail Feeding Damage Severity (Displayed ONLY when has_damage is true with positive severity) */}
        {hasDamage && (
          <div style={{ background: '#ffffff', borderRadius: '16px', padding: '22px', border: '1px solid #e2e8f0', boxShadow: '0 2px 10px rgba(0,0,0,0.03)', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.775rem', fontWeight: 800, color: '#64748b' }}>{t.cardDamageTitle}</span>
              <div style={{ background: '#fee2e2', padding: '8px', borderRadius: '8px' }}>
                <AlertTriangle size={20} color="#dc2626" />
              </div>
            </div>
            <div style={{
              fontSize: '1.35rem',
              fontWeight: 800,
              textTransform: 'capitalize',
              color: damageSeverity === 'severe_damage' ? '#dc2626' : '#d97706',
              marginBottom: '4px'
            }}>
              {damageSeverity.replace('_', ' ')}
            </div>
            <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '0 0 12px 0' }}>
              {damage_assessment?.explanation || `Physical feeding damage evaluated as ${damageSeverity.replace('_', ' ')}.`}
            </p>
            <div style={{ marginTop: 'auto', fontSize: '0.775rem', color: '#475569', display: 'flex', flexDirection: 'column', gap: '3px', borderTop: '1px solid #f1f5f9', paddingTop: '10px' }}>
              <div><strong>Damage Status:</strong> Feeding Lesions Present</div>
              <div><strong>Rating:</strong> {damageSeverity.replace('_', ' ')}</div>
              <div><strong>Model:</strong> MobileNetV2 Damage Classifier</div>
            </div>
          </div>
        )}

        {/* CARD 4: Overall Plant Health Status (Always displayed) */}
        <div style={{ background: '#ffffff', borderRadius: '16px', padding: '22px', border: '1px solid #e2e8f0', boxShadow: '0 2px 10px rgba(0,0,0,0.03)', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.775rem', fontWeight: 800, color: '#64748b' }}>{t.cardOverallTitle}</span>
            <div style={{ background: statusBadgeBg, padding: '8px', borderRadius: '8px' }}>
              <ShieldCheck size={20} color={statusBadgeText} />
            </div>
          </div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: statusBadgeText, marginBottom: '4px' }}>
            {overall_status_text || overall_status?.replace('_', ' ').toUpperCase()}
          </div>
          <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '0 0 12px 0' }}>
            {isHealthy && !snailFound && !hasDamage
              ? (lang === 'kn' ? 'ಸಸ್ಯವು ಸಂಪೂರ್ಣವಾಗಿ ಆರೋಗ್ಯಕರವಾಗಿದೆ ಮತ್ತು ಕೀಟಮುಕ್ತವಾಗಿದೆ.' : 'Plant is in healthy condition with no pests or pathogens detected.')
              : (lang === 'kn' ? 'ತಕ್ಷಣದ ನಿರ್ವಹಣಾ ಕ್ರಮಗಳನ್ನು ಕೈಗೊಳ್ಳಿ.' : 'Review recommended treatments and remedies below.')}
          </p>
          <div style={{ marginTop: 'auto', fontSize: '0.775rem', color: '#475569', display: 'flex', flexDirection: 'column', gap: '3px', borderTop: '1px solid #f1f5f9', paddingTop: '10px' }}>
            <div><strong>Diagnostic Summary:</strong> {overall_status?.replace('_', ' ').toUpperCase()}</div>
            <div><strong>Intervention:</strong> {isHealthy && !snailFound && !hasDamage ? 'Routine Surveillance' : 'Active Management Required'}</div>
            <div><strong>Advisory:</strong> Verified agronomic protocol</div>
          </div>
        </div>
      </div>

      {/* REDESIGNED SMART RECOMMENDATIONS & HOME REMEDIES SECTION */}
      <div style={{
        background: '#ffffff',
        borderRadius: '16px',
        padding: '28px',
        border: '1px solid #e2e8f0',
        boxShadow: '0 2px 10px rgba(0,0,0,0.03)',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sparkles size={24} color="#15803d" />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#14532d', margin: 0 }}>
            {t.recommendationsTitle || 'Smart Agronomic Recommendations & Remedies'}
          </h3>
        </div>

        {/* 1. Immediate Action Steps */}
        {smart_recommendations?.action_steps?.length > 0 && (
          <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '18px', border: '1px solid #e2e8f0' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0f172a', margin: '0 0 10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={18} color="#15803d" /> {t.actionStepsTitle || 'Immediate Action Steps'}
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {smart_recommendations.action_steps.map((step, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.875rem', color: '#334155' }}>
                  <span style={{ fontWeight: 700, color: '#15803d' }}>{idx + 1}.</span>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 2. Structured Home Remedies & Organic Solutions */}
        {smart_recommendations?.home_remedies?.length > 0 && (
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#065f46', margin: '0 0 12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <HeartHandshake size={18} color="#059669" /> {t.homeRemediesTitle || 'Home Remedies & Non-Chemical Measures'}
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
              {smart_recommendations.home_remedies.map((remedy, idx) => (
                <div
                  key={idx}
                  style={{
                    background: '#f0fdf4',
                    border: '1px solid #bbf7d0',
                    borderRadius: '12px',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#14532d' }}>
                    🌿 {remedy.title}
                  </div>
                  <div style={{ fontSize: '0.825rem', color: '#1e293b', lineHeight: 1.5 }}>
                    {remedy.description}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 3. Prescribed Treatments & Scientific Dosages */}
        {smart_recommendations?.chemical_treatments?.length > 0 && (
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#991b1b', margin: '0 0 12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Droplet size={18} color="#dc2626" /> {t.chemicalTitle || 'Prescribed Treatments & Dosages'}
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
              {smart_recommendations.chemical_treatments.map((chem, idx) => (
                <div
                  key={idx}
                  style={{
                    background: '#fff1f2',
                    border: '1px solid #fecdd3',
                    borderRadius: '12px',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#9f1239' }}>
                    🧪 {chem.name}
                  </div>
                  <div style={{ fontSize: '0.825rem', color: '#1e293b', lineHeight: 1.5 }}>
                    <strong>Dosage:</strong> {chem.dosage}
                  </div>
                  <div style={{ fontSize: '0.775rem', color: '#64748b', fontStyle: 'italic' }}>
                    ⚠️ {chem.safety}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 4. Complete Actionable Text Prescription */}
        <div style={{
          background: '#f8fafc',
          borderRadius: '12px',
          padding: '20px',
          border: '1px solid #cbd5e1',
          fontSize: '0.875rem',
          lineHeight: '1.7',
          color: '#1e293b',
          whiteSpace: 'pre-line'
        }}>
          <strong>{t.prescriptionHeading}:</strong>
          {'\n\n'}
          {combined_recommendation}
        </div>
      </div>
    </div>
  );
}
