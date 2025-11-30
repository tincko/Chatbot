import requests
import json

import re

import os

# Configuration defaults (can be overridden)
DEFAULT_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_MODEL_CHATBOT = "deepseek/deepseek-r1-0528-qwen3-8b" # Psychologist
DEFAULT_MODEL_PATIENT = "openai/gpt-oss-20b" # Patient Helper

class DualLLMOrchestrator:
    def __init__(self, api_url=None):
        self.api_url = api_url or os.getenv("LLM_API_URL", DEFAULT_API_URL)

    def _call_llm(self, model, messages, temperature=0.7):
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 2000
            }
            response = requests.post(self.api_url, json=payload, timeout=600)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling LLM {model}: {e}")
            return f"[Error: {str(e)}]"

    def _clean_think_tags(self, text: str) -> str:
        """Removes <think>...</think> blocks from the text."""
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def get_patient_suggestion(self, patient_model, history, psychologist_message, system_prompt=None):
        """
        Generates a suggested reply for the patient (user) based on the psychologist's message.
        """
        default_prompt = (
            "You are acting as the Patient in this therapy session. "
            "Your goal is to suggest a natural, authentic response to the Psychologist's last message. "
            "Do not be too formal. React to what the psychologist just said. "
            "Output ONLY the suggested response text, nothing else."
        )
        
        actual_prompt = system_prompt if system_prompt else default_prompt

        # Construct context: History + Psychologist's latest message
        # We need to ensure the history format is correct for the LLM
        # The 'history' list contains:
        # - role='user' -> The Patient (which is the role this model is playing)
        # - role='assistant' -> The Psychologist (the person we are talking to)
        
        # When we send this to the Patient Model (to act as Patient), we need to flip roles:
        # - Real 'user' (Patient) -> becomes 'assistant' (Self)
        # - Real 'assistant' (Psychologist) -> becomes 'user' (Interlocutor)
        
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
            "You are a Psychologist. Be warm, empathetic, and professional. "
            "Respond to the patient's input."
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
        # We pass the history + the NEW user message + the NEW psychologist response
        # The 'history' arg passed to this function didn't include the current user_message yet
        updated_history = history + [{"role": "user", "content": user_message}]
        
        suggested_reply = self.get_patient_suggestion(
            patient_model, 
            updated_history, 
            clean_response,
            system_prompt=patient_system_prompt
        )

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
