import React, { useState, useRef, useEffect } from 'react';
import {
  Upload,
  Camera,
  RefreshCw,
  Trash2,
  CheckCircle2,
  ArrowRight,
  Info,
  SwitchCamera,
  Image as ImageIcon
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function CaptureUploadPage({ onProceedToAnalysis }) {
  const { lang, t } = useAuth();
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'camera'
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  // Camera state
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraFacing, setCameraFacing] = useState('environment'); // 'user' | 'environment'
  const [capturedBlob, setCapturedBlob] = useState(null);
  const [cameraError, setCameraError] = useState('');
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const fileInputRef = useRef(null);

  // Clean up camera on unmount or tab switch
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setCapturedBlob(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setCapturedBlob(null);
    }
  };

  const handleClearImage = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setCapturedBlob(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Live Camera Handlers
  const startCamera = async (facing = cameraFacing) => {
    setCameraError('');
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facing, width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
    } catch (err) {
      console.error('Camera access error:', err);
      setCameraError(t.cameraDenied);
      setCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  const switchCameraFacing = () => {
    const nextFacing = cameraFacing === 'environment' ? 'user' : 'environment';
    setCameraFacing(nextFacing);
    if (cameraActive) {
      startCamera(nextFacing);
    }
  };

  const captureSnapshot = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `camera_${Date.now()}.jpg`, { type: 'image/jpeg' });
        setCapturedBlob(blob);
        setSelectedFile(file);
        setPreviewUrl(URL.createObjectURL(blob));
        stopCamera();
      }
    }, 'image/jpeg', 0.92);
  };

  const retakeSnapshot = () => {
    setCapturedBlob(null);
    setSelectedFile(null);
    setPreviewUrl(null);
    startCamera(cameraFacing);
  };

  const handleProceed = () => {
    if (selectedFile) {
      onProceedToAnalysis(selectedFile, previewUrl);
    }
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title Header */}
      <div>
        <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#0f172a', margin: '0 0 6px' }}>
          {t.captureTitle}
        </h2>
        <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>
          {t.captureSubtitle}
        </p>
      </div>

      {/* Main Choice Card */}
      <div style={{ background: '#ffffff', borderRadius: '16px', border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 2px 10px rgba(0,0,0,0.03)' }}>
        {/* Toggle Tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
          <button
            onClick={() => { setActiveTab('upload'); stopCamera(); }}
            style={{
              flex: 1,
              padding: '16px',
              border: 'none',
              background: activeTab === 'upload' ? '#ffffff' : 'transparent',
              borderBottom: activeTab === 'upload' ? '3px solid #15803d' : '3px solid transparent',
              color: activeTab === 'upload' ? '#15803d' : '#64748b',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            <Upload size={18} />
            {t.tabUpload}
          </button>
          <button
            onClick={() => { setActiveTab('camera'); startCamera(); }}
            style={{
              flex: 1,
              padding: '16px',
              border: 'none',
              background: activeTab === 'camera' ? '#ffffff' : 'transparent',
              borderBottom: activeTab === 'camera' ? '3px solid #15803d' : '3px solid transparent',
              color: activeTab === 'camera' ? '#15803d' : '#64748b',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            <Camera size={18} />
            {t.tabCamera}
          </button>
        </div>

        {/* Tab 1: Upload View */}
        {activeTab === 'upload' && (
          <div style={{ padding: '32px 24px' }}>
            <input
              type="file"
              ref={fileInputRef}
              accept="image/jpeg,image/png,image/jpg,image/webp"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />

            {!previewUrl ? (
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: '2px dashed #cbd5e1',
                  borderRadius: '16px',
                  padding: '48px 24px',
                  textAlign: 'center',
                  background: '#f8fafc',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                className="hover:border-green-600 hover:bg-green-50"
              >
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  background: '#dcfce7',
                  color: '#15803d',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 16px'
                }}>
                  <Upload size={32} />
                </div>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#1e293b', marginBottom: '6px' }}>
                  {t.dropzoneText}
                </h3>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '18px' }}>
                  {t.dropzoneSubtext}
                </p>
                <button
                  type="button"
                  style={{
                    background: '#15803d',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '10px 20px',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer'
                  }}
                >
                  {t.selectFileBtn}
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                <div style={{
                  maxWidth: '560px',
                  width: '100%',
                  borderRadius: '14px',
                  overflow: 'hidden',
                  border: '1px solid #e2e8f0',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
                  position: 'relative'
                }}>
                  <img
                    src={previewUrl}
                    alt="Upload Preview"
                    style={{ width: '100%', maxHeight: '420px', objectFit: 'contain', background: '#0f172a' }}
                  />
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    style={{
                      background: '#ffffff',
                      border: '1px solid #cbd5e1',
                      borderRadius: '8px',
                      padding: '8px 16px',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      color: '#334155',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <RefreshCw size={16} />
                    {t.replaceImage}
                  </button>
                  <button
                    onClick={handleClearImage}
                    style={{
                      background: '#fee2e2',
                      border: 'none',
                      borderRadius: '8px',
                      padding: '8px 16px',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      color: '#b91c1c',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <Trash2 size={16} />
                    {t.removeImage}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Live Camera View */}
        {activeTab === 'camera' && (
          <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '18px' }}>
            {cameraError && (
              <div style={{
                background: '#fee2e2',
                color: '#b91c1c',
                padding: '12px 18px',
                borderRadius: '8px',
                fontSize: '0.875rem'
              }}>
                {cameraError}
              </div>
            )}

            {!capturedBlob ? (
              <div style={{
                width: '100%',
                maxWidth: '640px',
                background: '#0f172a',
                borderRadius: '14px',
                overflow: 'hidden',
                position: 'relative',
                boxShadow: '0 4px 16px rgba(0,0,0,0.15)'
              }}>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  style={{ width: '100%', maxHeight: '420px', objectFit: 'cover', display: cameraActive ? 'block' : 'none' }}
                />
                {!cameraActive && (
                  <div style={{ padding: '60px 20px', textAlign: 'center', color: '#94a3b8' }}>
                    <Camera size={48} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
                    <p style={{ fontSize: '0.9rem', marginBottom: '16px' }}>{t.cameraNotice}</p>
                    <button
                      onClick={() => startCamera()}
                      style={{
                        background: '#15803d',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '8px',
                        padding: '10px 20px',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                    >
                      {t.startCamera}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div style={{
                maxWidth: '640px',
                width: '100%',
                borderRadius: '14px',
                overflow: 'hidden',
                border: '1px solid #e2e8f0',
                boxShadow: '0 4px 12px rgba(0,0,0,0.06)'
              }}>
                <img
                  src={previewUrl}
                  alt="Captured snapshot"
                  style={{ width: '100%', maxHeight: '420px', objectFit: 'contain', background: '#0f172a' }}
                />
              </div>
            )}

            {/* Camera Control Action Buttons */}
            {cameraActive && !capturedBlob && (
              <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
                <button
                  onClick={switchCameraFacing}
                  title={t.switchCamera}
                  style={{
                    background: '#f1f5f9',
                    border: '1px solid #cbd5e1',
                    borderRadius: '50%',
                    width: '44px',
                    height: '44px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer'
                  }}
                >
                  <SwitchCamera size={20} color="#334155" />
                </button>

                <button
                  onClick={captureSnapshot}
                  style={{
                    background: 'linear-gradient(135deg, #15803d, #16a34a)',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '24px',
                    padding: '12px 28px',
                    fontSize: '0.95rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    boxShadow: '0 4px 14px rgba(21,128,61,0.3)'
                  }}
                >
                  <Camera size={20} />
                  {t.capturePhoto}
                </button>

                <button
                  onClick={stopCamera}
                  style={{
                    background: '#ffffff',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    padding: '8px 14px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    color: '#64748b',
                    cursor: 'pointer'
                  }}
                >
                  {t.stopCamera}
                </button>
              </div>
            )}

            {capturedBlob && (
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={retakeSnapshot}
                  style={{
                    background: '#ffffff',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    padding: '10px 18px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: '#334155',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <RefreshCw size={16} />
                  {t.retakePhoto}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Action Bar: Proceed to AI Analysis */}
      {selectedFile && (
        <div style={{
          background: '#dcfce7',
          border: '1px solid #bbf7d0',
          borderRadius: '16px',
          padding: '20px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          animation: 'fadeIn 0.25s ease'
        }}>
          <div>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#14532d', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={20} color="#15803d" />
              {lang === 'kn' ? 'ಚಿತ್ರ ವಿಶ್ಲೇಷಣೆಗೆ ಸಿದ್ಧವಾಗಿದೆ' : 'Photograph ready for AI diagnostic inference'}
            </div>
            <p style={{ fontSize: '0.8rem', color: '#166534', margin: '4px 0 0' }}>
              {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </p>
          </div>

          <button
            onClick={handleProceed}
            style={{
              background: '#15803d',
              color: '#ffffff',
              border: 'none',
              borderRadius: '10px',
              padding: '12px 24px',
              fontSize: '0.95rem',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 12px rgba(21,128,61,0.25)'
            }}
          >
            {t.proceedToAnalysis}
            <ArrowRight size={18} />
          </button>
        </div>
      )}

      {/* Field Photography Instructions Card */}
      <div style={{ background: '#ffffff', borderRadius: '14px', padding: '20px', border: '1px solid #e2e8f0' }}>
        <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#14532d', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <Info size={18} color="#15803d" />
          {t.guidelinesTitle}
        </h4>
        <ul style={{ paddingLeft: '20px', fontSize: '0.85rem', color: '#475569', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <li>{t.guide1}</li>
          <li>{t.guide2}</li>
          <li>{t.guide3}</li>
        </ul>
      </div>
    </div>
  );
}
