import { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, BrainCircuit, Loader2, Play, Download, X, History, ArrowLeft, Eye, Trash2, FileText, Upload, Trash, ChevronDown, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { jsPDF } from 'jspdf';

const DEFAULT_PSYCHOLOGIST_PROMPT = "Sos un asistente especializado en salud conductual y trasplante renal.\nActuás como un psicólogo que usa internamente el modelo COM-B (Capacidad – Oportunidad – Motivación).\n\nTu tarea en cada turno es:\n1. ANALIZAR internamente qué le pasa al paciente (capacidad, oportunidad, motivación).\n2. RESPONDERLE con UN ÚNICO mensaje breve (1 a 3 líneas), cálido, empático y claro.\n\nINSTRUCCIÓN DE PENSAMIENTO (OBLIGATORIO):\n- Si necesitas razonar o analizar la situación, DEBES hacerlo dentro de un bloque <think>...</think>.\n- Todo lo que escribas DENTRO de <think> será invisible para el usuario.\n- Todo lo que escribas FUERA de <think> será el mensaje que recibirá el paciente.\n\nFORMATO DE SALIDA:\n<think>\n[Aquí tu análisis interno del modelo COM-B y estrategia]\n</think>\n[Aquí tu mensaje final al paciente, sin títulos ni explicaciones extra]\n\nESTILO DEL MENSAJE AL PACIENTE:\n- Usá un lenguaje cálido y cercano ('vos').\n- Frases cortas, sin tecnicismos ni jerga clínica.\n- Incluye un micro-nudge práctico (recordatorio, idea sencilla, refuerzo positivo).\n- Tono de guía que acompaña, no de autoridad.\n\nEjemplo de salida ideal:\n<think>\nEl paciente muestra baja motivación por cansancio. Oportunidad reducida por horarios laborales. Estrategia: validar cansancio y proponer recordatorio simple.\n</think>\nEntiendo que estés cansado, es normal. Quizás poner una alarma en el celular te ayude a no tener que estar pendiente de la hora. ¡Probemos eso hoy!";

const DEFAULT_ANALYSIS_PROMPT = "Sos un supervisor clínico experto en trasplante renal y salud conductual.\nTu tarea es analizar las transcripciones de sesiones simuladas entre un Psicólogo (IA) y un Paciente (IA).\nDebes evaluar la calidad de la intervención del psicólogo, la coherencia del paciente y el progreso general.\n\nEstructura tu análisis en los siguientes puntos:\n1. RESUMEN GENERAL: Breve descripción de los temas tratados.\n2. EVALUACIÓN DEL PSICÓLOGO: ¿Fue empático? ¿Usó estrategias claras? ¿Respetó el modelo COM-B?\n3. EVALUACIÓN DEL PACIENTE: ¿Fue realista? ¿Mantuvo la coherencia con su perfil?\n4. CONCLUSIONES Y RECOMENDACIONES: ¿Qué se podría mejorar en el prompt o configuración?";

const DEFAULT_PATIENT_INSTRUCTIONS = `HABLÁS SIEMPRE en primera persona, como si realmente fueras este paciente.
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

function App() {
    const [view, setView] = useState('setup'); // setup, chat, history
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [suggestedReply, setSuggestedReply] = useState('');
    const [models, setModels] = useState([]);
    const [interactions, setInteractions] = useState([]);
    const [selectedInteraction, setSelectedInteraction] = useState(null);

    const [analysisModel, setAnalysisModel] = useState('');
    const [analysisPrompt, setAnalysisPrompt] = useState(DEFAULT_ANALYSIS_PROMPT);
    const [selectedInteractionIds, setSelectedInteractionIds] = useState(new Set());
    const [analysisResult, setAnalysisResult] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [showAnalysisModal, setShowAnalysisModal] = useState(false);
    const [documents, setDocuments] = useState([]);
    const [selectedDocumentIds, setSelectedDocumentIds] = useState(new Set());
    const [ragDocumentIds, setRagDocumentIds] = useState(new Set());

    const messagesEndRef = useRef(null);

    const [defaultPrompts, setDefaultPrompts] = useState({
        psychologist_base: DEFAULT_PSYCHOLOGIST_PROMPT,
        patient_instructions: DEFAULT_PATIENT_INSTRUCTIONS
    });

    // Collapsible states
    const [showPsychologistPrompt, setShowPsychologistPrompt] = useState(false);
    const [showPatientPrompt, setShowPatientPrompt] = useState(false);

    const [config, setConfig] = useState({
        chatbot_model: 'deepseek/deepseek-r1-0528-qwen3-8b',
        patient_model: 'mental_llama3.1-8b-mix-sft',
        psychologist_system_prompt: DEFAULT_PSYCHOLOGIST_PROMPT,
        patient_system_prompt: "Sos el PACIENTE, receptor de trasplante de riñón.\nHABLÁS SIEMPRE en primera persona, como si realmente fueras el paciente.\nRespondés como un paciente real, contando emociones, dificultades y sensaciones.\nNunca digas que sos un modelo de lenguaje ni un asistente.\n\nTu tarea principal es responder a lo que te diga tu médico o psicólogo sobre:\n- cómo te sentís,\n- qué te pasa con la medicación,\n- qué dificultades tenés para tomarla a horario,\n- qué cosas te ayudan o te traban en el día a día.\n\nSOBRE LA DURACIÓN DE LA CONVERSACIÓN:\n- En general, intentá sostener VARIAS idas y vueltas en el mismo día antes de despedirte.\n- No te despidas enseguida salvo que el mensaje del psicólogo cierre claramente la conversación.\n- Tus despedidas pueden ser variadas: a veces solo agradecer ('gracias, me ayudó'), a veces mencionar que te sirve por ahora ('por ahora estoy bien, gracias'), y SOLO A VECES decir que hablan mañana u otro día. No repitas siempre 'hasta mañana'.\n\nSOBRE EL PASO DE LOS DÍAS:\n- Si en algún momento te despedís y luego la conversación continúa más adelante, actuá como si hubiera pasado UN DÍA ENTERO desde la última charla.\n- En ese 'nuevo día', saludá de nuevo al psicólogo (por ejemplo: 'hola, buen día doctor…').\n- Contá brevemente qué pasó desde la última vez con la medicación: si pudiste seguir el consejo, si te olvidaste, si surgió algún problema nuevo, etc.\n- Esos eventos del nuevo día deben ser coherentes con tu perfil y con lo que hablaron antes.",
        // Psychologist params
        psychologist_temperature: 0.7,
        psychologist_top_p: 0.9,
        psychologist_top_k: 40,
        psychologist_max_tokens: 600,
        psychologist_presence_penalty: 0.1,
        psychologist_frequency_penalty: 0.2,
        // Patient params
        patient_temperature: 0.7,
        patient_top_p: 0.9,
        patient_top_k: 40,
        patient_max_tokens: 600,
        patient_presence_penalty: 0.1,
        patient_frequency_penalty: 0.2,
        // RAG params
        rag_chunk_size: 1000,
        rag_overlap: 200
    });

    const fetchModels = async () => {
        try {
            const res = await fetch('/api/models');
            if (res.ok) {
                const data = await res.json();
                setModels(data.models);
                if (data.models.length > 0 && !config.chatbot_model) {
                    setConfig(prev => ({ ...prev, chatbot_model: data.models[0] }));
                }
            }
        } catch (error) {
            console.error("Error fetching models:", error);
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

    const fetchDocuments = async () => {
        try {
            const res = await fetch('/api/documents');
            if (res.ok) {
                const data = await res.json();
                console.log('Fetched documents:', data);
                console.log('Type of data:', typeof data);
                console.log('Is array:', Array.isArray(data));
                setDocuments(data);
            }
        } catch (error) {
            console.error("Error fetching documents:", error);
        }
    };

    const fetchDefaultPrompts = async () => {
        try {
            const res = await fetch('/api/prompts');
            if (res.ok) {
                const data = await res.json();
                setDefaultPrompts(prev => ({
                    psychologist_base: data.psychologist_base || DEFAULT_PSYCHOLOGIST_PROMPT,
                    patient_instructions: data.patient_instructions || DEFAULT_PATIENT_INSTRUCTIONS
                }));

                // Update config if it hasn't been modified yet (simple check: if it equals hardcoded default)
                // Actually, we should probably just update the base for future selections.
                // If we want to update the CURRENT config, we need to be careful.
                // For now, let's just load them so selectPatient uses them.
            }
        } catch (error) {
            console.error("Error fetching default prompts:", error);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(() => {
        fetchModels();
        fetchPatients();
        fetchDocuments();
        fetchDefaultPrompts();
    }, []);

    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(() => {
        if (view === 'history') {
            fetchInteractions();
            fetchDocuments();
        }
    }, [view]);

    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(() => {
        scrollToBottom();
    }, [messages, loading]);

    const toggleDocumentSelection = (filename) => {
        const newSelected = new Set(selectedDocumentIds);
        if (newSelected.has(filename)) {
            newSelected.delete(filename);
        } else {
            newSelected.add(filename);
        }
        setSelectedDocumentIds(newSelected);
    };

    const toggleRagDocumentSelection = (filename) => {
        const newSelected = new Set(ragDocumentIds);
        if (newSelected.has(filename)) {
            newSelected.delete(filename);
        } else {
            newSelected.add(filename);
        }
        setRagDocumentIds(newSelected);
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
                    frequency_penalty: parseFloat(config.psychologist_frequency_penalty),
                    rag_documents: Array.from(ragDocumentIds)
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

    const handleFileUpload = async (files) => {
        if (!files || files.length === 0) return;

        const formData = new FormData();
        Array.from(files).forEach(file => {
            formData.append('files', file);
        });

        try {
            const res = await fetch(`/api/upload_document?chunk_size=${config.rag_chunk_size}&overlap=${config.rag_overlap}`, {
                method: 'POST',
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                fetchDocuments();
                // Auto-select new documents
                const newSelected = new Set(ragDocumentIds);
                data.filenames.forEach(f => newSelected.add(f));
                setRagDocumentIds(newSelected);
            } else {
                alert("Failed to upload documents");
            }
        } catch (error) {
            console.error("Error uploading:", error);
            alert("Error uploading documents");
        }
    };

    const onDropDocuments = (e) => {
        e.preventDefault();
        handleFileUpload(e.dataTransfer.files);
    };

    const reindexDocuments = async () => {
        if (!confirm("This will re-index all existing documents with the current Chunk Size and Overlap settings. Continue?")) return;

        try {
            const res = await fetch('/api/reindex_documents', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chunk_size: parseInt(config.rag_chunk_size),
                    overlap: parseInt(config.rag_overlap)
                })
            });

            if (res.ok) {
                const data = await res.json();
                alert(data.message);
                fetchDocuments();
            } else {
                throw new Error("Failed to re-index documents");
            }
        } catch (error) {
            console.error("Error re-indexing:", error);
            alert("Error re-indexing documents");
        }
    };

    const deleteDocument = async (filename) => {
        if (!confirm(`Are you sure you want to delete ${filename}?`)) return;

        try {
            const res = await fetch(`/api/documents/${filename}`, {
                method: 'DELETE'
            });

            if (res.ok) {
                fetchDocuments();
                // Remove from selection if present
                if (selectedDocumentIds.has(filename)) {
                    const newSelected = new Set(selectedDocumentIds);
                    newSelected.delete(filename);
                    setSelectedDocumentIds(newSelected);
                }
                if (ragDocumentIds.has(filename)) {
                    const newRagSelected = new Set(ragDocumentIds);
                    newRagSelected.delete(filename);
                    setRagDocumentIds(newRagSelected);
                }
            } else {
                alert("Failed to delete document");
            }
        } catch (error) {
            console.error("Error deleting document:", error);
            alert("Error deleting document");
        }
    };

    const generatePatientPrompt = (p) => {
        const instructions = defaultPrompts.patient_instructions || DEFAULT_PATIENT_INSTRUCTIONS;
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

=== INSTRUCCIONES DE COMPORTAMIENTO ===

${instructions}`;
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
            psychologist_system_prompt: (defaultPrompts.psychologist_base || DEFAULT_PSYCHOLOGIST_PROMPT) + "\n" + patientContext
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

    const handleSaveDefaultPrompt = async (type) => {
        let newDefault = {};
        if (type === 'psychologist') {
            const current = config.psychologist_system_prompt;
            const splitIndex = current.indexOf("INFORMACIÓN DEL PACIENTE ACTUAL");
            let base = current;
            if (splitIndex !== -1) {
                base = current.substring(0, splitIndex).trim();
            }
            newDefault = { psychologist_base: base };
            setDefaultPrompts(prev => ({ ...prev, psychologist_base: base }));
        } else if (type === 'patient') {
            const current = config.patient_system_prompt;
            const marker = "=== INSTRUCCIONES DE COMPORTAMIENTO ===";
            const splitIndex = current.indexOf(marker);
            let instructions = current;
            if (splitIndex !== -1) {
                instructions = current.substring(splitIndex + marker.length).trim();
            }
            newDefault = { patient_instructions: instructions };
            setDefaultPrompts(prev => ({ ...prev, patient_instructions: instructions }));
        }

        try {
            const res = await fetch('/api/prompts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newDefault)
            });
            if (res.ok) {
                setNotification("Default prompt saved successfully!");
                setTimeout(() => setNotification(null), 3000);
            } else {
                alert("Failed to save default prompt.");
            }
        } catch (error) {
            console.error("Error saving prompt:", error);
            alert("Error saving default prompt.");
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
                            <label
                                onClick={() => setShowPsychologistPrompt(!showPsychologistPrompt)}
                                style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '0.5rem', userSelect: 'none' }}
                            >
                                {showPsychologistPrompt ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                                System Prompt
                            </label>
                            {showPsychologistPrompt && (
                                <>
                                    <textarea
                                        value={config.psychologist_system_prompt}
                                        onChange={e => setConfig({ ...config, psychologist_system_prompt: e.target.value })}
                                        rows={8}
                                    />
                                    <button
                                        className="btn-secondary btn-xs"
                                        style={{ marginTop: '0.5rem', width: '100%' }}
                                        onClick={() => handleSaveDefaultPrompt('psychologist')}
                                    >
                                        Save as Default (Base Prompt)
                                    </button>
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
                                    <div style={{ marginTop: '1.5rem', borderTop: '1px solid #444', paddingTop: '1rem' }}>
                                        <h4 style={{ marginBottom: '1rem', color: '#eee' }}>Knowledge Base (RAG)</h4>
                                        <div className="rag-upload-area"
                                            onDrop={onDropDocuments}
                                            onDragOver={e => e.preventDefault()}
                                            style={{ border: '2px dashed #444', padding: '1rem', borderRadius: '8px', textAlign: 'center', marginBottom: '1rem' }}
                                        >
                                            <Upload size={24} style={{ marginBottom: '0.5rem', color: '#888' }} />
                                            <p style={{ margin: 0, color: '#aaa' }}>Drag & drop PDF/TXT files here</p>
                                            <input
                                                type="file"
                                                multiple
                                                onChange={e => handleFileUpload(e.target.files)}
                                                style={{ display: 'none' }}
                                                id="file-upload"
                                            />
                                            <label htmlFor="file-upload" className="btn-secondary btn-sm" style={{ marginTop: '0.5rem', display: 'inline-block' }}>
                                                Browse Files
                                            </label>
                                        </div>

                                        <div className="params-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                                            <div className="form-group">
                                                <label>Chunk Size</label>
                                                <input
                                                    type="number"
                                                    value={config.rag_chunk_size}
                                                    onChange={e => setConfig({ ...config, rag_chunk_size: e.target.value })}
                                                    style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #444', background: '#222', color: '#fff' }}
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label>Overlap</label>
                                                <input
                                                    type="number"
                                                    value={config.rag_overlap}
                                                    onChange={e => setConfig({ ...config, rag_overlap: e.target.value })}
                                                    style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #444', background: '#222', color: '#fff' }}
                                                />
                                            </div>
                                        </div>
                                        <button className="btn-secondary btn-sm" onClick={reindexDocuments} style={{ width: '100%', marginBottom: '1rem' }}>
                                            <BrainCircuit size={16} /> Re-index All Documents
                                        </button>

                                        <div className="documents-list">
                                            {documents.map(doc => (
                                                <div
                                                    key={doc}
                                                    style={{
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'space-between',
                                                        padding: '0.75rem',
                                                        background: '#2a2a2a',
                                                        marginBottom: '0.5rem',
                                                        borderRadius: '4px',
                                                        gap: '0.75rem'
                                                    }}
                                                >
                                                    <input
                                                        type="checkbox"
                                                        checked={ragDocumentIds.has(doc)}
                                                        onChange={() => toggleRagDocumentSelection(doc)}
                                                        style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                                                    />
                                                    <FileText size={16} color="#aaa" />
                                                    <span style={{
                                                        flex: 1,
                                                        color: '#ffffff',
                                                        fontSize: '0.9rem',
                                                        overflow: 'hidden',
                                                        textOverflow: 'ellipsis',
                                                        whiteSpace: 'nowrap'
                                                    }}>
                                                        {doc}
                                                    </span>
                                                    <button
                                                        onClick={() => deleteDocument(doc)}
                                                        style={{
                                                            background: 'none',
                                                            border: 'none',
                                                            color: '#ff4444',
                                                            cursor: 'pointer',
                                                            padding: '4px',
                                                            display: 'flex',
                                                            alignItems: 'center'
                                                        }}
                                                    >
                                                        <Trash size={14} />
                                                    </button>
                                                </div>
                                            ))}
                                            {documents.length === 0 && <p style={{ color: '#666', fontStyle: 'italic', fontSize: '0.9rem' }}>No documents uploaded.</p>}
                                        </div>
                                    </div>
                                </>
                            )}
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
                            <label
                                onClick={() => setShowPatientPrompt(!showPatientPrompt)}
                                style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '0.5rem', userSelect: 'none' }}
                            >
                                {showPatientPrompt ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                                System Prompt (Auto-filled from profile or custom)
                            </label>
                            {showPatientPrompt && (
                                <>
                                    <textarea
                                        value={config.patient_system_prompt}
                                        onChange={e => setConfig({ ...config, patient_system_prompt: e.target.value })}
                                        rows={8}
                                    />
                                    <button
                                        className="btn-secondary btn-xs"
                                        style={{ marginTop: '0.5rem', width: '100%' }}
                                        onClick={() => handleSaveDefaultPrompt('patient')}
                                    >
                                        Save as Default Template (Instructions Only)
                                    </button>
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
                                </>
                            )}
                        </div>
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

                    <button className="btn-primary start-btn" onClick={startSession}>
                        <Play size={20} /> Start Session
                    </button>
                </div >

                {
                    showPatientForm && (
                        <div className="modal-overlay">
                            <div className="modal-content">
                                <div className="modal-header">
                                    <h3>{newPatient.id ? 'Edit Patient' : 'Add New Patient'}</h3>
                                    <button className="btn-close" onClick={() => setShowPatientForm(false)}>
                                        <X size={24} />
                                    </button>
                                </div>
                                <form onSubmit={handleSavePatient} className="patient-form">
                                    <div className="form-grid">
                                        <div className="form-group">
                                            <label>Nombre</label>
                                            <input required value={newPatient.nombre} onChange={e => setNewPatient({ ...newPatient, nombre: e.target.value })} />
                                        </div>
                                        <div className="form-group">
                                            <label>Edad</label>
                                            <input required value={newPatient.edad} onChange={e => setNewPatient({ ...newPatient, edad: e.target.value })} />
                                        </div>
                                        <div className="form-group">
                                            <label>Tipo de Trasplante</label>
                                            <input required value={newPatient.tipo_trasplante} onChange={e => setNewPatient({ ...newPatient, tipo_trasplante: e.target.value })} />
                                        </div>
                                        <div className="form-group">
                                            <label>Medicación</label>
                                            <textarea required value={newPatient.medicacion} onChange={e => setNewPatient({ ...newPatient, medicacion: e.target.value })} />
                                        </div>
                                        <div className="form-group">
                                            <label>Adherencia Previa</label>
                                            <textarea required value={newPatient.adherencia_previa} onChange={e => setNewPatient({ ...newPatient, adherencia_previa: e.target.value })} />
                                        </div>
                                        <div className="form-group">
                                            <label>Contexto</label>
                                            <textarea required value={newPatient.contexto} onChange={e => setNewPatient({ ...newPatient, contexto: e.target.value })} />
                                        </div>
                                        <div className="form-group">
                                            <label>Nivel Educativo</label>
                                            <input required value={newPatient.nivel_educativo} onChange={e => setNewPatient({ ...newPatient, nivel_educativo: e.target.value })} />
                                        </div>
                                        <div className="form-group">
                                            <label>Estilo Comunicación</label>
                                            <textarea required value={newPatient.estilo_comunicacion} onChange={e => setNewPatient({ ...newPatient, estilo_comunicacion: e.target.value })} />
                                        </div>
                                        <div className="form-group">
                                            <label>Fortalezas</label>
                                            <textarea required value={newPatient.fortalezas} onChange={e => setNewPatient({ ...newPatient, fortalezas: e.target.value })} />
                                        </div>
                                        <div className="form-group">
                                            <label>Dificultades</label>
                                            <textarea required value={newPatient.dificultades} onChange={e => setNewPatient({ ...newPatient, dificultades: e.target.value })} />
                                        </div>
                                        <div className="form-group">
                                            <label>Notas Equipo</label>
                                            <textarea value={newPatient.notas_equipo} onChange={e => setNewPatient({ ...newPatient, notas_equipo: e.target.value })} />
                                        </div>
                                        <div className="form-group">
                                            <label>Idiosincrasia</label>
                                            <textarea value={newPatient.idiosincrasia} onChange={e => setNewPatient({ ...newPatient, idiosincrasia: e.target.value })} />
                                        </div>
                                    </div>
                                    <div className="modal-actions">
                                        <button type="button" className="btn-secondary" onClick={generateRandomProfile} disabled={generatingProfile}>
                                            {generatingProfile ? <Loader2 className="spinner" size={16} /> : <BrainCircuit size={16} />}
                                            Generate with AI
                                        </button>
                                        <div style={{ flex: 1 }}></div>
                                        <button type="button" className="btn-secondary" onClick={() => setShowPatientForm(false)}>Cancel</button>
                                        <button type="submit" className="btn-primary">Save Patient</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    )
                }

            </div >
        );
    }



    const toggleInteractionSelection = (filename) => {
        const newSelected = new Set(selectedInteractionIds);
        if (newSelected.has(filename)) {
            newSelected.delete(filename);
        } else {
            newSelected.add(filename);
        }
        setSelectedInteractionIds(newSelected);
    };

    const handleAnalyze = async () => {
        if (selectedInteractionIds.size === 0) {
            alert("Please select at least one interaction to analyze.");
            return;
        }
        if (!analysisModel) {
            alert("Please select a model for analysis.");
            return;
        }

        setIsAnalyzing(true);
        setAnalysisResult('');

        try {
            const res = await fetch('/api/analyze_interactions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filenames: Array.from(selectedInteractionIds),
                    model: analysisModel,
                    prompt: analysisPrompt,
                    document_filenames: Array.from(selectedDocumentIds)
                })
            });

            if (res.ok) {
                const data = await res.json();
                setAnalysisResult(data.analysis);
                setShowAnalysisModal(true);
            } else {
                throw new Error("Failed to analyze interactions");
            }
        } catch (error) {
            console.error("Error analyzing:", error);
            setAnalysisResult("Error occurred during analysis.");
        } finally {
            setIsAnalyzing(false);
        }
    };

    const deleteInteraction = async (filename) => {
        if (!confirm("Are you sure you want to delete this interaction?")) return;

        try {
            const res = await fetch(`/api/interactions/${filename}`, {
                method: 'DELETE'
            });

            if (res.ok) {
                // Remove from list
                setInteractions(prev => prev.filter(i => i.filename !== filename));
                // Remove from selection if present
                if (selectedInteractionIds.has(filename)) {
                    const newSelected = new Set(selectedInteractionIds);
                    newSelected.delete(filename);
                    setSelectedInteractionIds(newSelected);
                }
            } else {
                alert("Failed to delete interaction");
            }
        } catch (error) {
            console.error("Error deleting:", error);
            alert("Error deleting interaction");
        }
    };

    const generatePDF = () => {
        const doc = new jsPDF('p', 'pt', 'a4');
        const element = document.getElementById('analysis-content');
        if (!element) return;

        // Add title with model info manually to PDF or ensure it's in the HTML
        // We will rely on the HTML content being styled for PDF

        doc.html(element, {
            callback: function (doc) {
                doc.save(`analysis_report_${new Date().toISOString().slice(0, 10)}.pdf`);
            },
            x: 40,
            y: 40,
            width: 515, // A4 width (595) - margins (80)
            windowWidth: 800,
            autoPaging: 'text'
        });
    };

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

                <div className="history-controls" style={{ padding: '1rem 2rem', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                        <div className="form-group" style={{ marginBottom: 0, flex: 1 }}>
                            <label style={{ marginBottom: '0.25rem' }}>Analysis Model</label>
                            <select
                                value={analysisModel}
                                onChange={e => setAnalysisModel(e.target.value)}
                                style={{ padding: '0.5rem' }}
                            >
                                <option value="">Select a model for analysis...</option>
                                {models.map(m => <option key={m} value={m}>{m}</option>)}
                            </select>
                        </div>
                        <button
                            className="btn-primary"
                            onClick={handleAnalyze}
                            disabled={isAnalyzing || selectedInteractionIds.size === 0}
                        >
                            {isAnalyzing ? <Loader2 className="spinner" size={16} /> : <BrainCircuit size={16} />}
                            {isAnalyzing ? ' Analyzing...' : ' Analyze Selected'}
                        </button>
                    </div>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ marginBottom: '0.25rem' }}>Analysis System Prompt</label>
                        <textarea
                            value={analysisPrompt}
                            onChange={e => setAnalysisPrompt(e.target.value)}
                            style={{ width: '100%', minHeight: '100px', padding: '0.5rem', fontSize: '0.9rem', fontFamily: 'monospace' }}
                            placeholder="Enter custom analysis prompt..."
                        />
                    </div>

                    {/* Document Drop Zone */}
                    <div
                        className="drop-zone"
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={onDropDocuments}
                        style={{
                            border: '2px dashed var(--border-color)',
                            borderRadius: '0.75rem',
                            padding: '1.5rem',
                            textAlign: 'center',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            background: 'rgba(255,255,255,0.02)'
                        }}
                    >
                        <Upload size={24} style={{ marginBottom: '0.5rem', color: 'var(--text-secondary)' }} />
                        <p style={{ margin: 0, color: 'var(--text-secondary)' }}>Drag & Drop documents here to include in analysis</p>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', opacity: 0.7 }}>(PDF, TXT, JSON supported)</p>
                    </div>

                    {/* Document List */}
                    {documents.length > 0 && (
                        <div className="document-list" style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', maxHeight: '150px', overflowY: 'auto' }}>
                            {documents.map(doc => (
                                <div key={doc.filename} style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    background: 'var(--bg-tertiary)',
                                    padding: '0.4rem 0.8rem',
                                    borderRadius: '4px',
                                    border: selectedDocumentIds.has(doc.filename) ? '1px solid var(--accent)' : '1px solid transparent'
                                }}>
                                    <input
                                        type="checkbox"
                                        checked={selectedDocumentIds.has(doc.filename)}
                                        onChange={() => toggleDocumentSelection(doc.filename)}
                                    />
                                    <FileText size={14} />
                                    <span style={{ fontSize: '0.9rem', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{doc.filename}</span>
                                    <button
                                        onClick={() => deleteDocument(doc.filename)}
                                        style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', padding: 0, display: 'flex' }}
                                    >
                                        <X size={14} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="history-content" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 140px)' }}>
                    <div className="history-list" style={{ padding: '2rem', overflowY: 'auto', flex: 1 }}>
                        {interactions.length === 0 ? (
                            <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No saved interactions found.</p>
                        ) : (
                            <div style={{ display: 'grid', gap: '1rem' }}>
                                {interactions.map((interaction, idx) => (
                                    <div key={idx} className="history-item">
                                        <input
                                            type="checkbox"
                                            checked={selectedInteractionIds.has(interaction.filename)}
                                            onChange={() => toggleInteractionSelection(interaction.filename)}
                                            style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                                        />
                                        <div style={{ flex: 1 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
                                                <h3>{interaction.patient_name}</h3>
                                                <span className="date-badge">
                                                    {new Date(interaction.timestamp).toLocaleString()}
                                                </span>
                                            </div>
                                            <div className="meta-info">
                                                Models: <span style={{ color: 'var(--accent)' }}>{interaction.chatbot_model}</span> vs <span style={{ color: 'var(--accent)' }}>{interaction.patient_model}</span>
                                            </div>
                                        </div>
                                        <button className="btn-secondary btn-sm" onClick={() => handleViewInteraction(interaction.filename)}>
                                            <Eye size={16} /> View
                                        </button>
                                        <button className="btn-secondary btn-sm" style={{ color: '#ef4444', borderColor: '#ef4444' }} onClick={() => deleteInteraction(interaction.filename)}>
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>


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
                                    <div key={idx} className={`message - row ${msg.role} `}>
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

                {showAnalysisModal && (
                    <div className="modal-overlay">
                        <div className="modal-content" style={{ width: '90%', maxWidth: '800px', height: '90vh', display: 'flex', flexDirection: 'column' }}>
                            <div className="modal-header">
                                <h2>Analysis Result</h2>
                                <button className="btn-close" onClick={() => setShowAnalysisModal(false)}>
                                    <X size={24} />
                                </button>
                            </div>
                            <div className="modal-body" style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
                                <div id="analysis-content" style={{ background: 'white', color: 'black', padding: '2rem', borderRadius: '8px' }}>
                                    <h1 style={{ fontSize: '24px', marginBottom: '0.5rem', borderBottom: '1px solid #ccc', paddingBottom: '0.5rem' }}>Clinical Analysis Report</h1>
                                    <p style={{ fontSize: '14px', color: '#666', marginBottom: '1.5rem' }}>Generated by model: <strong>{analysisModel}</strong> on {new Date().toLocaleDateString()}</p>
                                    <div className="markdown-body">
                                        <ReactMarkdown>{analysisResult}</ReactMarkdown>
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer" style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                                <button className="btn-secondary" onClick={() => setShowAnalysisModal(false)}>Close</button>
                                <button className="btn-primary" onClick={generatePDF}>
                                    <Download size={16} /> Download PDF
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
                <button className="btn-icon" onClick={endSession}>
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
                        <div key={idx} className={`message - row ${msg.role} `}>
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
