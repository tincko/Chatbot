import os
from datetime import datetime
import requests
import time
import re

# ==========================================================
# CONFIGURACIÓN DE LOGS
# ==========================================================
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

# ==========================================================
# CONFIGURACIÓN DE MODELOS Y API
# ==========================================================
URL = "http://127.0.0.1:1234/v1/chat/completions"

temperature = 0.7
top_p = 0.9
top_k = 40
max_tokens = 2000
presence_penalty = 0.1
frequency_penalty = 0.2

MODEL_PSICO = "deepseek/deepseek-r1-0528-qwen3-8b"
MODEL_PACIENTE = "openai/gpt-oss-20b"

# ==========================================================
# LLAMADA A MODELO
# ==========================================================
def ask_model(model_name, messages, role_label=""):
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
                "frequency_penalty": frequency_penalty,
            },
            timeout=600,
        )
    except Exception as e:
        error_msg = f"[ERROR REQUEST] Modelo={model_name} rol={role_label} exc={e}"
        print(error_msg)
        log(error_msg)
        return "[ERROR] Hubo un problema técnico."

    try:
        data = response.json()
    except Exception as e:
        log(f"[ERROR JSON] {response.text[:500]}")
        return "[ERROR] Respuesta inválida del modelo."

    if "error" in data and not data.get("choices"):
        log(f"[ERROR API] {data}")
        return "[ERROR] Fallo del modelo."

    if "choices" not in data:
        log("[ERROR SIN_CHOICES] " + str(data))
        return "[ERROR] Fallo del modelo."

    return data["choices"][0]["message"]["content"]

# ==========================================================
# RECORTAR HISTORIAL
# ==========================================================
def trim_history(history, max_pairs=6):
    if len(history) <= 1:
        return history
    system_msg = history[0]
    rest = history[1:]
    max_len = max_pairs * 2
    if len(rest) > max_len:
        rest = rest[-max_len:]
    return [system_msg] + rest

# ==========================================================
# LIMPIEZA DE <think> DE DEEPSEEK
# ==========================================================
def split_think_and_answer(text: str):
    think_blocks = re.findall(r"<think>(.*?)</think>", text, flags=re.DOTALL)
    think = "\n---\n".join(block.strip() for block in think_blocks)

    answer = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return think, answer

# ==========================================================
# SYSTEM PSICÓLOGO
# ==========================================================

system_psico = (
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
    "\"Gracias por contarme eso. Podés probar dejar la medicación en un lugar que veas siempre a la misma hora; "
    "a veces un pequeño cambio ayuda mucho. Estoy para acompañarte en esto.\"\n"
)

# ==========================================================
# PERFILES DE PACIENTES
# ==========================================================
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

# ==========================================================
# SYSTEM DEL PACIENTE
# ==========================================================
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

# ==========================================================
# SIMULACIÓN
# ==========================================================
log("===== INICIO DE SIMULACIÓN =====")
log(f"Fecha/Hora: {datetime.now()}")
log("="*60)

for profile in patient_profiles:
    print("\n" + "#" * 65)
    print(f"### SIMULACIÓN: {profile['id']} ({profile['nombre']})")
    print("#" * 65)

    log("\n" + "#" * 60)
    log(f"Paciente: {profile['id']} - {profile['nombre']}")
    log("#" * 60)

    system_paciente = build_system_paciente(profile)

    history_psico = [{"role": "system", "content": system_psico}]
    history_paciente = [{"role": "system", "content": system_paciente}]

    current_message = (
        f"Hola {profile['nombre'].split()[0]}, soy tu psicólogo. "
        "¿Cómo venís llevando el tema de tomar las pastillas del trasplante?"
    )

    logWithTime(f"[Psicólogo - Inicio] {current_message}")

    for turn in range(10):
        print(f"\n===== TURNO {turn+1} =====")

        # -------------------------------
        # PACIENTE HABLA
        # -------------------------------
        history_paciente.append({"role": "user", "content": current_message})
        history_paciente = trim_history(history_paciente)

        reply_paciente = ask_model(MODEL_PACIENTE, history_paciente, "paciente")
        if reply_paciente.startswith("[ERROR]"):
            log("[FIN ANTICIPADO] Error paciente")
            break

        history_paciente.append({"role": "assistant", "content": reply_paciente})

        print("\n🩺 Paciente:")
        print(reply_paciente)
        logWithTime(f"[Paciente]\n{reply_paciente}")

        # -------------------------------
        # PSICÓLOGO RESPONDE
        # -------------------------------
        history_psico.append({"role": "user", "content": reply_paciente})
        history_psico = trim_history(history_psico)

        reply_psico_raw = ask_model(MODEL_PSICO, history_psico, "psico")
        think_psico, reply_psico = split_think_and_answer(reply_psico_raw)

        log("===== PSICO THINK =====\n" + think_psico)
        log("===== PSICO RESPUESTA =====\n" + reply_psico)

        if reply_psico.startswith("[ERROR]"):
            log("[FIN ANTICIPADO] Error psico")
            break

        history_psico.append({"role": "assistant", "content": reply_psico})

        print("\n🧠 Psicólogo:")
        print(reply_psico)
        logWithTime(f"[Psicólogo]\n{reply_psico}")

        current_message = reply_psico  # el paciente reacciona a lo último dicho por el psicólogo
        time.sleep(1)

log("\n===== FIN DE SIMULACIÓN =====")