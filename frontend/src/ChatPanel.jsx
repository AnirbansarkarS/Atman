import React, { useState } from 'react';

const ChatPanel = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');

    const handleSend = () => {
        if (input.trim()) {
            setMessages([...messages, { text: input, sender: 'user' }]);
            // TODO: Send to backend and get AI response
            setInput('');
        }
    };

    const injectThought = (thought) => {
        // TODO: Handle thought injection
        console.log(`Injecting thought: ${thought}`);
    };

    return (
        <div>
            <div className="messages">
                {messages.map((msg, index) => (
                    <div key={index} className={`message ${msg.sender}`}>
                        {msg.text}
                    </div>
                ))}
            </div>
            <div className="input-area">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                />
                <button onClick={handleSend}>Send</button>
            </div>
            <div className="thought-injectors">
                <button onClick={() => injectThought('focus')}>Focus</button>
                <button onClick={() => injectThought('relax')}>Relax</button>
                <button onClick={() => injectThought('clarity')}>Clarity</button>
            </div>
        </div>
    );
};

export default ChatPanel;
