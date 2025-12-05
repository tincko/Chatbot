"""
Script COMPLETO para actualizar endpoints de análisis a SQLite
"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Bloque COMPLETO para analyze_interactions
old_analyze_start = '@app.post("/api/analyze_interactions")\ndef analyze_interactions_endpoint(req: AnalyzeRequest):'
new_analyze_start = '@app.post("/api/analyze_interactions")\ndef analyze_interactions_endpoint(req: AnalyzeRequest, db: Session = Depends(get_db)):'

content = content.replace(old_analyze_start, new_analyze_start)

# Reemplazar el loop que lee archivos JSON
old_loop = '''        for filename in req.filenames:
            filepath = os.path.join(DIALOGOS_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extract relevant info for analysis
                    timestamp = data.get('timestamp', 'Unknown Date')
                    config = data.get('config', {})
                    
                    if 'patient_model' in config:
                        patient_models.add(config['patient_model'])
                    if 'patient_system_prompt' in config:
                        patient_prompts.add(config['patient_system_prompt'])
                    messages = data.get('messages', [])
                    
                    # Extract patient name from config (similar logic to get_interactions)
                    patient_name = "Unknown Patient"
                    patient_prompt = config.get('patient_system_prompt', '')
                    # import re # This import is now global
                    match = re.search(r"Sos el PACIENTE[:\s]+(.*?)(?:,|\.;|\n|$)", patient_prompt, re.IGNORECASE)
                    if match:
                        patient_name = match.group(1).strip()
                    
                    # Format conversation
                    conversation_text = f"--- Interaction Date: {timestamp} | Patient: {patient_name} ---\\n"
                    for msg in messages:
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        conversation_text += f"{role.upper()}: {content}\\n"
                    
                    interactions_content.append(conversation_text)'''

new_loop = '''        # Get interactions from database
        interactions = db_helpers.get_interactions_by_filenames(db, req.filenames)
        
        for data in interactions:
            # Extract relevant info for analysis
            timestamp = data.get('timestamp', 'Unknown Date')
            config = data.get('config', {})
            
            if 'patient_model' in config:
                patient_models.add(config['patient_model'])
            if 'patient_system_prompt' in config:
                patient_prompts.add(config['patient_system_prompt'])
            messages = data.get('messages', [])
            
            # Extract patient name from config
            patient_name = config.get('patient_name', 'Unknown Patient')
            
            # Format conversation
            conversation_text = f"--- Interaction Date: {timestamp} | Patient: {patient_name} ---\\n"
            for msg in messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                conversation_text += f"{role.upper()}: {content}\\n"
            
            interactions_content.append(conversation_text)'''

content = content.replace(old_loop, new_loop)

# Ahora analysis_chat
old_analysis_chat_start = '@app.post("/api/analysis_chat")\ndef analysis_chat_endpoint(req: AnalysisChatRequest):'
new_analysis_chat_start = '@app.post("/api/analysis_chat")\ndef analysis_chat_endpoint(req: AnalysisChatRequest, db: Session = Depends(get_db)):'

content = content.replace(old_analysis_chat_start, new_analysis_chat_start)

# Reemplazar el loop de analysis_chat
old_chat_loop = '''        interactions_text = ""
        for filename in req.interaction_filenames:
            filepath = os.path.join(DIALOGOS_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Format conversation (simplified)
                    timestamp = data.get('timestamp', 'Unknown')
                    patient = data.get('config', {}).get('patient_name', 'Unknown')
                    interactions_text += f"\\n--- Interaction: {filename} ({timestamp}, Patient: {patient}) ---\\n"
                    for msg in data.get('messages', []):
                        interactions_text += f"{msg.get('role', 'unknown').UPPER()}: {msg.get('content', '')}\\n"'''

new_chat_loop = '''        interactions_text = ""
        # Get interactions from database
        interactions = db_helpers.get_interactions_by_filenames(db, req.interaction_filenames)
        all_ints = db_helpers.get_all_interactions(db)
        
        for data in interactions:
            timestamp = data.get('timestamp', 'Unknown')
            patient = data.get('config', {}).get('patient_name', 'Unknown')
            # Find filename from timestamp
            filename = next((i['filename'] for i in all_ints if i['timestamp'] == timestamp), 'unknown')
            interactions_text += f"\\n--- Interaction: {filename} ({timestamp}, Patient: {patient}) ---\\n"
            for msg in data.get('messages', []):
                interactions_text += f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}\\n"'''

content = content.replace(old_chat_loop, new_chat_loop)

# Guardar
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Endpoints actualizados correctamente")
