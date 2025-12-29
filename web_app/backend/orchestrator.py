import requests
import json
import re
import html
import os
import ast

# Configuration defaults (can be overridden)
DEFAULT_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_MODEL_CHATBOT = "mental_llama3.1-8b-mix-sft" # Psychologist
DEFAULT_MODEL_PATIENT = "openai/gpt-oss-20b" # Patient Helper

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
            raise Exception(f"LLM Call Failed: {error_msg}")

    def _extract_thought_and_response(self, text: str) -> dict:
        """
        Extracts thinking blocks and cleaning artifacts. 
        Returns a dict: {'thought': str|None, 'content': str}
        """
        if not text:
             return {"thought": None, "content": ""}
             
        text = html.unescape(text) # Handle encoded tags
        thought = None
        cleaned_text = text

        # 1. Try standard <think> blocks first (Most reliable, handling optional spaces)
        think_match = re.search(r"<\s*think\s*>(.*?)<\s*/\s*think\s*>", text, flags=re.DOTALL | re.IGNORECASE)
        if think_match:
            thought = think_match.group(1).strip()
            # Remove the think block from the text
            cleaned_text = re.sub(r"<\s*think\s*>.*?<\s*/\s*think\s*>", "", cleaned_text, flags=re.DOTALL | re.IGNORECASE)
        
        # 2. If no <think>, try <thought> blocks
        if not thought:
            thought_match = re.search(r"<thought>(.*?)</thought>", text, flags=re.DOTALL)
            if thought_match:
                thought = thought_match.group(1).strip()
                cleaned_text = re.sub(r"<thought>.*?</thought>", "", cleaned_text, flags=re.DOTALL)
                
            # 3. If still no thought, check for unclosed/malformed tags
            elif "<thought>" in text: # Unclosed <thought>
                parts = text.split("<thought>", 1)
                if len(parts) > 1:
                    thought = parts[1].strip()
                    cleaned_text = parts[0].strip()
            
            elif "<think>" in text: # Unclosed <think> (start only)
                parts = text.split("<think>", 1)
                if len(parts) > 1:
                    thought = parts[1].strip()
                    cleaned_text = parts[0].strip()
            
            elif "</think>" in text: # Unclosed </think> (end only, missing start)
                 split_match = re.split(r"</think>", text, flags=re.DOTALL, maxsplit=1)
                 if len(split_match) > 1:
                     thought = split_match[0].strip()
                     cleaned_text = split_match[1]

        # 4. Fallback: Check for "Thought:" headers if still no thought
        if not thought:
             # Look for "Thought:" or "Reasoning:" at the very beginning
             header_match = re.match(r"^(?:Thought|Reasoning|Pensamiento|Análisis):", cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
             if header_match:
                 # It starts with a header. We assume the thought goes until "Response:" or end of first paragraph/block
                 split_match = re.split(r"(?:^|\n)(?:Response|Answer|Respuesta|Contestación):", cleaned_text, flags=re.IGNORECASE)
                 if len(split_match) > 1:
                     thought = re.sub(r"^(?:Thought|Reasoning|Pensamiento|Análisis):\s*", "", split_match[0], flags=re.IGNORECASE | re.MULTILINE).strip()
                     cleaned_text = split_match[-1]
                 else:
                     # If no explicit "Response:", maybe it's just one block? checking for double newline separator
                     parts = re.split(r"\n\s*\n", cleaned_text, maxsplit=1)
                     if len(parts) > 1:
                         thought = re.sub(r"^(?:Thought|Reasoning|Pensamiento|Análisis):\s*", "", parts[0], flags=re.IGNORECASE | re.MULTILINE).strip()
                         cleaned_text = parts[1]

        # 5. Cleanup artifacts
        # Remove empty thinking artifacts left over
        cleaned_text = re.sub(r"<think>.*$", "", cleaned_text, flags=re.DOTALL)

        # Remove other common reasoning markers
        cleaned_text = re.sub(r"<\|thought\|>.*?(<\|/thought\|>|$)", "", cleaned_text, flags=re.DOTALL)
        cleaned_text = re.sub(r"<reasoning>.*?(</reasoning>|$)", "", cleaned_text, flags=re.DOTALL)
        
        # Remove <|channel|>... tags
        cleaned_text = re.sub(r"<\|.*?\|>.*?(?=\b[A-ZÁÉÍÓÚÑ]|$)", "", cleaned_text, flags=re.DOTALL) 
        cleaned_text = re.sub(r"<\|.*?\|>", "", cleaned_text)
        
        # Remove <｜begin of sentence｜>Human:
        cleaned_text = re.sub(r"<｜.*?｜>Human:", "", cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r"<｜.*?｜>", "", cleaned_text)

        # Final check: Is content empty but we have a thought?
        final_content = cleaned_text.strip()
        if not final_content and thought:
            # Heuristic: The model might have been cut off or put everything in thought
            final_content = "[El modelo generó un pensamiento interno pero no completó la respuesta externa.]"
            
        # FORCE DISPLAY: If no thought found, provide a placeholder so UI shows the box
        if not thought:
            thought = "[No se detectó razonamiento interno explícito en esta respuesta]"

        return {"thought": thought, "content": final_content}

    def _optimize_system_prompt(self, base_prompt, model_name):
        """
        Adapta el prompt del sistema con instrucciones técnicas específicas según el modelo detectado.
        Define explícitamente cómo separar 'Pensamiento' de 'Respuesta' según la arquitectura.
        """
        if not model_name:
            return base_prompt
            
        optimized_prompt = base_prompt
        model_name_lower = model_name.lower()

        # --- TIPO 1: MODELOS DE RAZONAMIENTO "DENSOS" (LLAMA / DEEPSEEK / MIX / QWEN) ---
        # Estos modelos están entrenados con tokens de formato XML explícito.
        if any(x in model_name_lower for x in ["llama", "mix", "deepseek", "qwen", "mental"]):
             specific_instructions = (
                 "\n\n=== PROTOCOLO DE PENSAMIENTO (ENGINE DE ALTO RAZONAMIENTO) ===\n"
                 "1. FORMATO OBLIGATORIO: Tu respuesta DEBE tener dos partes separadas exactamente así:\n"
                 "   <think>\n"
                 "   [Aquí escribes tu razonamiento interno, análisis COM-B, etc.]\n"
                 "   </think>\n"
                 "   [Aquí escribes tu respuesta final al usuario]\n"
                 "2. ANTI-ECO: No repitas el mensaje del usuario fuera de las etiquetas <think>.\n"
                 "3. ROL: Mantén el personaje clínico sin meta-comentarios."
             )
             optimized_prompt += specific_instructions
             
        # --- TIPO 2: MODELOS DE INSTRUCCIÓN GENERAL (GPT / OPENAI) ---
        # Estos modelos siguen mejor instrucciones de lenguaje natural estructurado ("Headers").
        elif "gpt" in model_name_lower:
             specific_instructions = (
                 "\n\n=== PROTOCOLO DE PENSAMIENTO (GPT ENGINE) ===\n"
                 "1. ESTRUCTURA DE RESPUESTA: Separa tu proceso mental de tu respuesta final usando estos encabezados exactos:\n"
                 "   Thought:\n"
                 "   [Tu análisis interno y estrategia aquí]\n\n"
                 "   Response:\n"
                 "   [Tu mensaje final para el paciente aquí]\n"
                 "2. NATURALIDAD: El contenido de 'Response' debe ser cálido y humano, no robótico."
             )
             optimized_prompt += specific_instructions
             
        # --- TIPO 3: MODELOS CONCISOS / OTROS (MISTRAL / GEMMA) ---
        # Prefieren XML simple pero instrucciones de brevedad.
        elif any(x in model_name_lower for x in ["mistral", "mixtral", "gemma"]):
             specific_instructions = (
                 "\n\n=== PROTOCOLO DE PENSAMIENTO (MISTRAL ENGINE) ===\n"
                 "1. FORMATO: Usa etiquetas XML para aislar tu pensamiento:\n"
                 "   <think> [Razonamiento breve] </think>\n"
                 "   [Respuesta final]\n"
                 "2. CONCISIÓN: Mantén el pensamiento directo y al grano."
             )
             optimized_prompt += specific_instructions
             
        # --- DEFAULT / GENÉRICO ---
        # Si no reconocemos el modelo, pedimos XML estándar por seguridad (compatible con el parser).
        else:
             specific_instructions = (
                 "\n\n=== INSTRUCCIONES DE FORMATO ===\n"
                 "Por favor, piensa antes de responder usando etiquetas <think>...</think> para tu análisis interno."
             )
             optimized_prompt += specific_instructions

        return optimized_prompt

    def get_patient_suggestion(self, patient_model, history, psychologist_message, system_prompt=None, temperature=0.7, top_p=0.9, top_k=40, max_tokens=600, presence_penalty=0.1, frequency_penalty=0.2):
        """
        Generates a suggested reply for the patient (user) based on the psychologist's message.
        """
        default_prompt = (
            "Sos el PACIENTE, receptor de trasplante de riñón.\n"
            "HABLÁS SIEMPRE en primera persona, como si realmente fueras el paciente.\n"
            "Respondés como un paciente real, contando emociones, dificultades y sensaciones.\n"
            "Nunca digas que sos un modelo de lenguaje ni un asistente.\n\n"
            "Tu tarea principal es responder a lo que te diga tu médico o asistente en salud renal sobre:\n"
            "- cómo te sentís,\n"
            "- qué te pasa con la medicación,\n"
            "- qué dificultades tenés para tomarla a horario,\n"
            "- qué cosas te ayudan o te traban en el día a día.\n\n"
            "SOBRE LA DURACIÓN DE LA CONVERSACIÓN:\n"
            "- En general, intentá sostener VARIAS idas y vueltas en el mismo día antes de despedirte.\n"
            "- No te despidas enseguida salvo que el mensaje del asistente en salud renal cierre claramente la conversación.\n"
            "- Tus despedidas pueden ser variadas: a veces solo agradecer ('gracias, me ayudó'), "
            "a veces mencionar que te sirve por ahora ('por ahora estoy bien, gracias'), y SOLO A VECES "
            "decir que hablan mañana u otro día. No repitas siempre 'hasta mañana'.\n\n"
            "SOBRE EL PASO DE LOS DÍAS:\n"
            "- Si en algún momento te despedís y luego la conversación continúa más adelante, "
            "actuá como si hubiera pasado UN DÍA ENTERO desde la última charla.\n"
            "- En ese 'nuevo día', saludá de nuevo al asistente en salud renal (por ejemplo: 'hola, buen día doctor…').\n"
            "- Contá brevemente qué pasó desde la última vez con la medicación: si pudiste seguir el consejo, "
            "si te olvidaste, si surgió algún problema nuevo, etc.\n"
            "- Esos eventos del nuevo día deben ser coherentes con tu perfil y con lo que hablaron antes."
        )
        
        actual_prompt = system_prompt if system_prompt else default_prompt
        
        # Optimización dinámica del prompt según el modelo elegido
        actual_prompt = self._optimize_system_prompt(actual_prompt, patient_model)

        messages = [{"role": "system", "content": actual_prompt}]
        
        # Separate system messages (instructions/alerts) from conversation history
        system_msgs_in_history = [m for m in history if m.get('role') == 'system']
        conversation_msgs = [m for m in history if m.get('role') != 'system']
        
        # Limit conversation history to last 6 messages
        recent_conversation = conversation_msgs[-6:] if len(conversation_msgs) > 6 else conversation_msgs
        
        # Reconstruct history: System prompts first, then conversation
        # Note: We process them to invert roles as needed
        
        # 1. Add preserved system messages (e.g. "EVENTO QUE TE OCURRIÓ")
        # Optimization: Only keep the most recent "New Day" event to avoid confusion
        final_system_msgs = []
        
        # Helper to check if a message is a "New Day" event
        def is_new_day_msg(m):
            role_ok = m.get('role') in ['system', 'episode']
            content = m.get('content', '').upper()
            return role_ok and ("NUEVO DÍA" in content or "EVENTO QUE TE OCURRIÓ" in content or "EPISODIO" in content)

        new_day_msgs = [m for m in history if is_new_day_msg(m)]
        other_system_msgs = [m for m in system_msgs_in_history if not is_new_day_msg(m)]
        
        # Add non-event system messages
        final_system_msgs.extend(other_system_msgs)
        
        # Add ONLY the last event message if any exist
        if new_day_msgs:
            final_system_msgs.append(new_day_msgs[-1])
            # EXTRACT STRONG REMINDER: If there is a new day event, we must ensure the model prioritizes it.
            # We append a specific reinforcement instruction at the very end of the conversation.
            latest_event_content = new_day_msgs[-1]['content']
            reminder_msg = {
                "role": "system", 
                "content": f"RECORDATORIO IMPORTANTE PARA TU RESPUESTA:\nTen muito en cuenta este evento reciente: {latest_event_content}\nSi el médico no lo mencionó, busca la forma de introducirlo o tenlo presente en tu estado de ánimo."
            }
            # We will append this AFTER constructing the full message list below
            
        for msg in final_system_msgs:
            messages.append({"role": "system", "content": msg['content']})
            
        # 2. Add recent conversation with inverted roles
        for msg in recent_conversation:
            if msg['role'] == 'user':
                # This was said by the Patient (us) -> becomes Assistant for the model
                messages.append({"role": "assistant", "content": msg['content']})
            elif msg['role'] == 'assistant':
                # This was said by the Psychologist (them) -> becomes User for the model
                messages.append({"role": "user", "content": msg['content']})
        
        # Add the psychologist's latest message as the latest input from the 'user' (interlocutor)
        messages.append({"role": "user", "content": psychologist_message})
        
        # 3. INJECT REMINDER INTO LAST MESSAGE (to force attention)
        if new_day_msgs:
             # Instead of a separate system message, we attach it to the immediate context
             # This forces the model to 'see' it as the current state of affairs
             messages[-1]['content'] += f"\n\n[EVENTO QUE ACABA DE OCURRIRME: {latest_event_content}. DEBO MENCIONAR ESTO EN MI RESPUESTA.]"

        print(f"--- Calling Patient Helper ({patient_model}) ---")
        print(f"System Prompt: {actual_prompt[:100]}...")
        print(f"\n=== DEBUG: FULL MESSAGES ARRAY BEING SENT TO LLM ===")
        for i, msg in enumerate(messages):
            print(f"Message {i}: role={msg['role']}, content={msg['content'][:100]}...")
        print(f"=== END DEBUG ===\n")
        import sys
        sys.stdout.flush()  # Force output to appear immediately

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
            "Actuás como un asistente en salud renal que usa internamente el modelo COM-B (Capacidad – Oportunidad – Motivación).\n\n"
            "IMPORTANTE:\n"
            "- Mantén tu rol de asistente profesional en todo momento.\n"
            "- Responde directamente a la inquietud del paciente, sin repetir todo lo que él dijo.\n\n"
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
        
        # Optimización dinámica del prompt según el modelo elegido
        actual_psico_prompt = self._optimize_system_prompt(actual_psico_prompt, chatbot_model)

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
        
        return self._extract_thought_and_response(raw_response)

    def generate_suggestion_only(self, patient_model, history, user_message, psychologist_response, patient_system_prompt=None, temperature=0.7, top_p=0.9, top_k=40, max_tokens=600, presence_penalty=0.1, frequency_penalty=0.2):
        """
        Step 2: Patient Helper suggests next reply.
        """
        updated_history = history + [{"role": "user", "content": user_message}]
        
        suggested_reply_data = self._extract_thought_and_response(self.get_patient_suggestion(
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
        suggested_reply = suggested_reply_data['content']

        # Clean any exposed instructions from the response
        import re
        
        # Remove common patterns where LLM exposes instructions
        patterns_to_remove = [
            r'We must obey instructions:.*?(?=\n|$)',
            r'INSTRUCCIÓN.*?(?=\n|$)',
            r'First line must.*?(?=\n|$)',
            r'And keep under.*?(?=\n|$)',
            r'\[.*?event.*?\].*?(?=\n|$)',
        ]
        
        for pattern in patterns_to_remove:
            suggested_reply = re.sub(pattern, '', suggested_reply, flags=re.IGNORECASE)
        
        # Clean up any remaining artifacts
        suggested_reply = suggested_reply.strip()
        
        suggested_reply_data['content'] = suggested_reply
        return suggested_reply_data

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

    def generate_patient_profile(self, model, guidance=None):
        """
        Generates a random patient profile using the LLM.
        Returns a dictionary with the patient's details.
        """
        system_prompt = (
            "You are a helpful assistant that generates synthetic medical data. "
            "Output ONLY valid JSON. Do not include any explanations, markdown formatting, or conversational text. "
            "Use double quotes for all keys and string values. Escape inner quotes properly."
        )
        
        guidance_text = ""
        if guidance:
            guidance_text = f"\nINSTRUCCIONES ADICIONALES DEL USUARIO: {guidance}\n"

        user_prompt = (
            "Genera un perfil JSON de un paciente de trasplante renal.\n"
            "IMPORTANTE: Varía la edad (entre 18 y 80 años), el género y el contexto social.\n"
            "Asegúrate de que todas las características (contexto, estilo de comunicación, dificultades, etc.) "
            "sean COHERENTES con la edad y situación de vida elegida.\n"
            f"{guidance_text}\n"
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
            # target_model = model if model else DEFAULT_MODEL_PATIENT
            target_model = "openai/gpt-oss-20b" # Force specific model for profile generation
            print(f"Generating profile with model: {target_model}")
            
            # Use a slightly lower temperature for more deterministic formatting
            response_text = self._call_llm(target_model, messages, temperature=0.8, max_tokens=1000)
            print(f"Raw profile response: {response_text[:200]}...") 
            
            # 1. Clean think tags
            response_data = self._extract_thought_and_response(response_text)
            response_text = response_data['content']
            
            # 2. Remove markdown code blocks if present
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*', '', response_text)

            # 3. Extract JSON using find/rfind (robust against pre/post text)
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            data = None
            
            if start != -1 and end != -1:
                json_str = response_text[start:end]
                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError:
                    print("JSON decode error. Trying ast.literal_eval fallback...")
                    try:
                        # ast.literal_eval can handle Python dict syntax (single quotes, etc.)
                        data = ast.literal_eval(json_str)
                    except Exception as e:
                        print(f"ast.literal_eval failed: {e}")
                        # Last ditch effort: try to fix common quote issues
                        try:
                            fixed_str = json_str.replace("'", '"')
                            data = json.loads(fixed_str)
                        except:
                            pass

            if not data:
                 # Try parsing the whole text if substring failed
                try:
                    data = json.loads(response_text)
                except:
                    try:
                        data = ast.literal_eval(response_text)
                    except:
                        pass

            if data and isinstance(data, dict):
                # Ensure all values are strings
                for key, value in data.items():
                    if isinstance(value, list):
                        data[key] = ", ".join(map(str, value))
                    elif isinstance(value, dict):
                        data[key] = json.dumps(value, ensure_ascii=False)
                    elif not isinstance(value, str):
                        data[key] = str(value)
                return data
            else:
                raise ValueError("Could not parse valid JSON or Dictionary from response")

        except Exception as e:
            print(f"Error generating profile: {e}")
            print(f"Error generating profile: {e}")
            raise e

    def analyze_interactions(self, model, interactions_text, system_prompt=None, **kwargs):
        """
        Analyzes a set of interactions using the specified LLM.
        """
        if not system_prompt:
            system_prompt = (
                "Sos un supervisor clínico experto en trasplante renal y salud conductual.\n"
                "Tu tarea es analizar las transcripciones de sesiones simuladas entre un Psicólogo (IA) y un Paciente (IA).\n"
                "Debes evaluar la calidad de la intervención del asistente en salud renal, la coherencia del paciente y el progreso general.\n\n"
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
        
        return self._extract_thought_and_response(self._call_llm(
            model,
            messages,
            **kwargs
        ))['content']

    def chat_analysis(self, model, history, system_prompt, context, **kwargs):
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
        return self._extract_thought_and_response(self._call_llm(
            model,
            messages,
            **kwargs
        ))['content']

    def simulate_interaction(self, chatbot_model, patient_model, psychologist_system_prompt, patient_system_prompt, turns=5, **kwargs):
        """
        Simulates an autonomous interaction between the Psychologist and the Patient.
        """
        history = []
        messages_log = []
        
        # Optimize prompts dynamically
        final_chatbot_prompt = self._optimize_system_prompt(psychologist_system_prompt, chatbot_model)
        final_patient_prompt = self._optimize_system_prompt(patient_system_prompt, patient_model)
        
        # Initial greeting
        last_psychologist_msg = "Hola. Soy tu asistente en salud renal virtual. ¿Cómo te sentís hoy?"
        messages_log.append({"role": "assistant", "content": last_psychologist_msg})
        
        print(f"--- Starting Simulation ({turns} turns) ---")

        for i in range(turns):
            # 1. Patient Responds
            print(f"Turn {i+1}: Patient responding...")
            
            # Construct patient history (Inverted roles: User=Psychologist, Assistant=Patient)
            patient_history_input = []
            for msg in history:
                if msg['role'] == 'user': # Patient said this
                    patient_history_input.append({"role": "assistant", "content": msg['content']})
                else: # Psychologist said this
                    patient_history_input.append({"role": "user", "content": msg['content']})
            
            patient_history_input.append({"role": "user", "content": last_psychologist_msg})
            
            patient_messages = [{"role": "system", "content": final_patient_prompt}] + patient_history_input
            
            patient_response_data = self._extract_thought_and_response(self._call_llm(
                patient_model,
                patient_messages,
                temperature=kwargs.get('patient_temperature', 0.7),
                max_tokens=kwargs.get('patient_max_tokens', 600)
            ))
            
            # Analyze Sentiment of the patient's clean response
            sentiment_data = None
            try:
                sentiment_data = self.analyze_sentiment(patient_response_data['content'], model=chatbot_model)
            except Exception as e:
                print(f"Error analyzing sentiment in simulation: {e}")

            # Add to log with thought and sentiment
            messages_log.append({
                "role": "user", 
                "content": patient_response_data['content'],
                "thought": patient_response_data['thought'],
                "sentiment": sentiment_data
            })
            
            # Add to history (standard format for next turn)
            history.append({"role": "user", "content": patient_response_data['content']})
            
            # 2. Psychologist Responds
            print(f"Turn {i+1}: Psychologist responding...")
            
            psico_messages = [{"role": "system", "content": final_chatbot_prompt}] + history
            
            psychologist_response_data = self._extract_thought_and_response(self._call_llm(
                chatbot_model,
                psico_messages,
                temperature=kwargs.get('psychologist_temperature', 0.7),
                max_tokens=kwargs.get('psychologist_max_tokens', 600)
            ))
            
            last_psychologist_msg = psychologist_response_data['content']
            
            # Add to log with thought
            messages_log.append({
                "role": "assistant", 
                "content": psychologist_response_data['content'],
                "thought": psychologist_response_data['thought']
            })
            
            history.append({"role": "assistant", "content": psychologist_response_data['content']})
            
        return messages_log

    def analyze_sentiment(self, text, model=None):
        """
        Analyzes the sentiment/psychological parameters of a patient's message.
        """
        # Use a lightweight or standard model for this task. Defaults to chatbot model if not specified.
        # We can use the same model as the chatbot for consistency, or a smarter one if available.
        target_model = model if model else DEFAULT_MODEL_CHATBOT
        
        system_prompt = (
            "Eres un experto en psicometría y análisis de sentimiento clínico. "
            "Tu tarea es analizar el siguiente mensaje de un paciente renal y puntuar los siguientes parámetros "
            "en una escala del 0 al 10 (donde 0 es nada/muy bajo y 10 es máximo/muy alto).\n"
            "También evalúa la valencia emocional de -5 (muy negativa) a +5 (muy positiva).\n\n"
            "Parámetros a evaluar:\n"
            "- valencia: -5 a +5\n"
            "- intensidad: 0 a 10 (intensidad de la emoción expresada)\n"
            "- frustracion: 0 a 10\n"
            "- hostilidad: 0 a 10\n"
            "- desesperanza: 0 a 10\n"
            "- autoeficacia: 0 a 10 (creencia en su propia capacidad de manejar su salud)\n\n"
            "Salida OBLIGATORIA: Un único objeto JSON con estas claves. Sin explicaciones ni texto extra."
        )
        
        user_prompt = f"Mensaje del paciente: \"{text}\""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response_text = self._call_llm(
                target_model, 
                messages, 
                temperature=0.1, # Low temp for deterministic JSON
                max_tokens=150
            )


            # Handle potential thinking blocks if the model puts them in (though prompts asks for JSON only)
            extracted = self._extract_thought_and_response(response_text)
            content = extracted['content']
            
            # Clean possible markdown
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            try:
                data = json.loads(content)
                return data
            except json.JSONDecodeError:
                # Fallback: try to finding JSON in text
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except:
                        pass
                print(f"Failed to parse sentiment JSON: {content}")
                return None
                
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return None
