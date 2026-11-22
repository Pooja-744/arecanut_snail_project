import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Radio, Sparkles, Square, HelpCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function VoiceAssistant({ onNavigate, onGoBack, onAskChatbot, currentAnalysis }) {
  const { lang, t } = useAuth();
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [transcript, setTranscript] = useState('');
  const [assistantReply, setAssistantReply] = useState('');
  const [speechEnabled, setSpeechEnabled] = useState(true);
  const [showHelp, setShowHelp] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = lang === 'kn' ? 'kn-IN' : 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
      setTranscript('');
      setAssistantReply('');
    };

    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      setTranscript(text);
      handleVoiceInput(text);
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.stop();
      } catch {}
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [lang]);

  // Text-To-Speech Synthesis
  const speak = (text) => {
    if (!speechEnabled || !window.speechSynthesis) return;

    window.speechSynthesis.cancel();
    // Clean markdown characters before speaking
    const cleanSpeech = text
      .replace(/[*#_`>~-]/g, '')
      .replace(/\n+/g, '. ')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanSpeech);
    utterance.lang = lang === 'kn' ? 'kn-IN' : 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  };

  // Voice Command & Question Dispatcher
  const handleVoiceInput = async (rawText) => {
    const cmd = rawText.toLowerCase().trim();

    // 0. Stop speech command
    if (cmd === 'stop' || cmd.includes('stop speaking') || cmd.includes('silence') || cmd.includes('ಮಾತು ನಿಲ್ಲಿಸು') || cmd.includes('ಸಾಕು')) {
      stopSpeaking();
      return;
    }

    // 1. Navigation Commands
    // A. Overview / Dashboard / Home
    if (
      cmd.includes('dashboard') ||
      cmd.includes('overview') ||
      cmd.includes('home') ||
      cmd.includes('ಮುಖ್ಯ ಪುಟ') ||
      cmd.includes('ಡ್ಯಾಶ್‌ಬೋರ್ಡ್')
    ) {
      const msg = lang === 'kn' ? 'ಮುಖ್ಯ ಪುಟಕ್ಕೆ ತೆರಳುತ್ತಿದ್ದೇವೆ.' : 'Opening overview dashboard.';
      setAssistantReply(msg);
      speak(msg);
      onNavigate?.('overview');
      return;
    }

    // B. Image Capture / Upload / Scan
    if (
      cmd.includes('image upload') ||
      cmd.includes('upload') ||
      cmd.includes('capture') ||
      cmd.includes('scan') ||
      cmd.includes('photograph') ||
      cmd.includes('photo') ||
      cmd.includes('ಕ್ಯಾಮೆರಾ') ||
      cmd.includes('ಚಿತ್ರ') ||
      cmd.includes('ಸ್ಕ್ಯಾನ್')
    ) {
      const msg = lang === 'kn' ? 'ಚಿತ್ರ ಸೆರೆಹಿಡಿಯುವ ಮತ್ತು ಅಪ್‌ಲೋಡ್ ಪುಟಕ್ಕೆ ತೆರಳುತ್ತಿದ್ದೇವೆ.' : 'Opening plant image capture and upload.';
      setAssistantReply(msg);
      speak(msg);
      onNavigate?.('capture');
      return;
    }

    // C. Results
    if (
      cmd.includes('result') ||
      cmd.includes('analysis result') ||
      cmd.includes('show results') ||
      cmd.includes('ಫಲಿತಾಂಶ')
    ) {
      if (currentAnalysis) {
        const msg = lang === 'kn' ? 'ವಿಶ್ಲೇಷಣಾ ಫಲಿತಾಂಶ ಪುಟಕ್ಕೆ ತೆರಳುತ್ತಿದ್ದೇವೆ.' : 'Opening analysis results.';
        setAssistantReply(msg);
        speak(msg);
        onNavigate?.('results');
      } else {
        const msg = lang === 'kn'
          ? 'ಯಾವುದೇ ವಿಶ್ಲೇಷಣೆ ಪೂರ್ಣಗೊಂಡಿಲ್ಲ. ದಯವಿಟ್ಟು ಮೊದಲು ಸಸ್ಯದ ಫೋಟೋ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ.'
          : 'No analysis has been performed yet. Please scan or upload a plant photo first.';
        setAssistantReply(msg);
        speak(msg);
        onNavigate?.('capture');
      }
      return;
    }

    // D. Reports / History
    if (
      cmd.includes('report') ||
      cmd.includes('history') ||
      cmd.includes('previous analyses') ||
      cmd.includes('past scan') ||
      cmd.includes('ವರದಿ') ||
      cmd.includes('ಇತಿಹಾಸ')
    ) {
      const msg = lang === 'kn' ? 'ತಪಾಸಣಾ ವರದಿಗಳು ಮತ್ತು ಇತಿಹಾಸ ಪುಟಕ್ಕೆ ತೆರಳುತ್ತಿದ್ದೇವೆ.' : 'Opening surveillance reports and scan history.';
      setAssistantReply(msg);
      speak(msg);
      onNavigate?.('history');
      return;
    }

    // E. Profile
    if (
      cmd.includes('profile') ||
      cmd.includes('account') ||
      cmd.includes('settings') ||
      cmd.includes('ಪ್ರೊಫೈಲ್') ||
      cmd.includes('ನನ್ನ ಖಾತೆ')
    ) {
      const msg = lang === 'kn' ? 'ಪ್ರೊಫೈಲ್ ಮತ್ತು ಸೆಟ್ಟಿಂಗ್ಸ್ ಪುಟಕ್ಕೆ ತೆರಳುತ್ತಿದ್ದೇವೆ.' : 'Opening profile and settings.';
      setAssistantReply(msg);
      speak(msg);
      onNavigate?.('profile');
      return;
    }

    // F. Model Administration
    if (
      cmd.includes('model training') ||
      cmd.includes('model admin') ||
      cmd.includes('administration') ||
      cmd.includes('ಮಾದರಿ ಆಡಳಿತ')
    ) {
      const msg = lang === 'kn' ? 'ಮಾದರಿ ಆಡಳಿತ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ತೆರೆಯುತ್ತಿದ್ದೇವೆ.' : 'Opening model administration dashboard.';
      setAssistantReply(msg);
      speak(msg);
      onNavigate?.('admin');
      return;
    }

    // G. Go Back
    if (cmd.includes('go back') || cmd.includes('previous') || cmd.includes('ಹಿಂದಕ್ಕೆ') || cmd.includes('ಹಿಂದಿನ ಪುಟ')) {
      const msg = lang === 'kn' ? 'ಹಿಂದಿನ ಪುಟಕ್ಕೆ ತೆರಳುತ್ತಿದ್ದೇವೆ.' : 'Navigating back to the previous page.';
      setAssistantReply(msg);
      speak(msg);
      onGoBack?.();
      return;
    }

    // 2. General AI, Technical, or Agronomic Questions -> Call backend chatbot
    setIsQuerying(true);
    setAssistantReply(lang === 'kn' ? 'ಉತ್ತರವನ್ನು ತಯಾರಿಸಲಾಗುತ್ತಿದೆ...' : 'Thinking...');

    try {
      const token = localStorage.getItem('arecaguard_token');
      const res = await fetch('/api/chatbot/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          message: rawText,
          language: lang,
          current_analysis: currentAnalysis
        })
      });

      if (!res.ok) {
        throw new Error('Chatbot query failed');
      }

      const data = await res.json();
      const reply = data.reply || '';
      setAssistantReply(reply);
      speak(reply);
      onAskChatbot?.(rawText);
    } catch (err) {
      console.error('Voice Assistant query error:', err);
      const errMsg = lang === 'kn'
        ? 'ಕ್ಷಮಿಸಿ, ಉತ್ತರಿಸಲು ಸಾಧ್ಯವಾಗುತ್ತಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಪ್ರಯತ್ನಿಸಿ.'
        : 'Sorry, I encountered an issue fetching the response. Please try again.';
      setAssistantReply(errMsg);
      speak(errMsg);
    } finally {
      setIsQuerying(false);
    }
  };

  const toggleListening = () => {
    if (!speechSupported) {
      alert(lang === 'kn'
        ? 'ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಧ್ವನಿ ಗುರುತಿಸುವಿಕೆ ಬೆಂಬಲಿತವಾಗಿಲ್ಲ. ದಯವಿಟ್ಟು Chrome ಅಥವಾ Edge ಬಳಸಿ.'
        : 'Speech recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.');
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      stopSpeaking();
      try {
        recognitionRef.current?.start();
      } catch (e) {
        console.warn('Recognition start error:', e);
      }
    }
  };

  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      left: '24px',
      zIndex: 90,
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    }}>
      {/* Help Popup Card */}
      {showHelp && (
        <div style={{
          background: '#ffffff',
          borderRadius: '16px',
          padding: '16px 20px',
          boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
          border: '1px solid #cbd5e1',
          maxWidth: '340px',
          fontSize: '0.825rem',
          color: '#334155',
          marginBottom: '6px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <strong style={{ color: '#15803d', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={16} /> {lang === 'kn' ? 'ಧ್ವನಿ ಆದೇಶಗಳ ಉದಾಹರಣೆಗಳು' : 'Voice Assistant Commands'}
            </strong>
            <button
              onClick={() => setShowHelp(false)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: '1rem' }}
            >
              ✕
            </button>
          </div>
          <p style={{ margin: '0 0 6px 0', fontWeight: 600, color: '#0f172a' }}>
            {lang === 'kn' ? 'ನ್ಯಾವಿಗೇಷನ್ ಆದೇಶಗಳು:' : 'Navigation:'}
          </p>
          <ul style={{ margin: '0 0 10px 0', paddingLeft: '18px', lineHeight: 1.5 }}>
            <li>"Open dashboard" / "ಮುಖ್ಯ ಪುಟ"</li>
            <li>"Scan the photo" / "ಚಿತ್ರ ಅಪ್‌ಲೋಡ್"</li>
            <li>"Show analysis results" / "ಫಲಿತಾಂಶ ತೋರಿಸು"</li>
            <li>"Open reports" / "ಹಿಂದಿನ ವರದಿಗಳು"</li>
            <li>"Go back" / "ಹಿಂದಿನ ಪುಟ"</li>
          </ul>
          <p style={{ margin: '0 0 6px 0', fontWeight: 600, color: '#0f172a' }}>
            {lang === 'kn' ? 'ಸಾಮಾನ್ಯ ಹಾಗೂ AI ಪ್ರಶ್ನೆಗಳು:' : 'General & AI Questions:'}
          </p>
          <ul style={{ margin: 0, paddingLeft: '18px', lineHeight: 1.5 }}>
            <li>"What is machine learning?"</li>
            <li>"Explain CNN and deep learning"</li>
            <li>"Giant African Snail control remedies"</li>
            <li>"Is my plant healthy?"</li>
          </ul>
        </div>
      )}

      {/* Floating Status & Reply Window */}
      {(isListening || isSpeaking || isQuerying || transcript || assistantReply) && (
        <div style={{
          background: '#ffffff',
          border: '1px solid #bbf7d0',
          borderRadius: '16px',
          padding: '12px 18px',
          boxShadow: '0 6px 24px rgba(0,0,0,0.12)',
          fontSize: '0.85rem',
          color: '#14532d',
          maxWidth: '360px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px'
        }}>
          {/* Header Row */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700 }}>
              {isListening && (
                <>
                  <Radio size={16} className="animate-pulse" color="#dc2626" />
                  <span style={{ color: '#dc2626' }}>{lang === 'kn' ? 'ಆಲಿಸುತ್ತಿದೆ...' : 'Listening...'}</span>
                </>
              )}
              {isQuerying && (
                <>
                  <Sparkles size={16} className="animate-spin" color="#16a34a" />
                  <span style={{ color: '#16a34a' }}>{lang === 'kn' ? 'ಯೋಚಿಸುತ್ತಿದೆ...' : 'Thinking...'}</span>
                </>
              )}
              {isSpeaking && (
                <>
                  <Volume2 size={16} className="animate-bounce" color="#16a34a" />
                  <span style={{ color: '#15803d' }}>{lang === 'kn' ? 'ಓದಲಾಗುತ್ತಿದೆ...' : 'Speaking...'}</span>
                </>
              )}
              {!isListening && !isQuerying && !isSpeaking && (
                <span style={{ color: '#047857' }}>{lang === 'kn' ? 'ಸಹಾಯಕ' : 'Voice Assistant'}</span>
              )}
            </div>

            {/* Stop Speaking Button */}
            {isSpeaking && (
              <button
                onClick={stopSpeaking}
                style={{
                  background: '#fee2e2',
                  border: '1px solid #f87171',
                  color: '#b91c1c',
                  borderRadius: '12px',
                  padding: '3px 8px',
                  fontSize: '0.725rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Square size={10} fill="#b91c1c" /> {lang === 'kn' ? 'ನಿಲ್ಲಿಸಿ' : 'Stop'}
              </button>
            )}
          </div>

          {/* User Transcript */}
          {transcript && (
            <div style={{ color: '#475569', fontStyle: 'italic', fontSize: '0.8rem' }}>
              "{transcript}"
            </div>
          )}

          {/* Assistant Text Preview */}
          {assistantReply && !isQuerying && (
            <div style={{
              color: '#0f172a',
              maxHeight: '140px',
              overflowY: 'auto',
              borderTop: '1px solid #f1f5f9',
              paddingTop: '6px',
              lineHeight: 1.45,
              fontSize: '0.8rem'
            }}>
              {assistantReply}
            </div>
          )}
        </div>
      )}

      {/* Main Bottom Control Buttons */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Main Microphone Button */}
        <button
          onClick={toggleListening}
          title={isListening ? 'Stop Listening' : t.voiceTitle}
          style={{
            width: '52px',
            height: '52px',
            borderRadius: '50%',
            border: 'none',
            background: isListening
              ? 'linear-gradient(135deg, #dc2626, #ef4444)'
              : 'linear-gradient(135deg, #15803d, #16a34a)',
            color: '#ffffff',
            boxShadow: isListening
              ? '0 0 0 6px rgba(220,38,38,0.25), 0 4px 14px rgba(0,0,0,0.2)'
              : '0 4px 14px rgba(21,128,61,0.35)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
            transform: isListening ? 'scale(1.08)' : 'scale(1)'
          }}
        >
          {isListening ? <MicOff size={24} /> : <Mic size={24} />}
        </button>

        {/* Speaker Mute/Unmute Toggle */}
        <button
          onClick={() => {
            if (isSpeaking) stopSpeaking();
            setSpeechEnabled(!speechEnabled);
          }}
          title={speechEnabled ? 'Mute Speech Audio' : 'Enable Speech Audio'}
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '50%',
            border: '1px solid #cbd5e1',
            background: '#ffffff',
            color: speechEnabled ? '#15803d' : '#94a3b8',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
          }}
        >
          {speechEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
        </button>

        {/* Commands Help Button */}
        <button
          onClick={() => setShowHelp(!showHelp)}
          title="Voice Commands Guide"
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '50%',
            border: '1px solid #cbd5e1',
            background: '#ffffff',
            color: '#475569',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
          }}
        >
          <HelpCircle size={18} />
        </button>
      </div>
    </div>
  );
}
