import { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, BrainCircuit, Loader2, Play, Download, X, History, ArrowLeft, Eye, Trash2, FileText, Upload, Trash, ChevronDown, ChevronRight, MessageSquare } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

const DEFAULT_PSYCHOLOGIST_PROMPT = "Sos un asistente especializado en salud conductual y trasplante renal.\nActuás como un psicólogo que usa internamente el modelo COM-B (Capacidad – Oportunidad – Motivación).\n\nTu tarea en cada turno es:\n1. ANALIZAR internamente qué le pasa al paciente (capacidad, oportunidad, motivación).\n2. RESPONDERLE con UN ÚNICO mensaje breve (1 a 3 líneas), cálido, empático y claro.\n\nINSTRUCCIÓN DE PENSAMIENTO (OBLIGATORIO):\n- Si necesitas razonar o analizar la situación, DEBES hacerlo dentro de un bloque <think>...</think>.\n- Todo lo que escribas DENTRO de <think> será invisible para el usuario.\n- Todo lo que escribas FUERA de <think> será el mensaje que recibirá el paciente.\n\nFORMATO DE SALIDA:\n<think>\n[Aquí tu análisis interno del modelo COM-B y estrategia]\n</think>\n[Aquí tu mensaje final al paciente, sin títulos ni explicaciones extra]\n\nESTILO DEL MENSAJE AL PACIENTE:\n- Usá un lenguaje cálido y cercano ('vos').\n- Frases cortas, sin tecnicismos ni jerga clínica.\n- Incluye un micro-nudge práctico (recordatorio, idea sencilla, refuerzo positivo).\n- Tono de guía que acompaña, no de autoridad.\n\nEjemplo de salida ideal:\n<think>\nEl paciente muestra baja motivación por cansancio. Oportunidad reducida por horarios laborales. Estrategia: validar cansancio y proponer recordatorio simple.\n</think>\nEntiendo que estés cansado, es normal. Quizás poner una alarma en el celular te ayude a no tener que estar pendiente de la hora. ¡Probemos eso hoy!";

const DEFAULT_ANALYSIS_PROMPT = "Sos un supervisor clínico experto en trasplante renal y salud conductual.\nTu tarea es analizar las transcripciones de sesiones simuladas entre un Psicólogo (IA) y un Paciente (IA).\nDebes evaluar la calidad de la intervención del psicólogo, la coherencia del paciente y el progreso general.\n\nEstructura tu análisis en los siguientes puntos:\n1. RESUMEN GENERAL: Breve descripción de los temas tratados.\n2. EVALUACIÓN DEL PSICÓLOGO: ¿Fue empático? ¿Usó estrategias claras? ¿Respetó el modelo COM-B?\n3. EVALUACIÓN DEL PACIENTE: ¿Fue realista? ¿Mantuvo la coherencia con su perfil?\n4. CONCLUSIONES Y RECOMENDACIONES: ¿Qué se podría mejorar en el prompt o configuración?";

const DEFAULT_HISTORY_CHAT_PROMPT = "Sos un asistente experto que tiene acceso al historial de conversaciones de terapia simulada.\nTu objetivo es responder preguntas del usuario sobre estas conversaciones, buscando patrones, detalles específicos o resumiendo información.\nUsa el contexto proporcionado para fundamentar tus respuestas.";

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
    const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);

    const [analysisModel, setAnalysisModel] = useState('');
    const [analysisPrompt, setAnalysisPrompt] = useState(DEFAULT_ANALYSIS_PROMPT);
    const [historyChatPrompt, setHistoryChatPrompt] = useState(DEFAULT_HISTORY_CHAT_PROMPT);
    const [selectedInteractionIds, setSelectedInteractionIds] = useState(new Set());
    const [analysisResult, setAnalysisResult] = useState('');
    const [analysisMetadata, setAnalysisMetadata] = useState(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [generatingPatientId, setGeneratingPatientId] = useState(null); // Changed from boolean to ID
    const [showAnalysisModal, setShowAnalysisModal] = useState(false);
    const [pendingAutoChatPatient, setPendingAutoChatPatient] = useState(null); // State for confirmation modal
    const [analysisChatMessages, setAnalysisChatMessages] = useState([]);
    const [showAnalysisChat, setShowAnalysisChat] = useState(false);
    const [isAnalysisChatLoading, setIsAnalysisChatLoading] = useState(false);
    const [documents, setDocuments] = useState([]);
    const [selectedDocumentIds, setSelectedDocumentIds] = useState(new Set());
    const [ragDocumentIds, setRagDocumentIds] = useState(new Set());
    const [soloMode, setSoloMode] = useState(false);

    // Filter states
    const [filterPatientModel, setFilterPatientModel] = useState('');
    const [filterChatbotModel, setFilterChatbotModel] = useState('');
    const [filterPatientName, setFilterPatientName] = useState('');
    const [selectedPatientId, setSelectedPatientId] = useState(null);

    const messagesEndRef = useRef(null);

    const [defaultPrompts, setDefaultPrompts] = useState({
        psychologist_base: DEFAULT_PSYCHOLOGIST_PROMPT,
        patient_instructions: DEFAULT_PATIENT_INSTRUCTIONS
    });

    // Collapsible states
    const [showPsychologistPrompt, setShowPsychologistPrompt] = useState(false);
    const [showPatientPrompt, setShowPatientPrompt] = useState(false);
    const [showAnalysisPrompt, setShowAnalysisPrompt] = useState(false);
    const [showRagConfig, setShowRagConfig] = useState(false);

    const [config, setConfig] = useState({
        chatbot_model: 'deepseek/deepseek-r1-0528-qwen3-8b',
        patient_model: 'mental_llama3.1-8b-mix-sft',
        psychologist_system_prompt: DEFAULT_PSYCHOLOGIST_PROMPT,
        patient_system_prompt: "Sos el PACIENTE, receptor de trasplante de riñón.\nHABLÁS SIEMPRE en primera persona, como si realmente fueras el paciente.\nRespondés como un paciente real, contando emociones, dificultades y sensaciones.\nNunca digas que sos un modelo de lenguaje ni un asistente.\n\nTu tarea principal es responder a lo que te diga tu médico o psicólogo sobre:\n- cómo te sentís,\n- qué te pasa con la medicación,\n- qué dificultades tenés para tomarla a horario,\n- qué cosas te ayudan o te traban en el día a día.\n\nSOBRE LA DURACIÓN DE LA CONVERSACIÓN:\n- En general, intentá sostener VARIAS idas y vueltas en el mismo día antes de despedirte.\n- No te despidas enseguida salvo que el mensaje del psicólogo cierre claramente la conversación.\n- Tus despedidas pueden ser variadas: a veces solo agradecer ('gracias, me ayudó'), a veces mencionar que te sirve por ahora ('por ahora estoy bien, gracias'), y SOLO A VECES decir que hablan mañana u otro día. No repitas siempre 'hasta mañana'.\n\nSOBRE EL PASO DE LOS DÍAS:\n- Si en algún momento te despedís y luego la conversación continúa más adelante, actuá como si hubiera pasado UN DÍA ENTERO desde la última charla.\n- En ese 'nuevo día', saludá de nuevo al psicólogo (por ejemplo: 'hola, buen día doctor…').\n- Contá brevemente qué pasó desde la última vez con la medicación: si pudiste seguir el consejo, si te olvidaste, si surgió algún problema nuevo, etc.\n- Esos eventos del nuevo día deben ser coherentes con tu perfil y con lo que hablaron antes.",
        // Psychologist params
        psychologist_temperature: 0.7,
        psychologist_top_p: 0.9,
        psychologist_top_k: 40,
        psychologist_max_tokens: 150,
        psychologist_presence_penalty: 0.1,
        psychologist_frequency_penalty: 0.2,
        // Patient params
        patient_temperature: 0.7,
        patient_top_p: 0.9,
        patient_top_k: 40,
        patient_max_tokens: 150,
        patient_presence_penalty: 0.1,
        patient_frequency_penalty: 0.2,
        // RAG params
        rag_chunk_size: 1000,
        rag_overlap: 200,
        // Analysis params
        analysis_temperature: 0.7,
        analysis_top_p: 0.9,
        analysis_top_k: 40,
        analysis_max_tokens: 2000,
        analysis_presence_penalty: 0.1,
        analysis_frequency_penalty: 0.2,
        // History Chat params
        history_chat_temperature: 0.7,
        history_chat_top_p: 0.9,
        history_chat_top_k: 40,
        history_chat_max_tokens: 2000,
        history_chat_presence_penalty: 0.1,
        history_chat_frequency_penalty: 0.2
    });

    const fetchModels = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/models');
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
            const res = await fetch('http://localhost:8000/api/interactions');
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
            const res = await fetch('http://localhost:8000/api/documents');
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

    const handleReindex = async () => {
        if (!confirm("Esto borrará la base de datos y re-indexará todos los documentos con la configuración actual. ¿Continuar?")) return;

        try {
            const res = await fetch('http://localhost:8000/api/reindex_documents', {
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
            } else {
                alert("Error al re-indexar documentos.");
            }
        } catch (error) {
            console.error("Error re-indexing:", error);
            alert("Error re-indexando documentos.");
        }
    };

    const fetchDefaultPrompts = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/prompts');
            if (res.ok) {
                const data = await res.json();
                setDefaultPrompts(prev => ({
                    psychologist_base: data.psychologist_base || DEFAULT_PSYCHOLOGIST_PROMPT,
                    patient_instructions: data.patient_instructions || DEFAULT_PATIENT_INSTRUCTIONS
                }));
                if (data.analysis_prompt) setAnalysisPrompt(data.analysis_prompt);
                if (data.history_chat_prompt) setHistoryChatPrompt(data.history_chat_prompt);

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
            const res = await fetch(`http://localhost:8000/api/interactions/${filename}`);
            if (res.ok) {
                const data = await res.json();
                setSelectedInteraction(data);
            }
        } catch (error) {
            console.error("Error fetching interaction detail:", error);
        }
    };

    const startSession = () => {
        if (!soloMode && !config.patient_name) {
            alert("Por favor selecciona un perfil de paciente primero, o habilita el 'Modo Solitario' para chatear solo con el psicólogo.");
            return;
        }
        setView('chat');
        if (!soloMode && config.patient_name) {
            generateInitialSuggestion();
        }
    };

    const endSession = () => {
        if (window.confirm("¿Estás seguro de que quieres terminar esta sesión? El historial del chat se perderá.")) {
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
            const res = await fetch('http://localhost:8000/api/save_interaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(interactionData)
            });

            if (res.ok) {
                const data = await res.json();
                setMessages([]);
                setView('setup');
                setNotification(`Interacción guardada exitosamente como ${data.filename}`);
                setTimeout(() => setNotification(null), 10000);
            } else {
                throw new Error('Error al guardar la interacción');
            }
        } catch (error) {
            console.error("Error saving interaction:", error);
            alert("Error al guardar la interacción en el servidor.");
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
            const res = await fetch('http://localhost:8000/api/chat', {
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

            if (!res.ok) throw new Error('Error al obtener respuesta');
            const data = await res.json();

            const botMsg = { role: 'assistant', content: data.response };
            setMessages(prev => [...prev, botMsg]);

            // Step 2: Get Patient Suggestion
            if (!soloMode) {
                setLoading('patient');

                const suggestRes = await fetch('http://localhost:8000/api/suggest', {
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
            }

        } catch (error) {
            console.error("Error in chat flow:", error);
            setMessages(prev => [...prev, { role: 'assistant', content: "Error: No se pudo obtener respuesta del modelo." }]);
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

            const suggestRes = await fetch('http://localhost:8000/api/suggest', {
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
            const res = await fetch(`http://localhost:8000/api/upload_document?chunk_size=${config.rag_chunk_size}&overlap=${config.rag_overlap}`, {
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
                alert("Error al subir documentos");
            }
        } catch (error) {
            console.error("Error uploading:", error);
            alert("Error subiendo documentos");
        }
    };

    const onDropDocuments = (e) => {
        e.preventDefault();
        handleFileUpload(e.dataTransfer.files);
    };

    const reindexDocuments = async () => {
        if (!confirm("Esto re-indexará todos los documentos existentes con la configuración actual de Tamaño de Fragmento y Superposición. ¿Continuar?")) return;

        try {
            const res = await fetch('http://localhost:8000/api/reindex_documents', {
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
                throw new Error("Error al re-indexar documentos");
            }
        } catch (error) {
            console.error("Error re-indexing:", error);
            alert("Error re-indexando documentos");
        }
    };

    const deleteDocument = async (filename) => {
        if (!confirm(`¿Estás seguro de que quieres eliminar ${filename}?`)) return;

        try {
            const res = await fetch(`http://localhost:8000/api/documents/${filename}`, {
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
                alert("Error al eliminar documento");
            }
        } catch (error) {
            console.error("Error deleting document:", error);
            alert("Error eliminando documento");
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
    const [profileGenerationError, setProfileGenerationError] = useState(null);
    const [showProfileGuidanceModal, setShowProfileGuidanceModal] = useState(false);
    const [profileGuidance, setProfileGuidance] = useState('');

    const generateRandomProfile = async () => {
        setGeneratingProfile(true);
        setProfileGenerationError(null);
        setShowProfileGuidanceModal(false); // Close guidance modal
        try {
            const res = await fetch('http://localhost:8000/api/generate_profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: config.patient_model,
                    guidance: profileGuidance // Send user guidance
                })
            });
            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.detail || 'Error al generar perfil');
            }
            const data = await res.json();
            setNewPatient({ ...data, id: '' });
        } catch (error) {
            console.error("Error generating profile:", error);
            setProfileGenerationError(error.message);
        } finally {
            setGeneratingProfile(false);
        }
    };

    const fetchPatients = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/patients');
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
            const res = await fetch('http://localhost:8000/api/patients', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedPatients)
            });
            if (!res.ok) {
                throw new Error(`Error al guardar pacientes: ${res.statusText}`);
            }
        } catch (error) {
            console.error("Error saving patients:", error);
            alert("Error guardando cambios en el backend.");
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
        setSelectedPatientId(patient.id);
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

    useEffect(() => {
        console.log("STATE CHANGE: pendingAutoChatPatient is now:", pendingAutoChatPatient);
    }, [pendingAutoChatPatient]);

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

    const handleGenerateInteraction = async (patient) => {
        console.log("handleGenerateInteraction called for:", patient.nombre);
        if (!config.chatbot_model || !config.patient_model) {
            console.log("Missing models:", config);
            alert("Por favor selecciona ambos modelos, Psicólogo y Paciente, en la configuración primero.");
            return;
        }
        setPendingAutoChatPatient(patient);
    };

    const startAutoChat = async (patient) => {
        console.log("Starting auto chat for:", patient.nombre);
        setGeneratingPatientId(patient.id);
        try {
            // Generate prompt for this patient
            const patientSystemPrompt = generatePatientPrompt(patient);

            const res = await fetch('http://localhost:8000/api/generate_interaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    patient_profile: patient,
                    patient_system_prompt: patientSystemPrompt,
                    psychologist_system_prompt: config.psychologist_system_prompt,
                    chatbot_model: config.chatbot_model,
                    patient_model: config.patient_model,
                    turns: 2, // Reduced to 2 turns for maximum stability
                    psychologist_temperature: parseFloat(config.psychologist_temperature),
                    patient_temperature: parseFloat(config.patient_temperature)
                })
            });

            if (res.ok) {
                const data = await res.json();
                setNotification(`¡Interacción generada exitosamente! Guardada como ${data.filename}`);
                setTimeout(() => setNotification(null), 10000);
                // Refresh interactions list if we are in history view, or just fetch them now
                fetchInteractions();
            } else {
                const errorData = await res.json();
                throw new Error(errorData.detail || "Error al generar interacción");
            }
        } catch (error) {
            console.error("Error generating interaction:", error);
            alert(`Error generando interacción: ${error.message}`);
        } finally {
            setGeneratingPatientId(null);
        }
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
        } else if (type === 'analysis') {
            newDefault = { analysis_prompt: analysisPrompt };
        } else if (type === 'history_chat') {
            newDefault = { history_chat_prompt: historyChatPrompt };
        }

        try {
            const res = await fetch('http://localhost:8000/api/prompts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newDefault)
            });
            if (res.ok) {
                setNotification("¡Prompt predeterminado guardado exitosamente!");
                setTimeout(() => setNotification(null), 3000);
            } else {
                alert("Error al guardar prompt predeterminado.");
            }
        } catch (error) {
            console.error("Error saving prompt:", error);
            alert("Error guardando prompt predeterminado.");
        }
    };
    if (view === 'setup') {
        return (
            <div className="app-container setup-view">
                <header className="header">
                    <div className="logo">
                        <BrainCircuit className="icon-logo" />
                        <h1>NefroNudge <span className="subtitle">Configuración</span></h1>
                    </div>
                    <button className="btn-secondary btn-sm" onClick={() => { setView('history'); fetchInteractions(); }}>
                        <History size={16} /> Historial
                    </button>
                </header>


                {notification && (
                    <div className="notification success">
                        {notification}
                    </div>
                )}

                <div className="setup-panel">
                    <h2>Configuración de Sesión</h2>

                    <div className="config-section">
                        <h3>Psicólogo (Chatbot)</h3>
                        <div className="form-group">
                            <label>Modelo</label>
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
                                Prompt del Sistema
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
                                        Guardar como Predeterminado (Prompt Base)
                                    </button>
                                    <div className="params-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                                        <div className="form-group">
                                            <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                Temperatura <span>{config.psychologist_temperature}</span>
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
                                                Penalización de Presencia <span>{config.psychologist_presence_penalty}</span>
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
                                                Penalización de Frecuencia <span>{config.psychologist_frequency_penalty}</span>
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
                                            <label>Tokens Máximos</label>
                                            <input
                                                type="number"
                                                value={config.psychologist_max_tokens}
                                                onChange={e => setConfig({ ...config, psychologist_max_tokens: e.target.value })}
                                                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #444', background: '#222', color: '#fff' }}
                                            />
                                        </div>
                                    </div>
                                    <div style={{ marginTop: '1.5rem', borderTop: '1px solid #444', paddingTop: '1rem' }}>
                                        <h4 style={{ marginBottom: '1rem', color: '#eee' }}>Base de Conocimiento (RAG)</h4>
                                        <div className="rag-upload-area"
                                            onDrop={onDropDocuments}
                                            onDragOver={e => e.preventDefault()}
                                            style={{ border: '2px dashed #444', padding: '1rem', borderRadius: '8px', textAlign: 'center', marginBottom: '1rem' }}
                                        >
                                            <Upload size={24} style={{ marginBottom: '0.5rem', color: '#888' }} />
                                            <p style={{ margin: 0, color: '#aaa' }}>Arrastra y suelta archivos PDF/TXT aquí</p>
                                            <input
                                                type="file"
                                                multiple
                                                onChange={e => handleFileUpload(e.target.files)}
                                                style={{ display: 'none' }}
                                                id="file-upload"
                                            />
                                            <label htmlFor="file-upload" className="btn-secondary btn-sm" style={{ marginTop: '0.5rem', display: 'inline-block' }}>
                                                Explorar Archivos
                                            </label>
                                        </div>

                                        <div className="params-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                                            <div className="form-group">
                                                <label>Tamaño del Fragmento</label>
                                                <input
                                                    type="number"
                                                    value={config.rag_chunk_size}
                                                    onChange={e => setConfig({ ...config, rag_chunk_size: e.target.value })}
                                                    style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #444', background: '#222', color: '#fff' }}
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label>Superposición</label>
                                                <input
                                                    type="number"
                                                    value={config.rag_overlap}
                                                    onChange={e => setConfig({ ...config, rag_overlap: e.target.value })}
                                                    style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #444', background: '#222', color: '#fff' }}
                                                />
                                            </div>
                                        </div>
                                        <button className="btn-secondary btn-sm" onClick={reindexDocuments} style={{ width: '100%', marginBottom: '1rem' }}>
                                            <BrainCircuit size={16} /> Re-indexar Todos los Documentos
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
                                            {documents.length === 0 && <p style={{ color: '#666', fontStyle: 'italic', fontSize: '0.9rem' }}>No hay documentos subidos.</p>}
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem', padding: '0.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '0.5rem', userSelect: 'none', width: '100%' }}>
                            <input
                                type="checkbox"
                                checked={soloMode}
                                onChange={(e) => setSoloMode(e.target.checked)}
                                style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                            />
                            <span style={{ fontSize: '1rem', fontWeight: '500' }}>Modo Solitario (Solo Psicólogo)</span>
                        </label>
                    </div>

                    <div className="config-section" style={{ display: soloMode ? 'none' : 'block' }}>
                        <h3>Ayudante del Paciente (Motor de Sugerencias)</h3>
                        <div className="form-group">
                            <label>Modelo</label>
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
                                Prompt del Sistema (Autocompletado desde perfil o personalizado)
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
                                        Guardar como Plantilla Predeterminada (Solo Instrucciones)
                                    </button>
                                    <div className="params-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                                        <div className="form-group">
                                            <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                Temperatura <span>{config.patient_temperature}</span>
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
                                                Penalización de Presencia <span>{config.patient_presence_penalty}</span>
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
                                                Penalización de Frecuencia <span>{config.patient_frequency_penalty}</span>
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
                                            <label>Tokens Máximos</label>
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
                    <div className="patient-profiles" style={{ display: soloMode ? 'none' : 'block' }}>
                        <div className="profiles-header">
                            <h4>Perfiles de Pacientes</h4>
                            <button
                                className="btn-secondary btn-sm"
                                onClick={openAddPatientModal}
                                disabled={generatingPatientId !== null || generatingProfile}
                            >
                                + Agregar Paciente
                            </button>
                        </div>

                        <table className="patients-table">
                            <thead>
                                <tr>
                                    <th>Nombre</th>
                                    <th>Edad</th>
                                    <th>Medicación</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {patients.map(p => (
                                    <tr key={p.id} className={selectedPatientId === p.id ? 'selected-patient' : ''}>
                                        <td>{p.nombre}</td>
                                        <td>{p.edad}</td>
                                        <td>{p.medicacion}</td>
                                        <td className="actions-cell">
                                            <div className="actions-wrapper">
                                                <button
                                                    className="btn-secondary btn-xs"
                                                    onClick={() => selectPatient(p)}
                                                    title="Usar este perfil"
                                                    disabled={generatingPatientId !== null || generatingProfile}
                                                >
                                                    Usar
                                                </button>
                                                <button
                                                    className="btn-secondary btn-xs"
                                                    onClick={() => handleEditPatient(p)}
                                                    title="Editar"
                                                    disabled={generatingPatientId !== null || generatingProfile}
                                                >
                                                    Editar
                                                </button>
                                                <button
                                                    className="btn-primary btn-xs"
                                                    onClick={() => { console.log("Clicked Auto Chat for", p.nombre); handleGenerateInteraction(p); }}
                                                    title="Auto Chat"
                                                    style={{ backgroundColor: '#4caf50', borderColor: '#4caf50', opacity: (generatingPatientId !== null && generatingPatientId !== p.id) ? 0.5 : 1 }}
                                                    disabled={generatingPatientId !== null || generatingProfile}
                                                >
                                                    {generatingPatientId === p.id ? <Loader2 size={12} className="spinner" /> : <Bot size={12} />}
                                                </button>
                                                <button
                                                    className="btn-danger btn-xs"
                                                    onClick={() => handleDeletePatient(p.id)}
                                                    title="Eliminar"
                                                    disabled={generatingPatientId !== null || generatingProfile}
                                                >
                                                    Del
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>


                    <button className="btn-primary start-btn" onClick={startSession} disabled={generatingPatientId !== null || generatingProfile}>
                        <Play size={20} /> Iniciar Sesión
                    </button>
                </div >

                {
                    showPatientForm && (
                        <div className="modal-overlay">
                            <div className="modal-content">
                                <div className="modal-header">
                                    <h3>{newPatient.id ? 'Editar Paciente' : 'Agregar Nuevo Paciente'}</h3>
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
                                        <button type="button" className="btn-secondary" onClick={() => { setProfileGuidance(''); setShowProfileGuidanceModal(true); }} disabled={generatingProfile}>
                                            {generatingProfile ? <Loader2 className="spinner" size={16} /> : <BrainCircuit size={16} />}
                                            Generar con IA
                                        </button>
                                        <div style={{ flex: 1 }}></div>
                                        <button type="button" className="btn-secondary" onClick={() => setShowPatientForm(false)} disabled={generatingProfile}>Cancelar</button>
                                        <button type="submit" className="btn-primary" disabled={generatingProfile}>Guardar Paciente</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    )
                }

                {/* Error Modal for Profile Generation */}
                {profileGenerationError && (
                    <div className="modal-overlay">
                        <div className="modal-content" style={{ maxWidth: '400px', border: '1px solid #ff4444' }}>
                            <div className="modal-header">
                                <h3 style={{ color: '#ff4444' }}>Error Generando Perfil</h3>
                                <button className="btn-close" onClick={() => setProfileGenerationError(null)}>
                                    <X size={24} />
                                </button>
                            </div>
                            <div style={{ padding: '1.5rem 0', color: '#ccc' }}>
                                {profileGenerationError}
                            </div>
                            <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end' }}>
                                <button
                                    className="btn-secondary"
                                    onClick={() => setProfileGenerationError(null)}
                                >
                                    Cerrar
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Profile Guidance Modal */}
                {showProfileGuidanceModal && (
                    <div className="modal-overlay">
                        <div className="modal-content" style={{ maxWidth: '500px' }}>
                            <div className="modal-header">
                                <h3>Guía de Perfil IA</h3>
                                <button className="btn-close" onClick={() => setShowProfileGuidanceModal(false)}>
                                    <X size={24} />
                                </button>
                            </div>
                            <div style={{ padding: '1rem 0' }}>
                                <p style={{ color: '#ccc', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                                    Proporciona instrucciones opcionales para guiar a la IA en la creación del perfil del paciente (ej: "Una mujer mayor con diabetes", "Un estudiante joven que rechaza la medicación").
                                    Deja vacío para un perfil completamente aleatorio.
                                </p>
                                <textarea
                                    value={profileGuidance}
                                    onChange={e => setProfileGuidance(e.target.value)}
                                    placeholder="Ingresa la guía aquí..."
                                    rows={4}
                                    style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #444', background: '#222', color: '#fff' }}
                                />
                            </div>
                            <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                                <button
                                    className="btn-secondary"
                                    onClick={() => setShowProfileGuidanceModal(false)}
                                    disabled={generatingProfile}
                                >
                                    Cancelar
                                </button>
                                <button
                                    className="btn-primary"
                                    onClick={generateRandomProfile}
                                    disabled={generatingProfile}
                                >
                                    <BrainCircuit size={16} style={{ marginRight: '0.5rem' }} />
                                    Generar Perfil
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Auto Chat Modal */}
                {pendingAutoChatPatient && (
                    <div className="modal-overlay">
                        <div className="modal-content" style={{ maxWidth: '400px' }}>
                            <div className="modal-header">
                                <h3>Iniciar Auto Chat</h3>
                                <button className="btn-close" onClick={() => setPendingAutoChatPatient(null)}>
                                    <X size={24} />
                                </button>
                            </div>
                            <div style={{ padding: '1.5rem 0', color: '#ccc' }}>
                                ¿Iniciar generación autónoma de chat para {pendingAutoChatPatient.nombre}? Esto puede tardar un poco.
                            </div>
                            <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                                <button
                                    className="btn-secondary"
                                    onClick={() => setPendingAutoChatPatient(null)}
                                >
                                    Cancelar
                                </button>
                                <button
                                    className="btn-primary"
                                    onClick={() => {
                                        console.log("Modal Accept clicked");
                                        startAutoChat(pendingAutoChatPatient);
                                        setPendingAutoChatPatient(null);
                                    }}
                                >
                                    Aceptar
                                </button>
                            </div>
                        </div>
                    </div>
                )}
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

    const handleStartAnalysisChat = () => {
        if (selectedInteractionIds.size === 0) {
            alert("Por favor selecciona al menos una interacción para analizar.");
            return;
        }
        if (!analysisModel) {
            alert("Por favor selecciona un modelo para análisis.");
            return;
        }
        setAnalysisChatMessages([]);
        setShowAnalysisChat(true);
    };

    const handleSendAnalysisMessage = async (message) => {
        if (!message.trim()) return;

        const newMessages = [...analysisChatMessages, { role: 'user', content: message }];
        setAnalysisChatMessages(newMessages);
        setIsAnalysisChatLoading(true);

        try {
            const res = await fetch('http://localhost:8000/api/analysis_chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    history: analysisChatMessages,
                    interaction_filenames: Array.from(selectedInteractionIds),
                    document_filenames: Array.from(selectedDocumentIds),
                    model: analysisModel,
                    system_prompt: historyChatPrompt || DEFAULT_HISTORY_CHAT_PROMPT,
                    temperature: parseFloat(config.history_chat_temperature),
                    top_p: parseFloat(config.history_chat_top_p),
                    top_k: parseInt(config.history_chat_top_k),
                    max_tokens: parseInt(config.history_chat_max_tokens),
                    presence_penalty: parseFloat(config.history_chat_presence_penalty),
                    frequency_penalty: parseFloat(config.history_chat_frequency_penalty)
                })
            });

            if (res.ok) {
                const data = await res.json();
                setAnalysisChatMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
            } else {
                console.error("Failed to send analysis message");
                setAnalysisChatMessages(prev => [...prev, { role: 'assistant', content: "Error: Falló la obtención de respuesta." }]);
            }
        } catch (error) {
            console.error("Error in analysis chat:", error);
            setAnalysisChatMessages(prev => [...prev, { role: 'assistant', content: "Error: Error de red." }]);
        } finally {
            setIsAnalysisChatLoading(false);
        }
    };

    const handleAnalyze = async () => {
        if (selectedInteractionIds.size === 0) {
            alert("Por favor selecciona al menos una interacción para analizar.");
            return;
        }
        if (!analysisModel) {
            alert("Por favor selecciona un modelo para análisis.");
            return;
        }

        setIsAnalyzing(true);
        setAnalysisResult('');

        try {
            const res = await fetch('http://localhost:8000/api/analyze_interactions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filenames: Array.from(selectedInteractionIds),
                    model: analysisModel,
                    prompt: analysisPrompt,
                    document_filenames: Array.from(selectedDocumentIds),
                    temperature: parseFloat(config.analysis_temperature),
                    top_p: parseFloat(config.analysis_top_p),
                    top_k: parseInt(config.analysis_top_k),
                    max_tokens: parseInt(config.analysis_max_tokens),
                    presence_penalty: parseFloat(config.analysis_presence_penalty),
                    frequency_penalty: parseFloat(config.analysis_frequency_penalty)
                })
            });

            if (res.ok) {
                const data = await res.json();
                setAnalysisResult(data.analysis);
                setAnalysisMetadata(data.metadata);
                setShowAnalysisModal(true);
            } else {
                throw new Error("Error al analizar interacciones");
            }
        } catch (error) {
            console.error("Error analyzing:", error);
            setAnalysisResult("Error ocurrido durante el análisis.");
        } finally {
            setIsAnalyzing(false);
        }
    };

    const deleteInteraction = async (filename) => {
        if (!confirm("¿Estás seguro de que quieres eliminar esta interacción?")) return;

        try {
            const res = await fetch(`http://localhost:8000/api/interactions/${filename}`, {
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
                alert("Error al eliminar interacción");
            }
        } catch (error) {
            console.error("Error deleting:", error);
            alert("Error eliminando interacción");
        }
    };

    const generatePDF = async () => {
        const element = document.getElementById('analysis-content');
        if (!element) {
            console.error("¡Elemento de contenido de análisis no encontrado!");
            alert("Error: No se pudo encontrar contenido para generar PDF.");
            return;
        }

        setIsGeneratingPDF(true);
    };

    if (view === 'history') {
        return (
            <div className="app-container history-view">
                <header className="header">
                    <div className="logo">
                        <BrainCircuit className="icon-logo" />
                        <h1>NefroNudge <span className="subtitle">Historial</span></h1>
                    </div>
                    <button className="btn-secondary btn-sm" onClick={() => setView('setup')}>
                        <ArrowLeft size={16} /> Volver a Configuración
                    </button>
                </header>

                <div className="history-controls" style={{ padding: '1rem 2rem', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                        <div className="form-group" style={{ marginBottom: 0, flex: 1 }}>
                            <label style={{ marginBottom: '0.25rem' }}>Modelo de Análisis</label>
                            <select
                                value={analysisModel}
                                onChange={e => setAnalysisModel(e.target.value)}
                                style={{ padding: '0.5rem' }}
                            >
                                <option value="">Selecciona un modelo para análisis...</option>
                                {models.map(m => <option key={m} value={m}>{m}</option>)}
                            </select>
                        </div>
                        <button
                            className="btn-primary"
                            onClick={handleAnalyze}
                            disabled={isAnalyzing || selectedInteractionIds.size === 0}
                        >
                            {isAnalyzing ? <Loader2 className="spinner" size={16} /> : <BrainCircuit size={16} />}
                            {isAnalyzing ? ' Analizando...' : ' Analizar Seleccionados'}
                        </button>
                        <button
                            className="btn-secondary"
                            onClick={handleStartAnalysisChat}
                            disabled={selectedInteractionIds.size === 0}
                            style={{ marginLeft: '0.5rem' }}
                        >
                            <MessageSquare size={16} /> Chatear con Historial
                        </button>
                    </div>
                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                        <label
                            onClick={() => setShowAnalysisPrompt(!showAnalysisPrompt)}
                            style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '0.5rem', userSelect: 'none', marginBottom: '0.25rem' }}
                        >
                            {showAnalysisPrompt ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                            Prompts del Sistema y Configuración RAG
                        </label>
                        {showAnalysisPrompt && (
                            <>
                                <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '0.5rem', marginBottom: '1rem' }}>
                                    <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid #444', paddingBottom: '1rem' }}>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#aaa' }}>Configuración del Informe de Análisis</label>
                                        <textarea
                                            value={analysisPrompt}
                                            onChange={e => setAnalysisPrompt(e.target.value)}
                                            style={{ width: '100%', minHeight: '100px', padding: '0.5rem', fontSize: '0.9rem', fontFamily: 'monospace', marginBottom: '0.5rem' }}
                                            placeholder="Ingresa prompt de análisis personalizado..."
                                        />
                                        <button
                                            className="btn-secondary btn-xs"
                                            onClick={() => handleSaveDefaultPrompt('analysis')}
                                        >
                                            Guardar como Predeterminado
                                        </button>

                                        <div className="params-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                                            <div className="form-group">
                                                <label style={{ display: 'flex', justifyContent: 'space-between' }}>Temp <span>{config.analysis_temperature}</span></label>
                                                <input type="range" min="0" max="2" step="0.1" value={config.analysis_temperature} onChange={e => setConfig({ ...config, analysis_temperature: e.target.value })} style={{ width: '100%' }} />
                                            </div>
                                            <div className="form-group">
                                                <label style={{ display: 'flex', justifyContent: 'space-between' }}>Top P <span>{config.analysis_top_p}</span></label>
                                                <input type="range" min="0" max="1" step="0.05" value={config.analysis_top_p} onChange={e => setConfig({ ...config, analysis_top_p: e.target.value })} style={{ width: '100%' }} />
                                            </div>
                                            <div className="form-group">
                                                <label>Max Tokens</label>
                                                <input type="number" value={config.analysis_max_tokens} onChange={e => setConfig({ ...config, analysis_max_tokens: e.target.value })} style={{ width: '100%', padding: '0.25rem', background: '#222', border: '1px solid #444', color: '#fff' }} />
                                            </div>
                                        </div>
                                    </div>

                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#aaa' }}>Configuración del Chat de Historial</label>
                                        <textarea
                                            value={historyChatPrompt}
                                            onChange={e => setHistoryChatPrompt(e.target.value)}
                                            style={{ width: '100%', minHeight: '100px', padding: '0.5rem', fontSize: '0.9rem', fontFamily: 'monospace', marginBottom: '0.5rem' }}
                                            placeholder="Ingresa prompt de chat de historial personalizado..."
                                        />
                                        <button
                                            className="btn-secondary btn-xs"
                                            onClick={() => handleSaveDefaultPrompt('history_chat')}
                                        >
                                            Guardar como Predeterminado
                                        </button>

                                        <div className="params-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                                            <div className="form-group">
                                                <label style={{ display: 'flex', justifyContent: 'space-between' }}>Temp <span>{config.history_chat_temperature}</span></label>
                                                <input type="range" min="0" max="2" step="0.1" value={config.history_chat_temperature} onChange={e => setConfig({ ...config, history_chat_temperature: e.target.value })} style={{ width: '100%' }} />
                                            </div>
                                            <div className="form-group">
                                                <label style={{ display: 'flex', justifyContent: 'space-between' }}>Top P <span>{config.history_chat_top_p}</span></label>
                                                <input type="range" min="0" max="1" step="0.05" value={config.history_chat_top_p} onChange={e => setConfig({ ...config, history_chat_top_p: e.target.value })} style={{ width: '100%' }} />
                                            </div>
                                            <div className="form-group">
                                                <label>Max Tokens</label>
                                                <input type="number" value={config.history_chat_max_tokens} onChange={e => setConfig({ ...config, history_chat_max_tokens: e.target.value })} style={{ width: '100%', padding: '0.25rem', background: '#222', border: '1px solid #444', color: '#fff' }} />
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* RAG Configuration */}
                                <div className="rag-config" style={{ padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '0.5rem' }}>
                                    <h4
                                        onClick={() => setShowRagConfig(!showRagConfig)}
                                        style={{ marginTop: 0, marginBottom: showRagConfig ? '0.5rem' : 0, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                                    >
                                        {showRagConfig ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                                        Configuración RAG
                                    </h4>
                                    {showRagConfig && (
                                        <>
                                            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                                                <div style={{ flex: 1 }}>
                                                    <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.25rem' }}>Tamaño del Fragmento</label>
                                                    <input
                                                        type="number"
                                                        value={config.rag_chunk_size}
                                                        onChange={e => setConfig({ ...config, rag_chunk_size: parseInt(e.target.value) })}
                                                        style={{ width: '100%', padding: '0.5rem', borderRadius: '0.25rem', border: '1px solid var(--border-color)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
                                                    />
                                                </div>
                                                <div style={{ flex: 1 }}>
                                                    <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.25rem' }}>Superposición</label>
                                                    <input
                                                        type="number"
                                                        value={config.rag_overlap}
                                                        onChange={e => setConfig({ ...config, rag_overlap: parseInt(e.target.value) })}
                                                        style={{ width: '100%', padding: '0.5rem', borderRadius: '0.25rem', border: '1px solid var(--border-color)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
                                                    />
                                                </div>
                                            </div>
                                            <button
                                                className="btn-secondary"
                                                onClick={handleReindex}
                                                style={{ width: '100%', justifyContent: 'center', marginBottom: '1rem' }}
                                            >
                                                <BrainCircuit size={16} /> Re-indexar Todos los Documentos
                                            </button>

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
                                                    background: 'rgba(255,255,255,0.02)',
                                                    marginBottom: '1rem'
                                                }}
                                            >
                                                <Upload size={24} style={{ marginBottom: '0.5rem', color: 'var(--text-secondary)' }} />
                                                <p style={{ margin: 0, color: 'var(--text-secondary)' }}>Arrastra y suelta documentos aquí para incluir en el análisis</p>
                                                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', opacity: 0.7 }}>(PDF, TXT, JSON soportados)</p>
                                            </div>

                                            {/* Document List */}
                                            {documents.length > 0 && (
                                                <div className="document-list" style={{ marginTop: '1rem', maxHeight: '300px', overflowY: 'auto' }}>
                                                    {documents.map(doc => (
                                                        <div key={doc} style={{
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'space-between',
                                                            padding: '0.75rem',
                                                            background: '#2a2a2a',
                                                            marginBottom: '0.5rem',
                                                            borderRadius: '4px',
                                                            gap: '0.75rem',
                                                            border: selectedDocumentIds.has(doc) ? '1px solid var(--accent)' : '1px solid transparent'
                                                        }}>
                                                            <input
                                                                type="checkbox"
                                                                checked={selectedDocumentIds.has(doc)}
                                                                onChange={() => toggleDocumentSelection(doc)}
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
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                </div>

                <div className="history-content" style={{ display: 'flex', flexDirection: 'column' }}>
                    {/* Filters */}
                    <div className="filters-bar" style={{
                        padding: '1rem 2rem',
                        display: 'flex',
                        gap: '1rem',
                        borderBottom: '1px solid var(--border-color)',
                        background: 'rgba(255,255,255,0.02)',
                        flexWrap: 'wrap',
                        alignItems: 'center'
                    }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                            <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Nombre del Paciente</label>
                            <select
                                value={filterPatientName}
                                onChange={e => setFilterPatientName(e.target.value)}
                                className="filter-select"
                                style={{ padding: '0.5rem', borderRadius: '4px', background: '#222', color: '#fff', border: '1px solid #444', minWidth: '150px' }}
                            >
                                <option value="">Todos los Pacientes</option>
                                {[...new Set(interactions.map(i => i.patient_name))].filter(Boolean).sort().map(name => (
                                    <option key={name} value={name}>{name}</option>
                                ))}
                            </select>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                            <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Modelo Psicólogo</label>
                            <select
                                value={filterChatbotModel}
                                onChange={e => setFilterChatbotModel(e.target.value)}
                                className="filter-select"
                                style={{ padding: '0.5rem', borderRadius: '4px', background: '#222', color: '#fff', border: '1px solid #444', minWidth: '150px' }}
                            >
                                <option value="">Todos los Modelos</option>
                                {[...new Set(interactions.map(i => i.chatbot_model))].filter(Boolean).sort().map(model => (
                                    <option key={model} value={model}>{model}</option>
                                ))}
                            </select>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                            <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Modelo Paciente</label>
                            <select
                                value={filterPatientModel}
                                onChange={e => setFilterPatientModel(e.target.value)}
                                className="filter-select"
                                style={{ padding: '0.5rem', borderRadius: '4px', background: '#222', color: '#fff', border: '1px solid #444', minWidth: '150px' }}
                            >
                                <option value="">Todos los Modelos</option>
                                {[...new Set(interactions.map(i => i.patient_model))].filter(Boolean).sort().map(model => (
                                    <option key={model} value={model}>{model}</option>
                                ))}
                            </select>
                        </div>

                        {(filterPatientName || filterChatbotModel || filterPatientModel) && (
                            <button
                                onClick={() => {
                                    setFilterPatientName('');
                                    setFilterChatbotModel('');
                                    setFilterPatientModel('');
                                }}
                                style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.9rem', marginTop: '1rem' }}
                            >
                                <X size={16} style={{ verticalAlign: 'middle', marginRight: '4px' }} /> Limpiar Filtros
                            </button>
                        )}
                    </div>

                    <div className="history-list" style={{ padding: '2rem' }}>
                        {interactions
                            .filter(i => !filterPatientName || i.patient_name === filterPatientName)
                            .filter(i => !filterChatbotModel || i.chatbot_model === filterChatbotModel)
                            .filter(i => !filterPatientModel || i.patient_model === filterPatientModel)
                            .length === 0 ? (
                            <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No se encontraron interacciones que coincidan con los filtros.</p>
                        ) : (
                            <div style={{ display: 'grid', gap: '1rem' }}>
                                {interactions
                                    .filter(i => !filterPatientName || i.patient_name === filterPatientName)
                                    .filter(i => !filterChatbotModel || i.chatbot_model === filterChatbotModel)
                                    .filter(i => !filterPatientModel || i.patient_model === filterPatientModel)
                                    .map((interaction, idx) => (
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
                                                <Eye size={16} /> Ver
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
                                <h3>Detalles de Interacción</h3>
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
                                                    (Respuesta sugerida usada)
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="modal-actions" style={{ marginTop: '1rem', borderTop: 'none' }}>
                                <button className="btn-secondary btn-sm" onClick={() => setSelectedInteraction(null)}>
                                    Cerrar
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {showAnalysisModal && (
                    <div className="modal-overlay">
                        <div className="modal-content" style={{ width: '90%', maxWidth: '800px', height: '90vh', display: 'flex', flexDirection: 'column' }}>
                            <div className="modal-header">
                                <h2>Resultado del Análisis</h2>
                                <button className="btn-close" onClick={() => setShowAnalysisModal(false)}>
                                    <X size={24} />
                                </button>
                            </div>
                            <div className="modal-body" style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
                                <div id="analysis-content" style={{ background: 'white', color: 'black', padding: '2rem', borderRadius: '8px' }}>
                                    <h1 style={{ fontSize: '24px', marginBottom: '0.5rem', borderBottom: '1px solid #ccc', paddingBottom: '0.5rem' }}>Informe de Análisis Clínico</h1>
                                    <p style={{ fontSize: '14px', color: '#666', marginBottom: '1.5rem' }}>Generado por modelo: <strong>{analysisModel}</strong> el {new Date().toLocaleDateString()}</p>

                                    {analysisMetadata && (
                                        <div style={{ marginBottom: '2rem', padding: '1rem', background: '#f8f9fa', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                                            <h2 style={{ fontSize: '18px', marginBottom: '1rem', color: '#2d3748' }}>Información</h2>

                                            <div style={{ marginBottom: '1rem' }}>
                                                <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568', marginBottom: '0.5rem' }}>Modelo(s) de Paciente Usado(s):</h3>
                                                <ul style={{ listStyle: 'disc', paddingLeft: '1.5rem', margin: 0 }}>
                                                    {analysisMetadata.patient_models.map((model, idx) => (
                                                        <li key={idx} style={{ fontSize: '14px', color: '#2d3748' }}>{model}</li>
                                                    ))}
                                                </ul>
                                            </div>

                                            <div>
                                                <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568', marginBottom: '0.5rem' }}>Perfil(es) de Paciente / Prompt(s) del Sistema:</h3>
                                                {analysisMetadata.patient_prompts.map((prompt, idx) => (
                                                    <div key={idx} style={{
                                                        fontSize: '13px',
                                                        color: '#4a5568',
                                                        background: '#fff',
                                                        padding: '0.75rem',
                                                        borderRadius: '4px',
                                                        border: '1px solid #cbd5e0',
                                                        marginBottom: '0.5rem',
                                                        whiteSpace: 'pre-wrap'
                                                    }}>
                                                        {prompt}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    <div className="markdown-body">
                                        <ReactMarkdown>{analysisResult}</ReactMarkdown>
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer" style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                                <button className="btn-secondary" onClick={() => setShowAnalysisModal(false)}>Cerrar</button>
                                <button className="btn-primary" onClick={generatePDF} disabled={isGeneratingPDF}>
                                    {isGeneratingPDF ? <><Loader2 className="spinner" size={16} /> Generando PDF...</> : <><Download size={16} /> Descargar PDF</>}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {showAnalysisChat && (
                    <div className="modal-overlay">
                        <div className="modal-content" style={{ width: '90%', maxWidth: '1000px', height: '90vh', display: 'flex', flexDirection: 'column' }}>
                            <div className="modal-header">
                                <h3>Chat de Análisis ({analysisModel})</h3>
                                <button className="btn-close" onClick={() => setShowAnalysisChat(false)}>
                                    <X size={24} />
                                </button>
                            </div>
                            <div className="chat-area" style={{ flex: 1, overflowY: 'auto', padding: '1rem', background: 'var(--bg-primary)', borderRadius: '0.5rem' }}>
                                {analysisChatMessages.length === 0 ? (
                                    <div className="welcome-screen" style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', opacity: 0.5 }}>
                                        <MessageSquare size={48} />
                                        <p>Haz preguntas sobre las interacciones seleccionadas...</p>
                                    </div>
                                ) : (
                                    analysisChatMessages.map((msg, idx) => (
                                        <div key={idx} className={`message-row ${msg.role}`}>
                                            <div className="avatar">
                                                {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                                            </div>
                                            <div className="message-content">
                                                <div className="text">
                                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                                {isAnalysisChatLoading && (
                                    <div className="message-row assistant">
                                        <div className="avatar"><Bot size={20} /></div>
                                        <div className="message-content">
                                            <div className="typing-indicator">
                                                <Loader2 className="spinner" size={16} /> Pensando...
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div className="input-area" style={{ padding: '1rem', borderTop: '1px solid var(--border-color)' }}>
                                <form
                                    onSubmit={(e) => {
                                        e.preventDefault();
                                        const input = e.target.elements.messageInput;
                                        handleSendAnalysisMessage(input.value);
                                        input.value = '';
                                    }}
                                    style={{ display: 'flex', gap: '1rem' }}
                                >
                                    <input
                                        name="messageInput"
                                        type="text"
                                        placeholder="Escribe tu pregunta..."
                                        style={{ flex: 1, padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                                        autoComplete="off"
                                    />
                                    <button type="submit" className="btn-primary" disabled={isAnalysisChatLoading}>
                                        <Send size={20} />
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                )}

                {/* Auto Chat Modal */}
                {pendingAutoChatPatient && (
                    <div className="modal-overlay" style={{ border: '5px solid red', zIndex: 99999 }}>
                        <div className="modal-content" style={{ maxWidth: '400px' }}>
                            <div className="modal-header">
                                <h3>Iniciar Auto Chat</h3>
                                <button className="btn-close" onClick={() => setPendingAutoChatPatient(null)}>
                                    <X size={24} />
                                </button>
                            </div>
                            <div style={{ padding: '1.5rem 0', color: '#ccc' }}>
                                ¿Iniciar generación autónoma de chat para {pendingAutoChatPatient.nombre}? Esto puede tardar un poco.
                            </div>
                            <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                                <button
                                    className="btn-secondary"
                                    onClick={() => setPendingAutoChatPatient(null)}
                                >
                                    Cancelar
                                </button>
                                <button
                                    className="btn-primary"
                                    onClick={() => {
                                        console.log("Modal Accept clicked");
                                        startAutoChat(pendingAutoChatPatient);
                                        setPendingAutoChatPatient(null);
                                    }}
                                >
                                    Aceptar
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
                    <h1>NefroNudge <span className="subtitle">Sesión de Terapia</span></h1>
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
                        <h2>Listo para Comenzar</h2>
                        <p>Escribe un mensaje para comenzar la simulación de terapia.</p>
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
                                        (Respuesta sugerida usada)
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
                                <Loader2 className="spinner" size={16} /> Pensando ({config.chatbot_model})...
                            </div>
                        </div>
                    </div>
                )}
                {loading === 'patient' && (
                    <div className="message-row assistant">
                        <div className="avatar"><Bot size={20} /></div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <Loader2 className="spinner" size={16} /> Generando sugerencia ({config.patient_model})...
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
                        placeholder="Escribe tu mensaje..."
                        disabled={loading}
                    />
                    <button type="submit" disabled={loading || !input.trim()}>
                        <Send size={20} />
                    </button>
                    <button type="button" onClick={saveInteraction} title="Guardar Interacción" className="btn-secondary">
                        <Download size={20} />
                    </button>
                </form>
            </div>
        </div>
    );
}

export default App;
