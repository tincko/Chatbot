import time
import lmstudio as lms

# NOMBRES DE LOS MODELOS TAL COMO APARECEN EN LM STUDIO
#MODEL_A_ID = "mental_llama3.1-8b-mix-sft"
#MODEL_B_ID = "openai/gpt-oss-20b"
MODEL_A_ID = "mental_llama3.1-8b-mix-sft"
MODEL_B_ID = "openai/gpt-oss-20b"

def main():
    # Conectarse a LM Studio
    client = lms.Client()

    # Cargar modelos
    model_a = client.llm.model(MODEL_A_ID)
    model_b = client.llm.model(MODEL_B_ID)

    # Chats (guardan el historial de cada uno)
    chat_a = lms.Chat(
        "Sos un nefrólogo que trabaja con pacientes trasplantados de riñón."
    )
    chat_b = lms.Chat(
        "Sos un psicólogo experto en modelo COM-B y en nudges "
        "para mejorar la adherencia a la medicación."
    )

    # Mensaje inicial
    current_message = (
        "Hola, ¿cómo podemos ayudar a un paciente trasplantado a tomar "
        "siempre su medicación inmunosupresora?"
    )

    for turn in range(6):  # cantidad de turnos de ida y vuelta
        print(f"\n===== TURNO {turn + 1} =====")

        # 👉 Habla el MODELO A
        chat_a.add_user_message(current_message)
        reply_a = model_a.respond(chat_a)
        chat_a.add_assistant_response(reply_a)

        print("\n🩺 Modelo A (nefrólogo):")
        print(reply_a)

        # 👉 Esa respuesta se la mandamos al MODELO B
        chat_b.add_user_message(reply_a)
        reply_b = model_b.respond(chat_b)
        chat_b.add_assistant_response(reply_b)

        print("\n🧠 Modelo B (psicólogo / nudges COM-B):")
        print(reply_b)

        # Lo que diga B es el próximo mensaje que recibe A
        current_message = reply_b

        time.sleep(1)

if __name__ == "__main__":
    main()
