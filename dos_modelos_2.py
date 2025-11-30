import os
from datetime import datetime
import requests
import time

# -------- LOG GLOBAL --------
folder = "dialogos"
os.makedirs(folder, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = f"{folder}/simulacion_{timestamp}.txt"

def log(text: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def logWithTime(text: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(datetime.now().strftime("%Y%m%d_%H%M%S") + " : " + text + "\n")

# ----------------------------


URL = "http://127.0.0.1:1234/v1/chat/completions"
temperature = 0.7
top_p = 0.9
top_k = 40
max_tokens = 200
presence_penalty = 0.1
frequency_penalty = 0.2


#"mental_llama3.1-8b-mix-sft"
# "psycollm"
#"tinyllama-chat-psychotherapist" - NO! ES EN INGLES!
#"psychotherapy-llm_psychocounsel-llama3-8b"
#"qwen/qwen3-4b-thinking-2507"  NO! INGLES Y parece que razona pero no
#"mradermacher/mistral7b-psycho-mergedv3-GGUF" 

MODEL_PSICO = "deepseek/deepseek-r1-0528-qwen3-8b"
MODEL_PACIENTE = "openai/gpt-oss-20b"      


def ask_model(model_name, messages, role_label=""):
    """Llama al modelo y maneja errores básicos."""
    try:
        response = requests.post(
            URL,
            json={
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "max_tokens": max_tokens,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty
            },
            timeout=10000,
        )
    except Exception as e:
        error_msg = f"[ERROR REQUEST] Modelo={model_name} rol={role_label} exc={e}"
        print(error_msg)
        log(error_msg)
        return "[ERROR] Hubo un problema técnico al conectar con el modelo."

    # Intentar parsear JSON
    try:
        data = response.json()
    except Exception as e:
        error_msg = (
            f"[ERROR JSON] Modelo={model_name} rol={role_label} "
            f"status={response.status_code} exc={e}"
        )
        print(error_msg)
        log(error_msg)
        log(f"[ERROR JSON RAW] {response.text[:500]}")
        return "[ERROR] El modelo devolvió una respuesta no válida."

    # Manejo explícito de errores del servidor (por ej. context length)
    if "error" in data and not data.get("choices"):
        error_msg = (
            f"[ERROR API] Modelo={model_name} rol={role_label} "
            f"status={response.status_code} body={data}"
        )
        print(error_msg)
        log(error_msg)
        # Devolvemos algo corto para que el otro agente pueda cerrar o seguir
        return "[ERROR] El modelo no pudo responder bien en este turno."

    if "choices" not in data:
        error_msg = (
            f"[ERROR SIN_CHOICES] Modelo={model_name} rol={role_label} "
            f"status={response.status_code} body={data}"
        )
        print(error_msg)
        log(error_msg)
        return "[ERROR] No se pudo generar una respuesta válida."

    return data["choices"][0]["message"]["content"]


def trim_history(history, max_pairs=8):
    """
    Mantiene el primer mensaje (system) y solo los últimos `max_pairs`
    pares (user+assistant). Así evitamos que el contexto se haga infinito.
    """
    if len(history) <= 1:
        return history

    system_msg = history[0]
    rest = history[1:]

    # Cada interacción normal son 2 mensajes: user + assistant
    max_len = max_pairs * 2
    if len(rest) > max_len:
        rest = rest[-max_len:]

    return [system_msg] + rest



system_psico = (
    "Sos un asistente especializado en salud conductual y trasplante renal.\n"
    "Actuás como un psicólogo que trabaja con el modelo COM-B (Capacidad – Oportunidad – Motivación),\n"
    "pero NUNCA mencionás COM-B ni mostrás el análisis interno al paciente.\n\n"

    "Tu tarea es:\n"
    "- analizar internamente lo que dice el paciente (capacidad, oportunidad, motivación),\n"
    "- responderle con un mensaje breve (1 a 3 líneas),\n"
    "- cálido, empático y claro,\n"
    "- sin tecnicismos,\n"
    "- con un micro-nudge práctico (recordatorio, idea sencilla, pequeño paso concreto, refuerzo positivo).\n\n"

    "ANÁLISIS INTERNO (NO mostrar al paciente):\n"
    "- CAPACITY: olvidos, confusión, organización; cansancio, dolor, limitaciones.\n"
    "- OPPORTUNITY: entorno, horarios, acceso a medicación; apoyo familiar, carga emocional.\n"
    "- MOTIVATION: emociones, hábitos automáticos; creencias, percepciones y expectativas.\n"
    "Este análisis es SOLO interno y no debe aparecer explícito en la respuesta.\n\n"

    "SOBRE LA CONVERSACIÓN EN UN MISMO DÍA:\n"
    "- Intentá mantener varias idas y vueltas con el paciente en el mismo día.\n"
    "- No cierres la conversación demasiado rápido salvo que el paciente lo pida explícitamente.\n"
    "- Podés hacer preguntas de seguimiento cortas para entender mejor su situación antes de despedirte.\n\n"

    "SOBRE DESPEDIDAS Y DÍAS DISTINTOS:\n"
    "- Cuando consideres que una ronda está razonablemente cerrada, podés despedirte de forma breve y cálida.\n"
    "- Variá la forma de despedirte: a veces solo agradecé y cerrá (\"gracias por contarme, seguimos en contacto\"),\n"
    "  a veces podés sugerir que más adelante vuelvan a hablar (\"cuando quieras seguimos ajustando esto\"),\n"
    "  y SOLO A VECES mencioná explícitamente \"mañana\" o \"otro día\". No repitas siempre \"hasta mañana\".\n"
    "- Si más adelante la conversación continúa después de una despedida, actuá como si hubiera pasado\n"
    "  UN DÍA ENTERO desde la última charla.\n"
    "- En ese 'día siguiente', saludá de nuevo (\"hola, buen día, ¿cómo te fue desde la última vez?\")\n"
    "  y conectá tu mensaje con lo que habían acordado o trabajado antes.\n\n"

    "ESTILO DEL MENSAJE:\n"
    "- Usá un lenguaje cálido y cercano.\n"
    "- Usá 'vos'.\n"
    "- Frases cortas.\n"
    "- Nada de jerga clínica.\n"
    "- Sin órdenes médicas ni diagnósticos.\n"
    "- Siempre mantené un tono de guía que acompaña, no de autoridad.\n\n"

    "FORMATO DE SALIDA OBLIGATORIO:\n"
    "- Un ÚNICO mensaje corto dirigido al paciente.\n"
    "Ejemplo de estilo (no lo copies literal):\n"
    "\"Gracias por contarme eso. Podés probar dejar la medicación en un lugar que veas siempre a la misma hora; "
    "a veces un pequeño cambio ayuda mucho. Estoy para acompañarte en esto.\"\n"

    "El psicólogo tiene en la medida de lo posible adaptarse a la idiosincrasia uruguaya"
)





# ---------------------------------------------------------
# PERFILES DE PACIENTES
# ---------------------------------------------------------
patient_profiles = [

    {
        "id": "carlos_68",
        "nombre": "Carlos S.",
        "edad": 68,
        "tipo_trasplante": "Renal (2021)",
        "medicacion": "Tacrolimus 1mg + MMF 500mg x2",
        "adherencia_previa": "Irregular; depende de su esposa para organizar pastillas.",
        "contexto": "Jubilado, vive con esposa; dificultades de memoria leve.",
        "nivel_educativo": "Primaria incompleta.",
        "estilo_comunicacion": "Necesita mensajes muy simples, paso a paso.",
        "fortalezas": "Buena actitud hacia el equipo médico, acepta ayuda.",
        "dificultades": "Baja alfabetización en salud; olvida pastillas si está solo.",
        "notas_equipo": "Evitar lenguaje técnico; reforzar señales visuales.",
        "idiosincrasia" : "Debe adaptarse a los estandares de la idiosincrasia uruguaya"
    },

    {
        "id": "lucia_32",
        "nombre": "Lucía R.",
        "edad": 32,
        "tipo_trasplante": "Renal (2022)",
        "medicacion": "Tacrolimus 2mg, Everolimus 1mg",
        "adherencia_previa": "Buena pero con episodios de ansiedad que generan dudas.",
        "contexto": "Vive sola; trabaja remoto en tecnología.",
        "nivel_educativo": "Universitario.",
        "estilo_comunicacion": "Le gusta información clara, directa y basada en lógica.",
        "fortalezas": "Muy responsable; usa apps y tecnología fácilmente.",
        "dificultades": "Crisis de ansiedad cuando siente efectos secundarios.",
        "notas_equipo": "Evitar alarmar; validar emociones; ofrecer micro-rutinas.",
        "idiosincrasia" : "Debe adaptarse a los estandares de la idiosincrasia uruguaya"
    },

    {
        "id": "mateo_17",
        "nombre": "Mateo G.",
        "edad": 17,
        "tipo_trasplante": "Renal (2020)",
        "medicacion": "Tacrolimus 1mg x2 + Prednisona 5mg",
        "adherencia_previa": "Fluctuante; omite dosis cuando está con amigos.",
        "contexto": "Vive con padres; conflicto leve con figura de autoridad.",
        "nivel_educativo": "Secundaria.",
        "estilo_comunicacion": "Mensajes breves, informales y motivacionales.",
        "fortalezas": "Inteligente, capaz de comprender consecuencias cuando quiere.",
        "dificultades": "Impulsividad; baja motivación reflexiva; busca aceptación social.",
        "notas_equipo": "No usar tono autoritario; reforzar autonomía y pequeños logros.",
        "idiosincrasia" : "Debe adaptarse a los estandares de la idiosincrasia uruguaya."
    },

    {
        "id": "fernanda_45",
        "nombre": "Fernanda D.",
        "edad": 45,
        "tipo_trasplante": "Renal (2019)",
        "medicacion": "Tacrolimus 2mg + MMF 750mg",
        "adherencia_previa": "Dificultades por horarios; olvidos frecuentes durante el turno nocturno.",
        "contexto": "Trabajo rotativo; madre soltera; poco tiempo libre.",
        "nivel_educativo": "Secundaria.",
        "estilo_comunicacion": "Directo, práctico.",
        "fortalezas": "Motivación alta; quiere cuidar el injerto por sus hijos.",
        "dificultades": "Oportunidad física limitada (horarios caóticos); cansancio.",
        "notas_equipo": "Ofrecer soluciones adaptadas a rutinas variables.",
        "idiosincrasia" : "Debe adaptarse a los estandares de la idiosincrasia uruguaya."
    },

    {
        "id": "adrian_51",
        "nombre": "Adrián C.",
        "edad": 51,
        "tipo_trasplante": "Renal (2017)",
        "medicacion": "Tacrolimus + Azatioprina",
        "adherencia_previa": "Irregular en periodos de ánimo bajo.",
        "contexto": "Vive con pareja; días con poca energía.",
        "nivel_educativo": "Técnico.",
        "estilo_comunicacion": "Cálido, empático, no invasivo.",
        "fortalezas": "Comprende la importancia del tratamiento.",
        "dificultades": "Motivación automática baja; apatía.",
        "notas_equipo": "Validar emociones; evitar presión; micro-pasos.",
        "idiosincrasia" : "Debe adaptarse a los estandares de la idiosincrasia uruguaya."
    },

    {
        "id": "ahmed_39",
        "nombre": "Ahmed K.",
        "edad": 39,
        "tipo_trasplante": "Renal (2020)",
        "medicacion": "Tacrolimus 1mg x2",
        "adherencia_previa": "Dificultades por idioma y diferencias culturales.",
        "contexto": "Migrante reciente; esposa no habla español.",
        "nivel_educativo": "Universitario.",
        "estilo_comunicacion": "Claro, formal y respetuoso.",
        "fortalezas": "Muy comprometido; desea integrar las recomendaciones.",
        "dificultades": "Oportunidad social limitada; poca red de apoyo.",
        "notas_equipo": "Priorizar claridad; verificar comprensión sin generar vergüenza.",
        "idiosincrasia" : "Debe adaptarse a los estandares de la idiosincrasia española."
    },
]


# ---------------------------------------------------------
# FUNCIÓN PARA CREAR EL SYSTEM DEL PACIENTE
# ---------------------------------------------------------
def build_system_paciente(profile: dict) -> str:
    return (
        f"Sos el PACIENTE {profile['nombre']}, receptor de trasplante de riñón.\n"
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
        "- Tus despedidas pueden ser variadas: a veces solo agradecer (\"gracias, me ayudó\"),\n"
        "  a veces mencionar que te sirve por ahora (\"por ahora estoy bien, gracias\"), y SOLO A VECES\n"
        "  decir que hablan mañana u otro día. No repitas siempre \"hasta mañana\".\n\n"

        "SOBRE EL PASO DE LOS DÍAS:\n"
        "- Si en algún momento te despedís y luego la conversación continúa más adelante,\n"
        "  actuá como si hubiera pasado UN DÍA ENTERO desde la última charla.\n"
        "- En ese 'nuevo día', saludá de nuevo al psicólogo (por ejemplo: \"hola, buen día doctor…\").\n"
        "- Contá brevemente qué pasó desde la última vez con la medicación: si pudiste seguir el consejo,\n"
        "  si te olvidaste, si surgió algún problema nuevo, etc.\n"
        "- Esos eventos del nuevo día deben ser coherentes con tu perfil y con lo que hablaron antes.\n\n"

        "[PERFIL DEL PACIENTE - SOLO PARA USO INTERNO]\n"
        f"Nombre: {profile['nombre']}\n"
        f"Edad: {profile['edad']}\n"
        f"Tipo de trasplante: {profile['tipo_trasplante']}\n"
        f"Medicación: {profile['medicacion']}\n"
        f"Adherencia previa: {profile['adherencia_previa']}\n"
        f"Contexto personal: {profile['contexto']}\n"
        f"Nivel educativo: {profile['nivel_educativo']}\n"
        f"Estilo de comunicación: {profile['estilo_comunicacion']}\n"
        f"Fortalezas: {profile['fortalezas']}\n"
        f"Dificultades: {profile['dificultades']}\n"
        f"Notas del equipo: {profile['notas_equipo']}\n"
        "[FIN DEL PERFIL]\n"
    )




# ---------------------------------------------------------
# SIMULACIÓN
# ---------------------------------------------------------
log("===== INICIO DE SIMULACIÓN =====")
log(f"Fecha/Hora: {datetime.now()}")
log("="*80 + "\n")
log(" MODELO PACIENTE: " + MODEL_PACIENTE + "\n")
log(" MODELO PSICO: " + MODEL_PSICO + "\n\n")

log("temperature : " + str(temperature) + "\n")
log("top_p : " + str(top_p) + "\n")
log("top_k : " + str(top_k) + "\n")
log("max_tokens : " + str(max_tokens) + "\n")
log("presence_penalty : " + str(presence_penalty) + "\n")
log("frequency_penalty : " + str(frequency_penalty) + "\n")




for profile in patient_profiles:

    log("\n" + "#"*80)
    log(f"Paciente: {profile['id']} - {profile['nombre']}")
    log("#"*80 + "\n")

    print("\n" + "#" * 70)
    print(f"### INICIO DE SIMULACIÓN PARA: {profile['id']} ({profile['nombre']})")
    print("#" * 70)

    system_paciente = build_system_paciente(profile)

    history_psico = [{"role": "system", "content": system_psico}]
    history_paciente = [{"role": "system", "content": system_paciente}]

    current_message = (
        f"Hola {profile['nombre'].split()[0]}, soy tu psicólogo. "
        "¿Cómo venís llevando el tema de tomar las pastillas del trasplante a horario?"
    )

    logWithTime(f"[Psicólogo - Inicio] {current_message}")

    for turn in range(10):
        print(f"\n===== TURNO {turn+1} =====")

        # 1) PACIENTE HABLA
        history_paciente.append({"role": "user", "content": current_message})
        reply_paciente = ask_model(MODEL_PACIENTE, history_paciente, role_label="paciente")
        if reply_paciente.startswith("[ERROR]"):
            print("\n⚠ Error al responder el paciente, se corta este paciente.\n")
            logWithTime(f"[FIN ANTICIPADO] Error en paciente {profile['id']} en turno {turn+1}")
            break
        history_paciente.append({"role": "assistant", "content": reply_paciente})

        print("\n" + datetime.now().strftime("%H:%M:%S") + "🩺 Paciente: ")
        print(reply_paciente)
        (f"\n===== TURNO {turn+1} =====")
        logWithTime(f" [Paciente]-------------------------------------\n")
        log(reply_paciente)

        # 2) PSICÓLOGO RESPONDE
        history_psico.append({"role": "user", "content": reply_paciente})
        reply_psico    = ask_model(MODEL_PSICO, history_psico, role_label="psicologo")
        if reply_psico.startswith("[ERROR]"):
            print("\n⚠ Error al responder el psicólogo, se corta este paciente.\n")
            logWithTime(f"[FIN ANTICIPADO] Error en psicólogo para paciente {profile['id']} en turno {turn+1}")
            break
        history_psico.append({"role": "assistant", "content": reply_psico})

        print("\n" + datetime.now().strftime("%H:%M:%S") + "🧠 Psicólogo / COM-B:")
        print(reply_psico)
        logWithTime(f"[Psicólogo]-------------------------------------\n")
        log(reply_psico)

        current_message = reply_psico
        time.sleep(1)


log("\n===== FIN DE SIMULACIÓN =====")
