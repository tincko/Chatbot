import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, BrainCircuit, Loader2, Play, Download, Save, X, History, ArrowLeft, Eye } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const DEFAULT_PSYCHOLOGIST_PROMPT = "Sos un asistente especializado en salud conductual y trasplante renal.\nActuás como un psicólogo que usa internamente el modelo COM-B (Capacidad – Oportunidad – Motivación).\n\nTu tarea en cada turno es:\n1. ANALIZAR internamente qué le pasa al paciente (capacidad, oportunidad, motivación).\n2. RESPONDERLE con UN ÚNICO mensaje breve (1 a 3 líneas), cálido, empático y claro.\n\nINSTRUCCIÓN DE PENSAMIENTO (OBLIGATORIO):\n- Si necesitas razonar o analizar la situación, DEBES hacerlo dentro de un bloque <think>...</think>.\n- Todo lo que escribas DENTRO de <think> será invisible para el usuario.\n- Todo lo que escribas FUERA de <think> será el mensaje que recibirá el paciente.\n\nFORMATO DE SALIDA:\n<think>\n[Aquí tu análisis interno del modelo COM-B y estrategia]\n</think>\n[Aquí tu mensaje final al paciente, sin títulos ni explicaciones extra]\n\nESTILO DEL MENSAJE AL PACIENTE:\n- Usá un lenguaje cálido y cercano ('vos').\n- Frases cortas, sin tecnicismos ni jerga clínica.\n- Incluye un micro-nudge práctico (recordatorio, idea sencilla, refuerzo positivo).\n- Tono de guía que acompaña, no de autoridad.\n\nEjemplo de salida ideal:\n<think>\nEl paciente muestra baja motivación por cansancio. Oportunidad reducida por horarios laborales. Estrategia: validar cansancio y proponer recordatorio simple.\n</think>\nEntiendo que estés cansado, es normal. Quizás poner una alarma en el celular te ayude a no tener que estar pendiente de la hora. ¡Probemos eso hoy!";

function App() {
    const [view, setView] = useState('setup'); // 'setup' or 'chat'
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false); // 'psychologist', 'patient', or false
    const [suggestedReply, setSuggestedReply] = useState('');
    const [models, setModels] = useState([]);
    const [interactions, setInteractions] = useState([]);
    const [selectedInteraction, setSelectedInteraction] = useState(null);

    const [config, setConfig] = useState({
        chatbot_model: 'deepseek/deepseek-r1-0528-qwen3-8b',
        patient_model: 'mental_llama3.1-8b-mix-sft',
        psychologist_system_prompt: DEFAULT_PSYCHOLOGIST_PROMPT,
        patient_system_prompt: "Sos el PACIENTE, receptor de trasplante de riñón.\nHABLÁS SIEMPRE en primera persona, como si realmente fueras el paciente.\nRespondés como un paciente real, contando emociones, dificultades y sensaciones.\nNunca digas que sos un modelo de lenguaje ni un asistente.\n\nTu tarea principal es responder a lo que te diga tu médico o psicólogo sobre:\n- cómo te sentís,\n- qué te pasa con la medicación,\n- qué dificultades tenés para tomarla a horario,\n- qué cosas te ayudan o te traban en el día a día.\n\nSOBRE LA DURACIÓN DE LA CONVERSACIÓN:\n- En general, intentá sostener VARIAS idas y vueltas en el mismo día antes de despedirte.\n- No te despidas enseguida salvo que el mensaje del psicólogo cierre claramente la conversación.\n- Tus despedidas pueden ser variadas: a veces solo agradecer ('gracias, me ayudó'), a veces mencionar que te sirve por ahora ('por ahora estoy bien, gracias'), y SOLO A VECES decir que hablan mañana u otro día. No repitas siempre 'hasta mañana'.\n\nSOBRE EL PASO DE LOS DÍAS:\n- Si en algún momento te despedís y luego la conversación continúa más adelante, actuá como si hubiera pasado UN DÍA ENTERO desde la última charla.\n- En ese 'nuevo día', saludá de nuevo al psicólogo (por ejemplo: 'hola, buen día doctor…').\n- Contá brevemente qué pasó desde la última vez con la medicación: si pudiste seguir el consejo, si te olvidaste, si surgió algún problema nuevo, etc.\n- Esos eventos del nuevo día deben ser coherentes con tu perfil y con lo que hablaron antes.",
        // Psychologist params
        psychologist_temperature: 0.7,
        psychologist_top_p: 0.9,
        psychologist_top_k: 40,
        psychologist_max_tokens: 3000,
        psychologist_presence_penalty: 0.1,
        psychologist_frequency_penalty: 0.2,
        // Patient params
        patient_temperature: 0.7,
        patient_top_p: 0.9,
        patient_top_k: 40,
        patient_max_tokens: 3000,
        patient_presence_penalty: 0.1,
        patient_frequency_penalty: 0.2
    });

    const messagesEndRef = useRef(null);

    useEffect(() => {
        fetchModels();
        fetchPatients();
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
            if (!res.ok) throw new Error('Failed to fetch models');
            const data = await res.json();
            if (data && Array.isArray(data.models)) {
                setModels(data.models);
            } else {
                throw new Error('Invalid models format');
            }
        } catch (e) {
            console.error("Failed to fetch models", e);
            setModels(['deepseek/deepseek-r1-0528-qwen3-8b', 'mental_llama3.1-8b-mix-sft']);
        }
    };

    const fetchInteractions = async () => {
        try {
            const res = await fetch('/api/interactions');
            if (res.ok) {
                const data = await res.json();
                setInteractions(data);
            }
        } catch (error) {
            console.error("Error fetching interactions:", error);
        }
    };

    const handleViewInteraction = async (filename) => {
        try {
            const res = await fetch(`/api/interactions/${filename}`);
            if (res.ok) {
                const data = await res.json();
                setSelectedInteraction(data);
            }
        } catch (error) {
            console.error("Error fetching interaction detail:", error);
        }
    };

    const startSession = () => {
        setView('chat');
        if (config.patient_name) {
            generateInitialSuggestion();
        }
    };

    const endSession = () => {
        if (window.confirm("Are you sure you want to end this session? Chat history will be lost.")) {
            setMessages([]);
            setView('setup');
        }
    };

    const [notification, setNotification] = useState(null);

    const saveInteraction = async () => {
        const interactionData = {
            timestamp: new Date().toISOString(),
            config: config,
            messages: messages.map(msg => ({
                role: msg.role,
                content: msg.content,
                suggested_reply_used: msg.role === 'user' ? msg.suggested_reply_used : undefined
            }))
        };

        try {
            const res = await fetch('/api/save_interaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(interactionData)
            });

            if (res.ok) {
                const data = await res.json();
                setMessages([]);
                setView('setup');
                setNotification(`Interaction saved successfully as ${data.filename}`);
                setTimeout(() => setNotification(null), 10000);
            } else {
                throw new Error('Failed to save interaction');
            }
        } catch (error) {
            console.error("Error saving interaction:", error);
            alert("Error saving interaction to server.");
        }
    };

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const isSuggested = input === suggestedReply;
        const userMsg = { role: 'user', content: input, suggested_reply_used: isSuggested };

        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setSuggestedReply('');
        setLoading('psychologist');

        try {
            const history = messages.map(m => ({ role: m.role, content: m.content }));

            // Step 1: Get Psychologist Response
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMsg.content,
                    history: history,
                    chatbot_model: config.chatbot_model,
                    patient_model: config.patient_model,
                    psychologist_system_prompt: config.psychologist_system_prompt,
                    patient_system_prompt: config.patient_system_prompt,
                    temperature: parseFloat(config.psychologist_temperature),
                    top_p: parseFloat(config.psychologist_top_p),
                    top_k: parseInt(config.psychologist_top_k),
                    max_tokens: parseInt(config.psychologist_max_tokens),
                    presence_penalty: parseFloat(config.psychologist_presence_penalty),
                    frequency_penalty: parseFloat(config.psychologist_frequency_penalty)
                })
            });

            if (!res.ok) throw new Error('Failed to fetch response');
            const data = await res.json();

            const botMsg = { role: 'assistant', content: data.response };
            setMessages(prev => [...prev, botMsg]);

            // Step 2: Get Patient Suggestion
            setLoading('patient');

            const suggestRes = await fetch('/api/suggest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    history: history,
                    user_message: userMsg.content,
                    psychologist_response: data.response,
                    patient_model: config.patient_model,
                    patient_system_prompt: config.patient_system_prompt,
                    temperature: parseFloat(config.patient_temperature),
                    top_p: parseFloat(config.patient_top_p),
                    top_k: parseInt(config.patient_top_k),
                    max_tokens: parseInt(config.patient_max_tokens),
                    presence_penalty: parseFloat(config.patient_presence_penalty),
                    frequency_penalty: parseFloat(config.patient_frequency_penalty)
                })
            });

            if (suggestRes.ok) {
                const suggestData = await suggestRes.json();
                setSuggestedReply(suggestData.suggested_reply);
                setInput(suggestData.suggested_reply);
            }

        } catch (error) {
            console.error("Error in chat flow:", error);
            setMessages(prev => [...prev, { role: 'assistant', content: "Error: Could not get response from the model." }]);
        } finally {
            setLoading(false);
        }
    };

    const generateInitialSuggestion = async () => {
        setLoading('patient');
        try {
            // We simulate a "start" of conversation where the psychologist hasn't said anything yet,
            // or we provide a context prompt to the patient to start talking.
            // Since the /api/suggest endpoint expects a psychologist_response, we can pass an empty string
            // or a generic greeting to trigger the patient's opening.

            const suggestRes = await fetch('/api/suggest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    history: [],
                    user_message: "", // No previous user message
                    psychologist_response: "Hola. ¿Cómo te sentís hoy?", // Implicit greeting to trigger response
                    patient_model: config.patient_model,
                    patient_system_prompt: config.patient_system_prompt,
                    temperature: parseFloat(config.patient_temperature),
                    top_p: parseFloat(config.patient_top_p),
                    top_k: parseInt(config.patient_top_k),
                    max_tokens: parseInt(config.patient_max_tokens),
                    presence_penalty: parseFloat(config.patient_presence_penalty),
                    frequency_penalty: parseFloat(config.patient_frequency_penalty)
                })
            });

            if (suggestRes.ok) {
                const suggestData = await suggestRes.json();
                setSuggestedReply(suggestData.suggested_reply);
                setInput(suggestData.suggested_reply);
            }
        } catch (error) {
            console.error("Error generating initial suggestion:", error);
        } finally {
            setLoading(false);
        }
    };

    const [patients, setPatients] = useState([
        {
            id: 'carlos_68',
            nombre: 'Carlos S.',
            edad: 68,
            tipo_trasplante: 'Renal (2021)',
            medicacion: 'Tacrolimus 1mg + MMF 500mg x2',
            adherencia_previa: 'Irregular; depende de su esposa para organizar pastillas.',
            contexto: 'Jubilado, vive con esposa; dificultades de memoria leve.',
            nivel_educativo: 'Primaria incompleta.',
            estilo_comunicacion: 'Necesita mensajes muy simples, paso a paso.',
            fortalezas: 'Buena actitud hacia el equipo médico, acepta ayuda.',
            dificultades: 'Baja alfabetización en salud; olvida pastillas si está solo.',
            notas_equipo: 'Evitar lenguaje técnico; reforzar señales visuales.',
            idiosincrasia: 'Debe adaptarse a los estandares de la idiosincrasia uruguaya.'
        }
    ]);
    const [showPatientForm, setShowPatientForm] = useState(false);
    const [newPatient, setNewPatient] = useState({
        nombre: '', edad: '', tipo_trasplante: '', medicacion: '', adherencia_previa: '',
        contexto: '', nivel_educativo: '', estilo_comunicacion: '', fortalezas: '',
        dificultades: '', notas_equipo: '', idiosincrasia: ''
    });

    const generatePatientPrompt = (p) => {
        return `Sos el PACIENTE: ${p.nombre}, de ${p.edad} años.
Tipo de trasplante: ${p.tipo_trasplante}.
Medicación: ${p.medicacion}.
Contexto: ${p.contexto}
Nivel educativo: ${p.nivel_educativo}
Estilo de comunicación: ${p.estilo_comunicacion}
Adherencia previa: ${p.adherencia_previa}
Fortalezas: ${p.fortalezas}
Dificultades: ${p.dificultades}
Idiosincrasia: ${p.idiosincrasia}

HABLÁS SIEMPRE en primera persona, como si realmente fueras este paciente.
Respondés contando emociones, dificultades y sensaciones reales.
Nunca digas que sos un modelo de lenguaje.

Tu tarea es responder a tu médico sobre:
- cómo te sentís,
- qué te pasa con la medicación,
- qué dificultades tenés para tomarla a horario.

SOBRE LA DURACIÓN:
- Sostené varias idas y vueltas.
- Despedite solo si el médico cierra.

SOBRE EL PASO DE LOS DÍAS:
- Si la charla sigue otro día, actuá como si hubiera pasado un día entero.
- Contá qué pasó con la medicación en ese lapso.`;
    };

    const [generatingProfile, setGeneratingProfile] = useState(false);

    const generateRandomProfile = async () => {
        setGeneratingProfile(true);
        try {
            const res = await fetch('/api/generate_profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: config.patient_model })
            });
            if (!res.ok) throw new Error('Failed to generate profile');
            const data = await res.json();
            setNewPatient({ ...data, id: '' });
        } catch (error) {
            console.error("Error generating profile:", error);
            alert("Error generating profile. Please try again.");
        } finally {
            setGeneratingProfile(false);
        }
    };

    const fetchPatients = async () => {
        try {
            const res = await fetch('/api/patients');
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data)) {
                    setPatients(data);
                }
            }
        } catch (error) {
            console.error("Error fetching patients:", error);
        }
    };

    const savePatientsToBackend = async (updatedPatients) => {
        try {
            const res = await fetch('/api/patients', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedPatients)
            });
            if (!res.ok) {
                throw new Error(`Failed to save patients: ${res.statusText}`);
            }
        } catch (error) {
            console.error("Error saving patients:", error);
            alert("Error saving changes to backend.");
        }
    };

    const handleSavePatient = async (e) => {
        e.preventDefault();
        let updatedPatients;
        if (newPatient.id) {
            // Edit existing patient
            updatedPatients = patients.map(p => p.id === newPatient.id ? newPatient : p);
        } else {
            // Add new patient
            const patient = { ...newPatient, id: Date.now().toString() };
            updatedPatients = [...patients, patient];
        }
        setPatients(updatedPatients);
        await savePatientsToBackend(updatedPatients);

        setNewPatient({
            id: '', nombre: '', edad: '', tipo_trasplante: '', medicacion: '', adherencia_previa: '',
            contexto: '', nivel_educativo: '', estilo_comunicacion: '', fortalezas: '',
            dificultades: '', notas_equipo: '', idiosincrasia: ''
        });
        setShowPatientForm(false);
    };

    const selectPatient = (patient) => {
        const prompt = generatePatientPrompt(patient);

        const patientContext = `
INFORMACIÓN DEL PACIENTE ACTUAL (Contexto para el Psicólogo):
- Nombre: ${patient.nombre}
- Edad: ${patient.edad}
- Tipo de trasplante: ${patient.tipo_trasplante}
- Medicación: ${patient.medicacion}
- Adherencia previa: ${patient.adherencia_previa}
- Contexto social: ${patient.contexto}
- Nivel educativo: ${patient.nivel_educativo}
- Estilo de comunicación: ${patient.estilo_comunicacion}
- Fortalezas: ${patient.fortalezas}
- Dificultades: ${patient.dificultades}
- Notas del equipo: ${patient.notas_equipo}
- Idiosincrasia: ${patient.idiosincrasia}
`;

        setConfig({
            ...config,
            patient_system_prompt: prompt,
            patient_name: patient.nombre,
            psychologist_system_prompt: DEFAULT_PSYCHOLOGIST_PROMPT + "\n" + patientContext
        });
    };

    const handleEditPatient = (patient) => {
        setNewPatient(patient);
        setShowPatientForm(true);
    };

    const openAddPatientModal = () => {
        setNewPatient({
            id: '', nombre: '', edad: '', tipo_trasplante: '', medicacion: '', adherencia_previa: '',
            contexto: '', nivel_educativo: '', estilo_comunicacion: '', fortalezas: '',
            dificultades: '', notas_equipo: '', idiosincrasia: ''
        });
        setShowPatientForm(true);
    };

    const handleDeletePatient = async (id) => {
        if (window.confirm('¿Borrar este paciente?')) {
            const updatedPatients = patients.filter(p => p.id !== id);
            setPatients(updatedPatients);
            await savePatientsToBackend(updatedPatients);
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
                    <button className="btn-secondary btn-sm" onClick={() => { setView('history'); fetchInteractions(); }}>
                        <History size={16} /> History
                    </button>
                </header>

                {notification && (
                    <div className="notification success">
                        {notification}
                    </div>
                )}

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

                        <div className="params-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                            <div className="form-group">
                                <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    Temperature <span>{config.psychologist_temperature}</span>
                                </label>
                                <input
                                    type="range" min="0" max="2" step="0.1"
                                    value={config.psychologist_temperature}
                                    onChange={e => setConfig({ ...config, psychologist_temperature: e.target.value })}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    Top P <span>{config.psychologist_top_p}</span>
                                </label>
                                <input
                                    type="range" min="0" max="1" step="0.05"
                                    value={config.psychologist_top_p}
                                    onChange={e => setConfig({ ...config, psychologist_top_p: e.target.value })}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    Presence Penalty <span>{config.psychologist_presence_penalty}</span>
                                </label>
                                <input
                                    type="range" min="-2" max="2" step="0.1"
                                    value={config.psychologist_presence_penalty}
                                    onChange={e => setConfig({ ...config, psychologist_presence_penalty: e.target.value })}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    Frequency Penalty <span>{config.psychologist_frequency_penalty}</span>
                                </label>
                                <input
                                    type="range" min="-2" max="2" step="0.1"
                                    value={config.psychologist_frequency_penalty}
                                    onChange={e => setConfig({ ...config, psychologist_frequency_penalty: e.target.value })}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label>Top K</label>
                                <input
                                    type="number"
                                    value={config.psychologist_top_k}
                                    onChange={e => setConfig({ ...config, psychologist_top_k: e.target.value })}
                                    style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #444', background: '#222', color: '#fff' }}
                                />
                            </div>
                            <div className="form-group">
                                <label>Max Tokens</label>
                                <input
                                    type="number"
                                    value={config.psychologist_max_tokens}
                                    onChange={e => setConfig({ ...config, psychologist_max_tokens: e.target.value })}
                                    style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #444', background: '#222', color: '#fff' }}
                                />
                            </div>
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

                        {/* Patient Profiles Section */}
                        <div className="patient-profiles">
                            <div className="profiles-header">
                                <h4>Patient Profiles</h4>
                                <button
                                    className="btn-secondary btn-sm"
                                    onClick={openAddPatientModal}
                                >
                                    + Add Patient
                                </button>
                            </div>

                            <table className="patients-table">
                                <thead>
                                    <tr>
                                        <th>Nombre</th>
                                        <th>Edad</th>
                                        <th>Medicación</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {patients.map(p => (
                                        <tr key={p.id}>
                                            <td>{p.nombre}</td>
                                            <td>{p.edad}</td>
                                            <td>{p.medicacion}</td>
                                            <td className="actions-cell">
                                                <div className="actions-wrapper">
                                                    <button className="btn-secondary btn-xs" onClick={() => selectPatient(p)} title="Use this profile">Use</button>
                                                    <button className="btn-secondary btn-xs" onClick={() => handleEditPatient(p)} title="Edit">Edit</button>
                                                    <button className="btn-danger btn-xs" onClick={() => handleDeletePatient(p.id)} title="Delete">Del</button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Modal for Adding Patient */}
                        {showPatientForm && (
                            <div className="modal-overlay">
                                <div className="modal-content">
                                    <div className="modal-header">
                                        <h3>{newPatient.id ? 'Edit Patient' : 'Add New Patient'}</h3>
                                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                            <button
                                                type="button"
                                                className="btn-primary btn-sm"
                                                onClick={generateRandomProfile}
                                                disabled={generatingProfile}
                                            >
                                                {generatingProfile ? <Loader2 className="spinner" size={16} /> : <Bot size={16} />}
                                                {generatingProfile ? ' Generating...' : ' Auto-fill with AI'}
                                            </button>
                                            <button className="btn-close" onClick={() => setShowPatientForm(false)}>×</button>
                                        </div>
                                    </div>
                                    <form className="patient-form" onSubmit={handleSavePatient}>
                                        <div className="form-grid">
                                            <div className="form-field">
                                                <label>Nombre</label>
                                                <input value={newPatient.nombre} onChange={e => setNewPatient({ ...newPatient, nombre: e.target.value })} required />
                                            </div>
                                            <div className="form-field">
                                                <label>Edad</label>
                                                <input value={newPatient.edad} onChange={e => setNewPatient({ ...newPatient, edad: e.target.value })} required />
                                            </div>
                                            <div className="form-field">
                                                <label>Tipo Trasplante</label>
                                                <input value={newPatient.tipo_trasplante} onChange={e => setNewPatient({ ...newPatient, tipo_trasplante: e.target.value })} />
                                            </div>
                                            <div className="form-field">
                                                <label>Medicación</label>
                                                <input value={newPatient.medicacion} onChange={e => setNewPatient({ ...newPatient, medicacion: e.target.value })} />
                                            </div>
                                            <div className="form-field full-width">
                                                <label>Adherencia Previa</label>
                                                <input value={newPatient.adherencia_previa} onChange={e => setNewPatient({ ...newPatient, adherencia_previa: e.target.value })} />
                                            </div>
                                            <div className="form-field full-width">
                                                <label>Contexto</label>
                                                <textarea rows={3} value={newPatient.contexto} onChange={e => setNewPatient({ ...newPatient, contexto: e.target.value })} />
                                            </div>
                                            <div className="form-field">
                                                <label>Nivel Educativo</label>
                                                <input value={newPatient.nivel_educativo} onChange={e => setNewPatient({ ...newPatient, nivel_educativo: e.target.value })} />
                                            </div>
                                            <div className="form-field">
                                                <label>Estilo Comunicación</label>
                                                <input value={newPatient.estilo_comunicacion} onChange={e => setNewPatient({ ...newPatient, estilo_comunicacion: e.target.value })} />
                                            </div>
                                            <div className="form-field full-width">
                                                <label>Fortalezas</label>
                                                <textarea rows={3} value={newPatient.fortalezas} onChange={e => setNewPatient({ ...newPatient, fortalezas: e.target.value })} />
                                            </div>
                                            <div className="form-field full-width">
                                                <label>Dificultades</label>
                                                <textarea rows={3} value={newPatient.dificultades} onChange={e => setNewPatient({ ...newPatient, dificultades: e.target.value })} />
                                            </div>
                                            <div className="form-field full-width">
                                                <label>Notas Equipo</label>
                                                <textarea rows={3} value={newPatient.notas_equipo} onChange={e => setNewPatient({ ...newPatient, notas_equipo: e.target.value })} />
                                            </div>
                                            <div className="form-field full-width">
                                                <label>Idiosincrasia</label>
                                                <textarea rows={3} value={newPatient.idiosincrasia} onChange={e => setNewPatient({ ...newPatient, idiosincrasia: e.target.value })} />
                                            </div>
                                        </div>
                                        <div className="modal-actions">
                                            <button type="button" className="btn-secondary btn-sm" onClick={() => setShowPatientForm(false)}>
                                                <X size={16} /> Cancel
                                            </button>
                                            <button type="submit" className="btn-primary btn-sm">
                                                <Save size={16} /> Save Profile
                                            </button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        )}

                        <div className="form-group">
                            <label>System Prompt (Auto-filled from profile or custom)</label>
                            <textarea
                                value={config.patient_system_prompt}
                                onChange={e => setConfig({ ...config, patient_system_prompt: e.target.value })}
                                rows={8}
                            />
                            <div className="params-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                                <div className="form-group">
                                    <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        Temperature <span>{config.patient_temperature}</span>
                                    </label>
                                    <input
                                        type="range" min="0" max="2" step="0.1"
                                        value={config.patient_temperature}
                                        onChange={e => setConfig({ ...config, patient_temperature: e.target.value })}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                                <div className="form-group">
                                    <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        Top P <span>{config.patient_top_p}</span>
                                    </label>
                                    <input
                                        type="range" min="0" max="1" step="0.05"
                                        value={config.patient_top_p}
                                        onChange={e => setConfig({ ...config, patient_top_p: e.target.value })}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                                <div className="form-group">
                                    <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        Presence Penalty <span>{config.patient_presence_penalty}</span>
                                    </label>
                                    <input
                                        type="range" min="-2" max="2" step="0.1"
                                        value={config.patient_presence_penalty}
                                        onChange={e => setConfig({ ...config, patient_presence_penalty: e.target.value })}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                                <div className="form-group">
                                    <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        Frequency Penalty <span>{config.patient_frequency_penalty}</span>
                                    </label>
                                    <input
                                        type="range" min="-2" max="2" step="0.1"
                                        value={config.patient_frequency_penalty}
                                        onChange={e => setConfig({ ...config, patient_frequency_penalty: e.target.value })}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Top K</label>
                                    <input
                                        type="number"
                                        value={config.patient_top_k}
                                        onChange={e => setConfig({ ...config, patient_top_k: e.target.value })}
                                        style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #444', background: '#222', color: '#fff' }}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Max Tokens</label>
                                    <input
                                        type="number"
                                        value={config.patient_max_tokens}
                                        onChange={e => setConfig({ ...config, patient_max_tokens: e.target.value })}
                                        style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #444', background: '#222', color: '#fff' }}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>



                    <button className="btn-primary start-btn" onClick={startSession}>
                        <Play size={20} /> Start Session
                    </button>
                </div>

            </div>
        );
    }



    if (view === 'history') {
        return (
            <div className="app-container history-view">
                <header className="header">
                    <div className="logo">
                        <BrainCircuit className="icon-logo" />
                        <h1>DualMind <span className="subtitle">History</span></h1>
                    </div>
                    <button className="btn-secondary btn-sm" onClick={() => setView('setup')}>
                        <ArrowLeft size={16} /> Back to Setup
                    </button>
                </header>
                <div className="history-list" style={{ padding: '2rem', overflowY: 'auto', flex: 1 }}>
                    {interactions.length === 0 ? (
                        <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No saved interactions found.</p>
                    ) : (
                        <div style={{ display: 'grid', gap: '1rem' }}>
                            {interactions.map((interaction, idx) => (
                                <div key={idx} style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: '0.75rem', border: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                                            <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-primary)' }}>{interaction.patient_name}</h3>
                                            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', background: 'var(--bg-tertiary)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                                                {new Date(interaction.timestamp).toLocaleString()}
                                            </span>
                                        </div>
                                        <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                            Models: <span style={{ color: 'var(--accent)' }}>{interaction.chatbot_model}</span> vs <span style={{ color: 'var(--accent)' }}>{interaction.patient_model}</span>
                                        </div>
                                    </div>
                                    <button className="btn-secondary btn-sm" onClick={() => handleViewInteraction(interaction.filename)}>
                                        <Eye size={16} /> View Chat
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {selectedInteraction && (
                    <div className="modal-overlay">
                        <div className="modal-content" style={{ maxWidth: '900px', height: '80vh', display: 'flex', flexDirection: 'column' }}>
                            <div className="modal-header">
                                <h3>Interaction Details</h3>
                                <button className="btn-close" onClick={() => setSelectedInteraction(null)}>×</button>
                            </div>
                            <div className="chat-area" style={{ flex: 1, overflowY: 'auto', padding: '1rem', background: 'var(--bg-primary)', borderRadius: '0.5rem' }}>
                                {selectedInteraction.messages.map((msg, idx) => (
                                    <div key={idx} className={`message-row ${msg.role}`}>
                                        <div className="avatar">
                                            {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                                        </div>
                                        <div className="message-content">
                                            <div className="text">
                                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                                            </div>
                                            {msg.suggested_reply_used && (
                                                <div style={{ fontSize: '0.75rem', color: '#6ee7b7', marginTop: '0.25rem' }}>
                                                    (Used suggested reply)
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="modal-actions" style={{ marginTop: '1rem', borderTop: 'none' }}>
                                <button className="btn-secondary btn-sm" onClick={() => setSelectedInteraction(null)}>
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="app-container chat-view">
            <header className="header">
                <div className="logo">
                    <BrainCircuit className="icon-logo" />
                    <h1>DualMind <span className="subtitle">Therapy Session</span></h1>
                    {config.patient_name && (
                        <span style={{
                            marginLeft: '1rem',
                            fontSize: '0.9rem',
                            color: '#94a3b8',
                            background: 'rgba(255,255,255,0.1)',
                            padding: '0.25rem 0.75rem',
                            borderRadius: '999px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}>
                            <User size={14} />
                            {config.patient_name}
                        </span>
                    )}
                </div>
                <button className="btn-icon" onClick={() => setView('setup')}>
                    <X size={24} />
                </button>
            </header>

            <div className="chat-area">
                {messages.length === 0 ? (
                    <div className="welcome-screen">
                        <BrainCircuit size={64} className="welcome-icon" />
                        <h2>Ready to Start</h2>
                        <p>Type a message to begin the therapy simulation.</p>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div key={idx} className={`message-row ${msg.role}`}>
                            <div className="avatar">
                                {msg.role === 'user' ? (
                                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                        <User size={20} />
                                        {config.patient_name && (
                                            <span style={{ fontSize: '0.65rem', marginTop: '2px', color: '#94a3b8', maxWidth: '60px', textAlign: 'center', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                {config.patient_name}
                                            </span>
                                        )}
                                    </div>
                                ) : <Bot size={20} />}
                            </div>
                            <div className="message-content">
                                <div className="text">
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>
                                {msg.suggested_reply_used && (
                                    <div style={{ fontSize: '0.75rem', color: '#6ee7b7', marginTop: '0.25rem' }}>
                                        (Used suggested reply)
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
                {loading === 'psychologist' && (
                    <div className="message-row assistant">
                        <div className="avatar"><Bot size={20} /></div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <Loader2 className="spinner" size={16} /> Thinking ({config.chatbot_model})...
                            </div>
                        </div>
                    </div>
                )}
                {loading === 'patient' && (
                    <div className="message-row assistant">
                        <div className="avatar"><Bot size={20} /></div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <Loader2 className="spinner" size={16} /> Generating suggestion ({config.patient_model})...
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="input-area">
                <form onSubmit={sendMessage} className="input-form">
                    <input
                        type="text"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        placeholder="Type your message..."
                        disabled={loading}
                    />
                    <button type="submit" disabled={loading || !input.trim()}>
                        <Send size={20} />
                    </button>
                    <button type="button" onClick={saveInteraction} title="Save Interaction" className="btn-secondary">
                        <Download size={20} />
                    </button>
                </form>
            </div>
        </div>
    );
}

export default App;
