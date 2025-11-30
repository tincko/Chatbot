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

    def _call_llm(self, model, messages, temperature=0.7, max_tokens=2000):
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            # Increased timeout to allow for model loading
            response = requests.post(self.api_url, json=payload, timeout=1200)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling LLM {model}: {e}")
            if 'response' in locals():
                 print(f"Raw response: {response.text}")
            return f"[Error: {str(e)}]"

    def _clean_think_tags(self, text: str) -> str:
        """Removes <think>...</think> blocks and other model artifacts."""
        # Remove <think> blocks
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        
        # Remove <|channel|>... tags (common in some fine-tunes)
        text = re.sub(r"<\|.*?\|>.*?(?=\b[A-ZÁÉÍÓÚÑ]|$)", "", text, flags=re.DOTALL) 
        text = re.sub(r"<\|.*?\|>", "", text)
        
        # Remove specific artifacts like <｜begin of sentence｜>Human:
        text = re.sub(r"<｜.*?｜>Human:", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<｜.*?｜>", "", text)

        # Remove common reasoning preambles (heuristic)
        if re.match(r"^(We are asked|Here is a suggestion|The user wants|So reply)", text, re.IGNORECASE):
            # Try to find the last quoted string
            quotes = re.findall(r'"([^"]*)"', text)
            if quotes:
                return quotes[-1].strip()
            
            # Or try to split by "So reply..." or similar markers
            split_match = re.split(r"(So reply|The response is|Answer):", text, flags=re.IGNORECASE)
            if len(split_match) > 1:
                return split_match[-1].strip()

        return text.strip()

    def get_patient_suggestion(self, patient_model, history, psychologist_message, system_prompt=None):
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

        return self._call_llm(patient_model, messages, temperature=0.7)

    def chat(self, chatbot_model, patient_model, history, user_message, psychologist_system_prompt=None, patient_system_prompt=None):
        """
        Main chat flow:
        1. User (Patient) sends message.
        2. Chatbot (Psychologist) responds.
        3. System cleans <think> tags from Psychologist response.
        4. Patient Model (Helper) suggests next reply for User.
        """
        
        # 1. Chatbot (Psychologist) Step
        default_psico_prompt = (
            "Sos un asistente especializado en salud conductual y trasplante renal.\n"
            "Actuás como un psicólogo que usa internamente el modelo COM-B "
            "(Capacidad – Oportunidad – Motivación), pero NUNCA mencionás COM-B, "
            "ni CAPACIDAD, ni OPORTUNIDAD, ni MOTIVACIÓN, ni mostrás tu análisis.\n\n"
            "Tu tarea en cada turno es SOLO esta:\n"
            "- Pensar internamente qué le pasa al paciente (capacidad, oportunidad, motivación),\n"
            "- y responderle con UN ÚNICO mensaje breve (1 a 3 líneas),\n"
            "- cálido, empático y claro,\n"
            "- sin tecnicismos,\n"
            "- con un micro-nudge práctico (recordatorio, idea sencilla, pequeño paso concreto o refuerzo positivo).\n\n"
            "MUY IMPORTANTE (OBLIGATORIO):\n"
            "- Tu salida tiene que ser SOLO el mensaje al paciente.\n"
            "- NO escribas títulos como 'Análisis', 'Vamos a analizar', 'Posible respuesta'.\n"
            "- NO uses listas, bullets, ni explicaciones de tu razonamiento.\n"
            "- NO muestres secciones internas, ni uses etiquetas como <think>.\n\n"
            "FORMATO DE SALIDA OBLIGATORIO:\n"
            "- Una o dos frases dirigidas al paciente, en lenguaje natural.\n"
            "- Sin encabezados, sin numeración, sin comentarios meta.\n\n"
            "ESTILO DEL MENSAJE:\n"
            "- Usá un lenguaje cálido y cercano.\n"
            "- Usá 'vos'.\n"
            "- Frases cortas.\n"
            "- Nada de jerga clínica.\n"
            "- Sin órdenes médicas ni diagnósticos.\n"
            "- Siempre mantené un tono de guía que acompaña, no de autoridad.\n\n"
            "Ejemplo de estilo (no lo copies literal):\n"
            "Gracias por contarme eso. Podés probar dejar la medicación en un lugar que veas siempre a la misma hora; "
            "a veces un pequeño cambio ayuda mucho. Estoy para acompañarte en esto."
        )
        
        actual_psico_prompt = psychologist_system_prompt if psychologist_system_prompt else default_psico_prompt

        messages = [
            {"role": "system", "content": actual_psico_prompt},
            *history,
            {"role": "user", "content": user_message}
        ]

        raw_response = self._call_llm(chatbot_model, messages, temperature=0.7)
        
        # 2. Clean <think> tags
        clean_response = self._clean_think_tags(raw_response)

        # 3. Patient Helper Step (Suggest next reply)
        updated_history = history + [{"role": "user", "content": user_message}]
        
        suggested_reply = self._clean_think_tags(self.get_patient_suggestion(
            patient_model, 
            updated_history, 
            clean_response,
            system_prompt=patient_system_prompt
        ))

        return {
            "response": clean_response,
            "suggested_reply": suggested_reply
        }

    def list_models(self):
        try:
            # LM Studio usually has a GET /v1/models endpoint
            url = self.api_url.replace("/chat/completions", "/models")
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                data = response.json()
                return [m["id"] for m in data["data"]]
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
            "Campos requeridos:\n"
            "{\n"
            '  "nombre": "Nombre Ficticio",\n'
            '  "edad": 40,\n'
            '  "tipo_trasplante": "Renal (año)",\n'
            '  "medicacion": "Lista de medicamentos",\n'
            '  "adherencia_previa": "Breve descripción",\n'
            '  "contexto": "Situación social",\n'
            '  "nivel_educativo": "Nivel",\n'
            '  "estilo_comunicacion": "Cómo se expresa",\n'
            '  "fortalezas": "Puntos fuertes",\n'
            '  "dificultades": "Obstáculos",\n'
            '  "notas_equipo": "Sugerencias",\n'
            '  "idiosincrasia": "Rasgos culturales"\n'
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
