import requests
import json
import re
import os

# Configuration defaults (can be overridden)
DEFAULT_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_MODEL_CHATBOT = "deepseek/deepseek-r1-0528-qwen3-8b" # Psychologist
DEFAULT_MODEL_PATIENT = "mental_llama3.1-8b-mix-sft" # Patient Helper

class DualLLMOrchestrator:
    def __init__(self, api_url=None):
        self.api_url = api_url or os.getenv("LLM_API_URL", DEFAULT_API_URL)

    def _call_llm(self, model, messages, temperature=0.7, max_tokens=2000, top_p=0.9, top_k=40, presence_penalty=0.1, frequency_penalty=0.2):
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "top_k": top_k,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty
            }
            # Increased timeout to allow for model loading
            response = requests.post(self.api_url, json=payload, timeout=1200)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            error_msg = str(e)
            if 'response' in locals() and response is not None:
                try:
                    error_detail = response.json()
                    if 'error' in error_detail:
                        error_msg += f" Details: {json.dumps(error_detail['error'])}"
                    else:
                        error_msg += f" Response: {response.text}"
                except:
                    error_msg += f" Response: {response.text}"
            
            print(f"Error calling LLM {model}: {error_msg}")
            return f"[Error: {error_msg}]"

    def _clean_think_tags(self, text: str) -> str:
        """Removes thinking blocks and other model artifacts to extract the final response."""
        
        # 1. Remove standard <think> blocks (closed and unclosed)
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"<think>.*$", "", text, flags=re.DOTALL)
        
        # 2. Remove other common reasoning markers used by various models
        # e.g. <|thought|>, <reasoning>, etc.
        text = re.sub(r"<\|thought\|>.*?(<\|/thought\|>|$)", "", text, flags=re.DOTALL)
        text = re.sub(r"<reasoning>.*?(</reasoning>|$)", "", text, flags=re.DOTALL)
        
        # 3. Remove <|channel|>... tags (common in some fine-tunes)
        text = re.sub(r"<\|.*?\|>.*?(?=\b[A-ZÁÉÍÓÚÑ]|$)", "", text, flags=re.DOTALL) 
        text = re.sub(r"<\|.*?\|>", "", text)
        
        # 4. Remove specific artifacts like <｜begin of sentence｜>Human:
        text = re.sub(r"<｜.*?｜>Human:", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<｜.*?｜>", "", text)

        # 5. Handle models that output "Thought: ... Response: ..." pattern
        # If we find a clear "Response:" or "Answer:" marker, take everything after it.
        # This is a strong heuristic for models that don't use XML tags for thinking.
        split_match = re.split(r"(?:^|\n)(?:Response|Answer|Respuesta|Contestación):\s*", text, flags=re.IGNORECASE)
        if len(split_match) > 1:
            # Return the last part, which should be the actual response
            return split_match[-1].strip()

        # 6. Remove common reasoning preambles (heuristic fallback)
        if re.match(r"^(We are asked|Here is a suggestion|The user wants|So reply|Thinking Process:)", text, re.IGNORECASE):
            # Try to find the last quoted string
            quotes = re.findall(r'"([^"]*)"', text)
            if quotes:
                return quotes[-1].strip()
            
            # Or try to split by "So reply..." or similar markers
            split_match = re.split(r"(So reply|The response is|Answer):", text, flags=re.IGNORECASE)
            if len(split_match) > 1:
                return split_match[-1].strip()

        return text.strip()

    def get_patient_suggestion(self, patient_model, history, psychologist_message, system_prompt=None, temperature=0.7, top_p=0.9, top_k=40, max_tokens=600, presence_penalty=0.1, frequency_penalty=0.2):
        """
        Generates a suggested reply for the patient (user) based on the psychologist's message.
        """
        default_prompt = (
            "Sos el PACIENTE, receptor de trasplante de riñón.\n"
            "HABLÁS SIEMPRE en primera persona, como si realmente fueras el paciente.\n"
            "Respondés como un paciente real, contando emociones, dificultades y sensaciones.\n"
            "Nunca digas que sos un modelo de lenguaje ni un asistente.\n\n"
            "Tu tarea principal es responder a lo que te diga tu médico o psicólogo sobre:\n"
            "- cómo te sentís,\n"
            "- qué te pasa con la medicación,\n"
            "- qué dificultades tenés para tomarla a horario,\n"
            "- qué cosas te ayudan o te traban en el día a día.\n\n"
            "SOBRE LA DURACIÓN DE LA CONVERSACIÓN:\n"
            "- En general, intentá sostener VARIAS idas y vueltas en el mismo día antes de despedirte.\n"
            "- No te despidas enseguida salvo que el mensaje del psicólogo cierre claramente la conversación.\n"
            "- Tus despedidas pueden ser variadas: a veces solo agradecer ('gracias, me ayudó'), "
            "a veces mencionar que te sirve por ahora ('por ahora estoy bien, gracias'), y SOLO A VECES "
            "decir que hablan mañana u otro día. No repitas siempre 'hasta mañana'.\n\n"
            "SOBRE EL PASO DE LOS DÍAS:\n"
            "- Si en algún momento te despedís y luego la conversación continúa más adelante, "
            "actuá como si hubiera pasado UN DÍA ENTERO desde la última charla.\n"
            "- En ese 'nuevo día', saludá de nuevo al psicólogo (por ejemplo: 'hola, buen día doctor…').\n"
            "- Contá brevemente qué pasó desde la última vez con la medicación: si pudiste seguir el consejo, "
            "si te olvidaste, si surgió algún problema nuevo, etc.\n"
            "- Esos eventos del nuevo día deben ser coherentes con tu perfil y con lo que hablaron antes."
        )
        
        actual_prompt = system_prompt if system_prompt else default_prompt

        messages = [{"role": "system", "content": actual_prompt}]
        
        # Add recent history (limit to last 6 messages to avoid context overflow)
        recent_history = history[-6:] if len(history) > 6 else history
        
        for msg in recent_history:
            if msg['role'] == 'user':
                # This was said by the Patient (us)
                messages.append({"role": "assistant", "content": msg['content']})
            elif msg['role'] == 'assistant':
                # This was said by the Psychologist (them)
                messages.append({"role": "user", "content": msg['content']})
        
        # Add the psychologist's latest message as the latest input from the 'user' (interlocutor)
        messages.append({"role": "user", "content": psychologist_message})

        print(f"--- Calling Patient Helper ({patient_model}) ---")
        print(f"System Prompt: {actual_prompt[:100]}...")

        return self._call_llm(
            patient_model, 
            messages, 
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty
        )

    def chat_psychologist(self, chatbot_model, history, user_message, psychologist_system_prompt=None, temperature=0.7, top_p=0.9, top_k=40, max_tokens=600, presence_penalty=0.1, frequency_penalty=0.2, context=None):
        """
        Step 1: Chatbot (Psychologist) responds.
        """
        default_psico_prompt = (
            "Sos un asistente especializado en salud conductual y trasplante renal.\n"
            "Actuás como un psicólogo que usa internamente el modelo COM-B (Capacidad – Oportunidad – Motivación).\n\n"
            "Tu tarea en cada turno es:\n"
            "1. ANALIZAR internamente qué le pasa al paciente (capacidad, oportunidad, motivación).\n"
            "2. RESPONDERLE con UN ÚNICO mensaje breve (1 a 3 líneas), cálido, empático y claro.\n\n"
            "INSTRUCCIÓN DE PENSAMIENTO (OBLIGATORIO):\n"
            "- Si necesitas razonar o analizar la situación, DEBES hacerlo dentro de un bloque <think>...</think>.\n"
            "- Todo lo que escribas DENTRO de <think> será invisible para el usuario.\n"
            "- Todo lo que escribas FUERA de <think> será el mensaje que recibirá el paciente.\n\n"
            "FORMATO DE SALIDA:\n"
            "<think>\n"
            "[Aquí tu análisis interno del modelo COM-B y estrategia]\n"
            "</think>\n"
            "[Aquí tu mensaje final al paciente, sin títulos ni explicaciones extra]\n\n"
            "ESTILO DEL MENSAJE AL PACIENTE:\n"
            "- Usá un lenguaje cálido y cercano ('vos').\n"
            "- Frases cortas, sin tecnicismos ni jerga clínica.\n"
            "- Incluye un micro-nudge práctico (recordatorio, idea sencilla, refuerzo positivo).\n"
            "- Tono de guía que acompaña, no de autoridad.\n\n"
            "Ejemplo de salida ideal:\n"
            "<think>\n"
            "El paciente muestra baja motivación por cansancio. Oportunidad reducida por horarios laborales. Estrategia: validar cansancio y proponer recordatorio simple.\n"
            "</think>\n"
            "Entiendo que estés cansado, es normal. Quizás poner una alarma en el celular te ayude a no tener que estar pendiente de la hora. ¡Probemos eso hoy!"
        )
        
        actual_psico_prompt = psychologist_system_prompt if psychologist_system_prompt else default_psico_prompt

        if context:
            actual_psico_prompt += f"\n\n{context}"

        messages = [
            {"role": "system", "content": actual_psico_prompt},
            *history,
            {"role": "user", "content": user_message}
        ]

        print(f"--- Calling Psychologist ({chatbot_model}) ---")
        print(f"System Prompt: {actual_psico_prompt[:100]}...")

        raw_response = self._call_llm(
            chatbot_model, 
            messages, 
            temperature=temperature, 
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty
        )
        
        return self._clean_think_tags(raw_response)

    def generate_suggestion_only(self, patient_model, history, user_message, psychologist_response, patient_system_prompt=None, temperature=0.7, top_p=0.9, top_k=40, max_tokens=600, presence_penalty=0.1, frequency_penalty=0.2):
        """
        Step 2: Patient Helper suggests next reply.
        """
        updated_history = history + [{"role": "user", "content": user_message}]
        
        suggested_reply = self._clean_think_tags(self.get_patient_suggestion(
            patient_model, 
            updated_history, 
            psychologist_response,
            system_prompt=patient_system_prompt,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty
        ))

        return suggested_reply

    def list_models(self):
        try:
            # LM Studio usually has a GET /v1/models endpoint
            url = self.api_url.replace("/chat/completions", "/models")
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                data = response.json()
                models = [m["id"] for m in data["data"]]
                if models:
                    return models
        except:
            pass
        return [DEFAULT_MODEL_CHATBOT, DEFAULT_MODEL_PATIENT]

    def generate_patient_profile(self, model):
        """
        Generates a random patient profile using the LLM.
        Returns a dictionary with the patient's details.
        """
        system_prompt = (
            "You are a helpful assistant that generates synthetic medical data. "
            "Output ONLY valid JSON. Do not include any explanations, markdown formatting, or conversational text."
        )
        
        user_prompt = (
            "Genera un perfil JSON de un paciente de trasplante renal.\n"
            "IMPORTANTE: Varía la edad (entre 18 y 80 años), el género y el contexto social.\n"
            "Asegúrate de que todas las características (contexto, estilo de comunicación, dificultades, etc.) "
            "sean COHERENTES con la edad y situación de vida elegida.\n\n"
            "Campos requeridos en el JSON:\n"
            "{\n"
            '  "nombre": "Nombre y Apellido (ficticio)",\n'
            '  "edad": "Número entero (ej: 25, 48, 72)",\n'
            '  "tipo_trasplante": "Renal (año del trasplante)",\n'
            '  "medicacion": "Lista realista de inmunosupresores y otros medicamentos",\n'
            '  "adherencia_previa": "Descripción de su historial de toma de medicación",\n'
            '  "contexto": "Situación laboral, familiar y social (coherente con la edad)",\n'
            '  "nivel_educativo": "Nivel de estudios alcanzado",\n'
            '  "estilo_comunicacion": "Cómo se expresa (formal, coloquial, breve, detallado, etc.)",\n'
            '  "fortalezas": "Recursos personales o sociales que ayudan a su tratamiento",\n'
            '  "dificultades": "Barreras específicas (cognitivas, económicas, emocionales, etc.)",\n'
            '  "notas_equipo": "Sugerencias clínicas para el abordaje",\n'
            '  "idiosincrasia": "Rasgos culturales o de personalidad específicos (ej: uruguayo, rural, urbano)"\n'
            "}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # Force use of the specific model if requested by user logic, or fallback to default
            target_model = model if model else DEFAULT_MODEL_PATIENT
            print(f"Generating profile with model: {target_model}")
            
            # Use a slightly lower temperature for more deterministic formatting
            response_text = self._call_llm(target_model, messages, temperature=0.8, max_tokens=1000)
            print(f"Raw profile response: {response_text[:200]}...") 
            
            # 1. Clean think tags
            response_text = self._clean_think_tags(response_text)
            
            # 2. Extract JSON using find/rfind (robust against pre/post text)
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end != -1:
                json_str = response_text[start:end]
                import json
                try:
                    data = json.loads(json_str)
                    # Ensure all values are strings
                    for key, value in data.items():
                        if isinstance(value, list):
                            data[key] = ", ".join(map(str, value))
                        elif isinstance(value, dict):
                            data[key] = json.dumps(value, ensure_ascii=False)
                        elif not isinstance(value, str):
                            data[key] = str(value)
                    return data
                except json.JSONDecodeError:
                    print("Extracted text was not valid JSON. Trying to fix common issues...")
                    try:
                        fixed_str = json_str.replace("'", '"')
                        data = json.loads(fixed_str)
                        for key, value in data.items():
                            if isinstance(value, list):
                                data[key] = ", ".join(map(str, value))
                            elif isinstance(value, dict):
                                data[key] = json.dumps(value, ensure_ascii=False)
                            elif not isinstance(value, str):
                                data[key] = str(value)
                        return data
                    except:
                        pass

            # 3. Fallback: try parsing the whole text
            import json
            data = json.loads(response_text)
            for key, value in data.items():
                if isinstance(value, list):
                    data[key] = ", ".join(map(str, value))
                elif isinstance(value, dict):
                    data[key] = json.dumps(value, ensure_ascii=False)
                elif not isinstance(value, str):
                    data[key] = str(value)
            return data

        except Exception as e:
            print(f"Error generating profile: {e}")
            return {
                "nombre": "Error al generar",
                "edad": "0",
                "tipo_trasplante": "Intente nuevamente",
                "medicacion": "Verifique la consola del servidor",
                "adherencia_previa": "-",
                "contexto": f"Error: {str(e)}",
                "nivel_educativo": "-",
                "estilo_comunicacion": "-",
                "fortalezas": "-",
                "dificultades": "-",
                "notas_equipo": "-",
                "idiosincrasia": "-"
            }

    def analyze_interactions(self, model, interactions_text, system_prompt=None):
        """
        Analyzes a set of interactions using the specified LLM.
        """
        if not system_prompt:
            system_prompt = (
                "Sos un supervisor clínico experto en trasplante renal y salud conductual.\n"
                "Tu tarea es analizar las transcripciones de sesiones simuladas entre un Psicólogo (IA) y un Paciente (IA).\n"
                "Debes evaluar la calidad de la intervención del psicólogo, la coherencia del paciente y el progreso general.\n\n"
                "Estructura tu análisis en los siguientes puntos:\n"
                "1. RESUMEN GENERAL: Breve descripción de los temas tratados.\n"
                "2. EVALUACIÓN DEL PSICÓLOGO: ¿Fue empático? ¿Usó estrategias claras? ¿Respetó el modelo COM-B?\n"
                "3. EVALUACIÓN DEL PACIENTE: ¿Fue realista? ¿Mantuvo la coherencia con su perfil?\n"
                "4. CONCLUSIONES Y RECOMENDACIONES: ¿Qué se podría mejorar en el prompt o configuración?"
            )
        
        # Truncate context if it's too long. 
        # User has a 4096 token limit (~16k chars). We'll limit input to ~12k chars to leave room for response.
        MAX_CHARS = 12000
        if len(interactions_text) > MAX_CHARS:
            print(f"Warning: Context too long ({len(interactions_text)} chars). Truncating to {MAX_CHARS} chars.")
            interactions_text = interactions_text[:MAX_CHARS] + "\n\n[...TRUNCATED DUE TO LENGTH...]"

        user_prompt = f"Aquí está el contexto para el análisis (transcripciones de interacciones y documentos de referencia si los hay):\n\n{interactions_text}\n\nPor favor, genera el análisis clínico."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        print(f"--- Analyzing Interactions with {model} ---")
        
        return self._clean_think_tags(self._call_llm(
            model,
            messages,
            temperature=0.7,
            max_tokens=2000
        ))

    def chat_analysis(self, model, history, system_prompt, context):
        """
        Chat with the analysis model, including context from interactions and RAG.
        """
        # Prepare messages
        # Check if placeholder exists
        if "{{CONTEXT}}" in system_prompt:
            full_system_prompt = system_prompt.replace("{{CONTEXT}}", f"\n=== CONTEXT FOR ANALYSIS ===\n{context}")
        else:
            # We inject the context into the system prompt at the end
            full_system_prompt = f"{system_prompt}\n\n=== CONTEXT FOR ANALYSIS ===\n{context}"
        
        messages = [{"role": "system", "content": full_system_prompt}]
        
        # Append history
        for msg in history:
            messages.append({"role": msg['role'], "content": msg['content']})
            
        print(f"--- Chat Analysis with {model} ---")
        return self._clean_think_tags(self._call_llm(
            model,
            messages,
            temperature=0.7,
            max_tokens=2000
        ))
