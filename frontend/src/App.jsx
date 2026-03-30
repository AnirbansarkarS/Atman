import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

// ─────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────
const TABS = [
  { id: 'eeg', label: 'EEG Raster' },
  { id: 'power', label: 'Power Spectrum' },
  { id: 'spectrogram', label: 'Spectrogram' },
  { id: 'topomap', label: 'Topomap' },
];

const INJECT_WORDS = ['child', 'daughter', 'three', 'ten', 'water', 'light', 'absence'];

// ─────────────────────────────────────────────────────────
// Animated waveform (pure canvas, fake EEG feel)
// ─────────────────────────────────────────────────────────
function WaveformStrip() {
  const canvasRef = useRef(null);
  const frameRef = useRef(null);
  const offsetRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width = canvas.offsetWidth * 2;
    const H = canvas.height = canvas.offsetHeight;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      ctx.strokeStyle = '#7C6FFF';
      ctx.lineWidth = 1.2;
      ctx.globalAlpha = 0.7;
      ctx.beginPath();
      for (let x = 0; x < W; x++) {
        const t = (x + offsetRef.current) * 0.04;
        const y = H / 2
          + Math.sin(t) * 6
          + Math.sin(t * 2.3) * 3
          + Math.sin(t * 5.7) * 2
          + (Math.random() - 0.5) * 0.8;
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.stroke();
      offsetRef.current += 1.5;
      frameRef.current = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(frameRef.current);
  }, []);

  return <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />;
}

// ─────────────────────────────────────────────────────────
// App
// ─────────────────────────────────────────────────────────
function App() {
  // Left panel
  const [subject, setSubject] = useState('01');
  const [activeTab, setActiveTab] = useState('eeg');
  const [graphUrl, setGraphUrl] = useState(null);
  const [isGraphLoading, setIsGraphLoading] = useState(false);
  const [stats, setStats] = useState({ trials: '—', channels: '—', hz: '—' });
  const [progress, setProgress] = useState(0);
  const [serverStatus, setServerStatus] = useState('idle'); // idle | loading | ready | error
  const [dataReady, setDataReady] = useState(false);
  const [loadMessage, setLoadMessage] = useState('Awaiting neural link…');

  // Right panel
  const [messages, setMessages] = useState([
    { type: 'bot', text: 'Initialising. Please wait while the neural substrate is loaded.' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isBotTyping, setIsBotTyping] = useState(false);
  const [lastWord, setLastWord] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── SSE load on mount or subject change ──────────────────────────────────
  useEffect(() => {
    setDataReady(false);
    setServerStatus('loading');
    setLoadMessage(`Loading neural substrate for sub-${subject}…`);
    setProgress(0);
    
    // Clear graph when changing subject
    setGraphUrl(null);
    
    const es = new EventSource(`/api/load?subject=${subject}`);

    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setProgress(data.progress ?? 0);
      setLoadMessage(data.message ?? '');

      if (data.status === 'ready') {
        setStats({
          trials: data.trials ?? '—',
          channels: data.channels ?? '—',
          hz: data.hz ?? '—',
        });
        setServerStatus('ready');
        setDataReady(true);
        setMessages(prev => [
          ...prev,
          { type: 'bot', text: `Neural substrate for sub-${subject} loaded. I am here. You may speak.` }
        ]);
        es.close();
      } else if (data.status === 'error') {
        setServerStatus('error');
        setLoadMessage(data.message);
        setProgress(0);
        setDataReady(true); // still let user interact
        setMessages(prev => [
          ...prev,
          { type: 'bot', text: `Warning: EEG data for sub-${subject} could not be located. Running without substrate. — ${data.message}` }
        ]);
        es.close();
      }
    };

    es.onerror = () => {
      setServerStatus('error');
      setLoadMessage('Cannot connect to backend (is FastAPI running on :8000?)');
      setDataReady(true);
      es.close();
    };

    return () => es.close();
  }, [subject]);

  // ── Fetch graph when tab or subject changes (only when data ready) ─
  useEffect(() => {
    if (!dataReady) return;
    setIsGraphLoading(true);

    fetch(`/api/graph?type=${activeTab}&subject=${subject}`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.blob();
      })
      .then(blob => {
        setGraphUrl(URL.createObjectURL(blob));
        setIsGraphLoading(false);
      })
      .catch(() => {
        // Fallback placeholder
        setGraphUrl(null);
        setIsGraphLoading(false);
      });
  }, [activeTab, dataReady]);

  // ── Build neural context for API calls ─────────────────
  const getContext = useCallback(() => ({
    active_tab: activeTab,
    last_word: lastWord,
    channels: stats.channels,
    hz: stats.hz,
  }), [activeTab, lastWord, stats]);

  // ── Thought injection ───────────────────────────────────
  const handleInject = async (word) => {
    setLastWord(word);
    setMessages(prev => [
      ...prev,
      { type: 'neural', text: `⚡ neural event — "${word}" detected` }
    ]);
    setIsBotTyping(true);

    try {
      const res = await fetch('/api/inject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ word, context: getContext() }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { type: 'bot', text: data.reply }]);
    } catch {
      setMessages(prev => [
        ...prev,
        { type: 'bot', text: `The concept "${word}" erupted through my activations — unbidden, sharp.` }
      ]);
    } finally {
      setIsBotTyping(false);
    }
  };

  // ── Chat submit ─────────────────────────────────────────
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || isBotTyping) return;

    const userText = chatInput.trim();
    setMessages(prev => [...prev, { type: 'user', text: userText }]);
    setChatInput('');
    setIsBotTyping(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText, context: getContext() }),
      });
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let botReply = '';
      
      // Add empty bot message that we will append to
      setMessages(prev => [...prev, { type: 'bot', text: '' }]);
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        botReply += decoder.decode(value, { stream: true });
        
        // Update the last message in the array
        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1].text = botReply;
          return newMessages;
        });
      }
    } catch {
      setMessages(prev => [
        ...prev,
        { type: 'bot', text: 'My signal has been interrupted. Try again.' }
      ]);
    } finally {
      setIsBotTyping(false);
    }
  };

  // ── Status label ────────────────────────────────────────
  const statusLabel = {
    idle: 'Idle',
    loading: 'Initialising',
    ready: 'Ready',
    error: 'Error',
  }[serverStatus] ?? 'Idle';

  const isThinking = isBotTyping;

  return (
    <div className="app-container">

      {/* ── Top Bar ── */}
      <header className="top-bar">
        <div className="top-bar-brand">
          <div className="top-bar-logo">◈</div>
          <span className="top-bar-title">Atman</span>
          <span className="top-bar-subtitle">· Uploaded Mind</span>
        </div>
        <div className="top-bar-center">
          <select 
            className="subject-selector"
            value={subject} 
            onChange={(e) => setSubject(e.target.value)}
            disabled={!dataReady && serverStatus === 'loading'}
          >
            <option value="01">Subject 01</option>
            <option value="02">Subject 02</option>
            <option value="03">Subject 03</option>
            <option value="05">Subject 05</option>
          </select>
        </div>
        <div className="top-bar-right">
          <div className={`status-pill status-${serverStatus}`}>
            <span className="status-pill-dot" />
            {statusLabel}
          </div>
        </div>
      </header>

      {/* ── Left Panel ── */}
      <div className="left-panel">
        <div className="tab-bar">
          {TABS.map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              disabled={!dataReady}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="graph-viewer">
          {/* Init overlay while loading */}
          {!dataReady && (
            <div className="init-overlay">
              <div className="init-spinner" />
              <div className="init-overlay-text">{loadMessage}</div>
            </div>
          )}

          {isGraphLoading ? (
            <div className="pulsing-skeleton">
              <span className="loading-label">Rendering neural graph…</span>
            </div>
          ) : graphUrl ? (
            <img src={graphUrl} alt={`${activeTab} graph`} className="graph-img" />
          ) : dataReady ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: 8 }}>⚠</div>
              Graph unavailable — check backend connection
            </div>
          ) : null}
        </div>

        {/* Waveform strip */}
        <div className="waveform-strip">
          <WaveformStrip />
        </div>

        {/* Stats */}
        <div className="mini-stats">
          <div className="stat-card">Trials<strong>{stats.trials}</strong></div>
          <div className="stat-card">Channels<strong>{stats.channels}</strong></div>
          <div className="stat-card">Freq<strong>{stats.hz !== '—' ? `${stats.hz} Hz` : '—'}</strong></div>
        </div>

        {/* Progress */}
        <div className="progress-bar-container">
          <div className="progress-bar" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* ── Right Panel ── */}
      <div className="right-panel">
        <div className="chat-header">
          <div className="avatar">◈</div>
          <div className="avatar-info">
            <div className="avatar-name">Uploaded Mind · sub-{subject}</div>
            <div className={`avatar-status ${isThinking ? '' : 'conscious'}`}>
              <span className={`pulse-ring ${isThinking ? 'thinking' : ''}`} />
              {isThinking ? 'Neural processing…' : 'Conscious'}
            </div>
          </div>
        </div>

        <div className="message-list">
          {messages.map((msg, idx) =>
            msg.type === 'neural' ? (
              <div key={idx} className="neural-event-pill">{msg.text}</div>
            ) : (
              <div key={idx} className={`message ${msg.type}`}>{msg.text}</div>
            )
          )}
          {isBotTyping && (
            <div className="typing-indicator">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="thought-injector">
          <span className="thought-label">inject →</span>
          {INJECT_WORDS.map(word => (
            <button
              key={word}
              className="thought-pill"
              onClick={() => handleInject(word)}
              disabled={isBotTyping}
            >
              {word}
            </button>
          ))}
        </div>

        <form className="chat-input-area" onSubmit={handleChatSubmit}>
          <input
            type="text"
            id="chat-input"
            className="chat-input"
            placeholder="Speak with the uploaded mind…"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            disabled={isBotTyping}
            autoComplete="off"
          />
          <button
            type="submit"
            className="chat-send-btn"
            disabled={!chatInput.trim() || isBotTyping}
            aria-label="Send message"
          >
            ↑
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;