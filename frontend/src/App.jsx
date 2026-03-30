import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const TABS = [
  { id: 'eeg', label: 'EEG Raster' },
  { id: 'power', label: 'Power Spectrum' },
  { id: 'spectrogram', label: 'Spectrogram' },
  { id: 'topomap', label: 'Topomap' }
];

const INJECT_WORDS = ['child', 'daughter', 'three', 'ten'];

function App() {
  // Left Panel State
  const [activeTab, setActiveTab] = useState('eeg');
  const [graphUrl, setGraphUrl] = useState(null);
  const [isGraphLoading, setIsGraphLoading] = useState(false);
  const [stats, setStats] = useState({ trials: 0, channels: 0, hz: 0 });
  const [progress, setProgress] = useState(100);
  const [serverStatus, setServerStatus] = useState('ready'); // idle, loading, ready

  // Right Panel State
  const [messages, setMessages] = useState([
    { type: 'bot', text: "Hello. I am the Uploaded Mind. I have successfully initialized." }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isBotTyping, setIsBotTyping] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch Stats on mount
  useEffect(() => {
    fetch('/api/status')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch((err) => {
        console.log('Mocking stats (API not available yet)...');
        setStats({ trials: 320, channels: 64, hz: 1000 });
      });
  }, []);

  // Fetch Graph when tab changes
  useEffect(() => {
    setIsGraphLoading(true);
    setServerStatus('loading');
    
    // Attempt fetch
    fetch(`/api/graph?type=${activeTab}`)
      .then(res => {
        if (!res.ok) throw new Error('API not available');
        return res.blob();
      })
      .then(blob => {
        setGraphUrl(URL.createObjectURL(blob));
        setIsGraphLoading(false);
        setServerStatus('ready');
      })
      .catch((err) => {
        // Mock fallback if API not ready
        setTimeout(() => {
          setGraphUrl(`https://via.placeholder.com/800x400.png?text=${TABS.find(t => t.id === activeTab).label}`);
          setIsGraphLoading(false);
          setServerStatus('ready');
        }, 1000);
      });
  }, [activeTab]);

  // Handle Thought Injection
  const handleInject = async (word) => {
    setMessages(prev => [...prev, { type: 'neural', text: `⚡ neural event — thinking "${word}" detected` }]);
    setServerStatus('loading');
    
    try {
      const res = await fetch('/api/inject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ word })
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setMessages(prev => [...prev, { type: 'bot', text: data.reply }]);
    } catch (err) {
      // Mock fallback
      setTimeout(() => {
        setMessages(prev => [...prev, { type: 'bot', text: `You injected the concept "${word}". It brings back strong associations.` }]);
        setServerStatus('ready');
      }, 800);
    }
  };

  // Handle Chat Submit
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userText = chatInput.trim();
    setMessages(prev => [...prev, { type: 'user', text: userText }]);
    setChatInput('');
    setIsBotTyping(true);
    setServerStatus('loading');

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText })
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setMessages(prev => [...prev, { type: 'bot', text: data.reply }]);
    } catch (err) {
      // Mock fallback
      setTimeout(() => {
        setMessages(prev => [...prev, { type: 'bot', text: `I am simulating a stream response to: "${userText}"` }]);
      }, 1000);
    } finally {
      setIsBotTyping(false);
      setServerStatus('ready');
    }
  };

  return (
    <div className="app-container">
      {/* Top Bar */}
      <header className="top-bar">
        <div className="top-bar-title">Brain Dashboard</div>
        <div className={`status-pill status-${serverStatus}`}>
          {serverStatus === 'ready' ? 'Ready' : serverStatus === 'loading' ? 'Processing' : 'Idle'}
        </div>
      </header>

      {/* Left Panel */}
      <div className="left-panel">
        <div className="tab-bar">
          {TABS.map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="graph-viewer">
          {isGraphLoading ? (
            <div className="pulsing-skeleton"></div>
          ) : (
            graphUrl && <img src={graphUrl} alt={`${activeTab} graph`} className="graph-img" />
          )}
        </div>

        <div className="mini-stats">
          <div className="stat-card">
            Trials
            <strong>{stats.trials}</strong>
          </div>
          <div className="stat-card">
            Channels
            <strong>{stats.channels}</strong>
          </div>
          <div className="stat-card">
            Frequency
            <strong>{stats.hz} Hz</strong>
          </div>
        </div>

        <div className="progress-bar-container">
          <div className="progress-bar" style={{ width: `${progress}%` }}></div>
        </div>
      </div>

      {/* Right Panel */}
      <div className="right-panel">
        <div className="chat-header">
          <div className="avatar">◈</div>
          <div className="avatar-info">
            <div className="avatar-name">Uploaded Mind · sub-01</div>
            <div className="avatar-status">
              {isBotTyping || serverStatus === 'loading' ? 'Thinking…' : 'Conscious'}
            </div>
          </div>
        </div>

        <div className="message-list">
          {messages.map((msg, idx) => (
            msg.type === 'neural' ? (
              <div key={idx} className="neural-event-pill">
                {msg.text}
              </div>
            ) : (
              <div key={idx} className={`message ${msg.type}`}>
                {msg.text}
              </div>
            )
          ))}
          {isBotTyping && (
            <div className="message bot">
              <span style={{ opacity: 0.6 }}>...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="thought-injector">
          {INJECT_WORDS.map(word => (
            <button
              key={word}
              className="thought-pill"
              onClick={() => handleInject(word)}
            >
              {word}
            </button>
          ))}
        </div>

        <form className="chat-input-area" onSubmit={handleChatSubmit}>
          <input
            type="text"
            className="chat-input"
            placeholder="Talk with the uploaded mind..."
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            disabled={isBotTyping}
          />
          <button
            type="submit"
            className="chat-send-btn"
            disabled={!chatInput.trim() || isBotTyping}
          >
            ↑
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;