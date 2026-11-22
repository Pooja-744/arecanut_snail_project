import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Sparkles, Sprout, Minimize2, Maximize2, Bot } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import FormattedMessage from './FormattedMessage';

export default function Chatbot({ externalTriggerText, onClearExternalTrigger, currentAnalysis }) {
  const { lang, t } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [inputMsg, setInputMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: lang === 'kn'
        ? 'ನಮಸ್ಕಾರ! ನಾನು **ArecaKisan AI**.\n\nನಾನು ಆರ್ಟಿಫಿಶಿಯಲ್ ಇಂಟೆಲಿಜೆನ್ಸ್, ಕಂಪ್ಯೂಟರ್ ಸೈನ್ಸ್, ಅಡಿಕೆ ರೋಗಗಳು (ಕೊಳೆರೋಗ, ಸುಳಿಕೊಳೆ), ದೈತ್ಯ ಆಫ್ರಿಕನ್ ಬಸವನಹುಳು ನಿಯಂತ್ರಣ, ಮನೆಮದ್ದುಗಳು ಮತ್ತು ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಸಸ್ಯದ ತಪಾಸಣಾ ವಿವರಗಳ ಬಗ್ಗೆ ಉತ್ತರಿಸಬಲ್ಲೆ. ನೀವು ಏನು ತಿಳಿಯಲು ಬಯಸುತ್ತೀರಿ?'
        : 'Hello! I am **ArecaKisan AI**, your versatile general AI assistant and plantation expert.\n\nI can answer questions on Artificial Intelligence, Machine Learning, CNNs, Python, as well as Giant African Snail control, arecanut diseases, home remedies, and your live plant scan results. How can I assist you today?'
    }
  ]);

  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  // Handle voice triggers passed from VoiceAssistant
  useEffect(() => {
    if (externalTriggerText) {
      setIsOpen(true);
      sendMessage(externalTriggerText);
      onClearExternalTrigger?.();
    }
  }, [externalTriggerText]);

  const sendMessage = async (textToSend) => {
    const text = textToSend || inputMsg;
    if (!text.trim() || loading) return;

    const userMessage = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMessage]);
    if (!textToSend) setInputMsg('');
    setLoading(true);

    try {
      const token = localStorage.getItem('arecaguard_token');
      const res = await fetch('/api/chatbot/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
          language: lang,
          current_analysis: currentAnalysis
        })
      });

      if (!res.ok) {
        throw new Error('API request failed');
      }

      const data = await res.json();
      if (data.session_id) setSessionId(data.session_id);

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.reply || 'No response generated.' }
      ]);
    } catch (err) {
      console.warn('Chatbot error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: lang === 'kn'
            ? 'ಕ್ಷಮಿಸಿ, ಸಂಪರ್ಕದಲ್ಲಿ ಸಮಸ್ಯೆಯಾಗಿದೆ. ಸ್ಥಳೀಯ ತುರ್ತು ಮಾಹಿತಿ: ಬಸವನಹುಳುಗಳಿಗಾಗಿ ಮುಂಜಾನೆ ಕೈಯಿಂದ ಆರಿಸಿ 15% ಉಪ್ಪುನೀರಿನಲ್ಲಿ ಹಾಕಿ, ಬುಡಕ್ಕೆ ಸುಣ್ಣದ ಉಂಗುರ ಹಾಕಿ. ಕೊಳೆರೋಗಕ್ಕೆ 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಸಿಂಪಡಿಸಿ.'
            : 'Connection error. Offline advice: For Giant African Snail, hand-pick at dawn into 15% salt brine, and apply slaked lime barrier rings. For Koleroga, spray 1% Bordeaux mixture.'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Chat Trigger Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            zIndex: 90,
            background: 'linear-gradient(135deg, #15803d 0%, #16a34a 100%)',
            color: '#ffffff',
            border: 'none',
            borderRadius: '28px',
            padding: '14px 22px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            boxShadow: '0 6px 20px rgba(21,128,61,0.35)',
            cursor: 'pointer',
            fontWeight: 700,
            fontSize: '0.9rem',
            transition: 'all 0.2s',
          }}
          className="hover:scale-105"
        >
          <Bot size={20} />
          {t.chatTitle}
        </button>
      )}

      {/* Floating Chatbot Window */}
      {isOpen && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 95,
          width: '420px',
          maxWidth: '92vw',
          height: isMinimized ? '58px' : '560px',
          background: '#ffffff',
          borderRadius: '16px',
          boxShadow: '0 12px 36px rgba(0,0,0,0.18)',
          border: '1px solid #e2e8f0',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          transition: 'height 0.25s ease'
        }}>
          {/* Header */}
          <div style={{
            background: 'linear-gradient(135deg, #14532d 0%, #15803d 100%)',
            color: '#ffffff',
            padding: '12px 18px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ background: '#22c55e', color: '#14532d', padding: '6px', borderRadius: '8px' }}>
                <Bot size={18} />
              </div>
              <div>
                <h4 style={{ fontSize: '0.925rem', fontWeight: 800, margin: 0 }}>{t.chatTitle}</h4>
                <p style={{ fontSize: '0.7rem', opacity: 0.85, margin: 0 }}>{t.chatSubtitle}</p>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                onClick={(e) => { e.stopPropagation(); setIsMinimized(!isMinimized); }}
                style={{ background: 'transparent', border: 'none', color: '#ffffff', cursor: 'pointer', opacity: 0.8 }}
                title={isMinimized ? 'Expand' : 'Minimize'}
              >
                {isMinimized ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); setIsOpen(false); }}
                style={{ background: 'transparent', border: 'none', color: '#ffffff', cursor: 'pointer', opacity: 0.8 }}
                title="Close"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {!isMinimized && (
            <>
              {/* Quick Prompt Chips */}
              <div style={{
                display: 'flex',
                gap: '6px',
                padding: '8px 12px',
                background: '#f8fafc',
                borderBottom: '1px solid #e2e8f0',
                overflowX: 'auto',
                whiteSpace: 'nowrap'
              }}>
                {[
                  { label: t.chipML || "What is ML & CNN?", text: 'Explain machine learning and convolutional neural networks in simple terms.' },
                  { label: t.chipHomeRemedies || "Home remedies", text: 'What are the best organic and home remedies for Giant African Snail control?' },
                  { label: t.chipBordeaux, text: 'How to prepare 1% Bordeaux mixture for arecanut?' },
                  { label: t.chipKoleroga, text: 'What is the full treatment protocol for Koleroga (Mahali)?' }
                ].map((chip, idx) => (
                  <button
                    key={idx}
                    onClick={() => sendMessage(chip.text)}
                    style={{
                      background: '#ffffff',
                      border: '1px solid #cbd5e1',
                      borderRadius: '16px',
                      padding: '4px 10px',
                      fontSize: '0.725rem',
                      fontWeight: 600,
                      color: '#334155',
                      cursor: 'pointer',
                      flexShrink: 0
                    }}
                  >
                    {chip.label}
                  </button>
                ))}
              </div>

              {/* Messages Container */}
              <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                background: '#f8fafc'
              }}>
                {messages.map((m, idx) => {
                  const isUser = m.role === 'user';
                  return (
                    <div
                      key={idx}
                      style={{
                        alignSelf: isUser ? 'flex-end' : 'flex-start',
                        maxWidth: '85%',
                        background: isUser ? '#15803d' : '#ffffff',
                        color: isUser ? '#ffffff' : '#0f172a',
                        borderRadius: isUser ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                        padding: '10px 14px',
                        fontSize: '0.875rem',
                        border: isUser ? 'none' : '1px solid #e2e8f0',
                        boxShadow: '0 2px 6px rgba(0,0,0,0.04)'
                      }}
                    >
                      {isUser ? (
                        <p style={{ margin: 0 }}>{m.content}</p>
                      ) : (
                        <FormattedMessage content={m.content} />
                      )}
                    </div>
                  );
                })}
                {loading && (
                  <div style={{ alignSelf: 'flex-start', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '8px 14px', fontSize: '0.8rem', color: '#64748b' }}>
                    {t.chatTyping}
                  </div>
                )}
                <div ref={scrollRef} />
              </div>

              {/* Input Footer */}
              <div style={{
                padding: '10px 14px',
                background: '#ffffff',
                borderTop: '1px solid #e2e8f0',
                display: 'flex',
                gap: '8px'
              }}>
                <input
                  type="text"
                  placeholder={t.chatPlaceholder}
                  value={inputMsg}
                  onChange={(e) => setInputMsg(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                  style={{
                    flex: 1,
                    padding: '10px 12px',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                />
                <button
                  onClick={() => sendMessage()}
                  disabled={!inputMsg.trim() || loading}
                  style={{
                    background: '#15803d',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '0 14px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <Send size={16} />
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}
