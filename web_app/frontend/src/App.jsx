import React, { useState, useEffect, useRef } from 'react';
import { Send, Settings, Bot, User, BrainCircuit, Loader2, Play } from 'lucide-react';

function App() {
    const [view, setView] = useState('setup'); // 'setup' or 'chat'
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [models, setModels] = useState([]);

    const [config, setConfig] = useState({
        chatbot_model: 'deepseek/deepseek-r1-0528-qwen3-8b',
        patient_model: 'openai/gpt-oss-20b',
        psychologist_system_prompt: "You are a Psychologist. Be warm, empathetic, and professional. Respond to the patient's input.",
        patient_system_prompt: "You are acting as the Patient in this therapy session. Your goal is to suggest a natural, authentic response to the Psychologist's last message. Do not be too formal. React to what the psychologist just said. Output ONLY the suggested response text, nothing else."
    });

    const messagesEndRef = useRef(null);

    useEffect(() => {
        fetchModels();
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const fetchModels = async () => {
        try {
            const res = await fetch('/api/models');
            const data = await res.json();
            setModels(data.models);
        } catch (e) {
            console.error("Failed to fetch models", e);
            setModels(['deepseek/deepseek-r1-0528-qwen3-8b', 'openai/gpt-oss-20b']);
        }
    };

    const startSession = () => {
        setView('chat');
    };

    const endSession = () => {
        if (window.confirm("Are you sure you want to end this session? Chat history will be lost.")) {
            setMessages([]);
            setView('setup');
        }
    };

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const history = messages.map(m => ({ role: m.role, content: m.content }));

            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMsg.content,
                    history: history,
                    chatbot_model: config.chatbot_model,
                    patient_model: config.patient_model,
                    psychologist_system_prompt: config.psychologist_system_prompt,
                    patient_system_prompt: config.patient_system_prompt
                })
            });

            if (!res.ok) throw new Error('Network response was not ok');

            const data = await res.json();

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.response
            }]);

            if (data.suggested_reply) {
                setInput(data.suggested_reply);
            }

        } catch (error) {
            console.error("Error sending message:", error);
            setMessages(prev => [...prev, { role: 'assistant', content: "Error: Could not connect to the backend." }]);
        } finally {
            setLoading(false);
        }
    };

    if (view === 'setup') {
        return (
            <div className="app-container setup-view">
                <header className="header">
                    <div className="logo">
                        <BrainCircuit className="icon-logo" />
                        <h1>DualMind <span className="subtitle">Setup</span></h1>
                    </div>
                </header>

                <div className="setup-panel">
                    <h2>Session Configuration</h2>

                    <div className="config-section">
                        <h3>Psychologist (Chatbot)</h3>
                        <div className="form-group">
                            <label>Model</label>
                            <select
                                value={config.chatbot_model}
                                onChange={e => setConfig({ ...config, chatbot_model: e.target.value })}
                            >
                                {models.map(m => <option key={m} value={m}>{m}</option>)}
                            </select>
                        </div>
                        <div className="form-group">
                            <label>System Prompt</label>
                            <textarea
                                value={config.psychologist_system_prompt}
                                onChange={e => setConfig({ ...config, psychologist_system_prompt: e.target.value })}
                                rows={4}
                            />
                        </div>
                    </div>

                    <div className="config-section">
                        <h3>Patient Helper (Suggestion Engine)</h3>
                        <div className="form-group">
                            <label>Model</label>
                            <select
                                value={config.patient_model}
                                onChange={e => setConfig({ ...config, patient_model: e.target.value })}
                            >
                                {models.map(m => <option key={m} value={m}>{m}</option>)}
                            </select>
                        </div>
                        <div className="form-group">
                            <label>System Prompt</label>
                            <textarea
                                value={config.patient_system_prompt}
                                onChange={e => setConfig({ ...config, patient_system_prompt: e.target.value })}
                                rows={4}
                            />
                        </div>
                    </div>

                    <button className="btn-primary start-btn" onClick={startSession}>
                        <Play size={20} /> Start Session
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="app-container chat-view">
            <header className="header">
                <div className="logo">
                    <BrainCircuit className="icon-logo" />
                    <h1>DualMind <span className="subtitle">Therapy Session</span></h1>
                </div>
                <button className="btn-icon" onClick={endSession} title="End Session & Configure">
                    <Settings size={20} />
                </button>
            </header>

            <div className="chat-area">
                {messages.length === 0 && (
                    <div className="welcome-screen">
                        <BrainCircuit size={64} className="welcome-icon" />
                        <h2>Session Started</h2>
                        <p>Say "Hello" to start the conversation.</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div key={idx} className={`message-row ${msg.role}`}>
                        <div className="avatar">
                            {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                        </div>
                        <div className="message-content">
                            <div className="text">{msg.content}</div>
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="message-row assistant loading">
                        <div className="avatar"><Bot size={20} /></div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <Loader2 className="spinner" size={16} />
                                <span>Psychologist is thinking...</span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form className="input-area" onSubmit={sendMessage}>
                <input
                    type="text"
                    placeholder="Type your message..."
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    disabled={loading}
                />
                <button type="submit" disabled={loading || !input.trim()}>
                    <Send size={20} />
                </button>
            </form>
        </div>
    );
}

export default App;
