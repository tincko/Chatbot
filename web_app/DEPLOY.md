# Guía de Despliegue (Deployment Guide)

Esta guía te ayudará a subir tu aplicación "DualMind" a un servidor barato (VPS) y configurarlo con un dominio de No-IP.

## 1. Requisitos Previos

1.  **Servidor VPS**: Necesitás alquilar un servidor.
    *   *Recomendación Barata*: Hetzner Cloud (CPX11 ~€5/mes), DigitalOcean Droplet ($6/mes), o OVH.
    *   *Sistema Operativo*: Ubuntu 22.04 o 24.04 (LTS).
2.  **Cuenta No-IP**:
    *   Creá una cuenta en [noip.com](https://www.noip.com).
    *   Creá un "Hostname" (ej: `michatbot.ddns.net`) y apuntalo a la **IP Pública** de tu nuevo VPS.
3.  **Docker**: La aplicación ya está configurada para usar Docker, lo que hace el despliegue muy fácil.

---

## 2. El Problema del Modelo (LLM)

**IMPORTANTE**: Los servidores baratos (VPS de $5-10) **NO tienen tarjeta gráfica (GPU)**.
Esto significa que **NO podrás correr modelos grandes** (como DeepSeek 7B o GPT-OSS) directamente en el servidor de forma rápida.

Tenés 3 opciones:

*   **Opción A (Recomendada para Producción)**: Usar una API externa (OpenAI, DeepSeek API, OpenRouter).
    *   *Costo*: Pagás por uso.
    *   *Configuración*: Cambiás la URL en el `docker-compose.yml` a la de la API.
*   **Opción B (Túnel a Casa)**: Dejar el modelo corriendo en TU PC (con GPU) y conectar el servidor a tu casa.
    *   *Costo*: Gratis (usás tu luz).
    *   *Configuración*: Usás `ngrok` en tu PC para exponer el puerto 1234 y ponés esa URL en el servidor.
*   **Opción C (Lento)**: Correr un modelo muy pequeño (Quantized GGUF) en el CPU del servidor.
    *   *Costo*: Gratis (incluido en VPS).
    *   *Desventaja*: Será muy lento (tokens por segundo bajos).

---

## 3. Pasos para Desplegar

### Paso 1: Preparar el Servidor
Conectate a tu VPS por SSH:
```bash
ssh root@tu-ip-del-vps
```

Instalá Docker y Docker Compose:
```bash
# Actualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verificar
docker --version
docker compose version
```

### Paso 2: Subir el Código
Podés usar `git` si subís tu código a GitHub/GitLab, o copiar los archivos desde tu PC usando `scp`.

**Opción SCP (desde tu PC):**
Asegurate de estar en la carpeta `Chatbot/web_app`:
```powershell
# Ejemplo en PowerShell
scp -r . root@tu-ip-del-vps:/root/chatbot
```

### Paso 3: Configurar y Correr
En el servidor:
```bash
cd /root/chatbot
```

Editá el archivo `docker-compose.yml` si necesitás cambiar la URL del LLM:
```bash
nano docker-compose.yml
```
*   Si usás **Opción B (Ngrok)**: Cambiá `LLM_API_URL` a tu URL de Ngrok (ej: `https://xxxx.ngrok-free.app/v1/chat/completions`).
*   Si usás **Opción A (API)**: Poné la URL de la API y asegurate de manejar las API Keys (quizás necesites modificar el código para pasar headers de autorización).

Arrancá la aplicación:
```bash
docker compose up -d --build
```

### Paso 4: Configurar No-IP (Si tenés IP Dinámica)
Si tu VPS tiene IP Estática (lo normal), solo configurá el registro A en el panel de No-IP.
Si por alguna razón es dinámica, instalá el cliente de No-IP en el servidor:
```bash
cd /usr/local/src/
wget http://www.noip.com/client/linux/noip-duc-linux.tar.gz
tar xf noip-duc-linux.tar.gz
cd noip-2.1.9-1/
make
make install
# Te pedirá tu usuario y contraseña de No-IP
```

## 4. ¡Listo!
Ahora podés entrar a:
`http://michatbot.ddns.net` (o tu dominio elegido).

---

## Notas Adicionales
*   **Seguridad**: Este despliegue usa HTTP (puerto 80). Para HTTPS, necesitarás configurar un proxy reverso con SSL (como Nginx Proxy Manager o Traefik), o usar Certbot manualmente.
## 5. Opción con GPU y Tope de Gastos (Control Total)

Si querés correr los modelos en un servidor potente pero tenés miedo de que te llegue una factura gigante (como pasa en AWS o Google Cloud), la mejor opción son los proveedores de **GPU bajo demanda con sistema prepago**.

### ¿Por qué Prepago?
En estos servicios, cargás un saldo (ej: $10 o $20 USD). El servidor consume ese saldo por hora. **Cuando el saldo llega a cero, el servidor se apaga automáticamente.** Es la única forma real de garantizar un "tope" estricto.

### Proveedores Recomendados

1.  **RunPod (Muy Recomendado)**
    *   **Modelo**: "Pods" (Contenedores Docker con GPU).
    *   **Costo**: Desde ~$0.30/hora por una GPU decente (RTX 3090 / 4090).
    *   **Control**: Cargás créditos. Si se acaban, se para.
    *   **Uso**: Tienen plantillas listas con "vLLM" o "Text Generation WebUI" para levantar una API compatible con OpenAI en 1 clic.

2.  **Vast.ai**
    *   **Modelo**: Mercado de GPUs (alquilás máquinas de otros).
    *   **Costo**: Extremadamente barato (a veces $0.15/hora).
    *   **Control**: También prepago.
    *   **Desventaja**: La disponibilidad varía y la seguridad es menor (no recomendado para datos muy sensibles).

3.  **Lambda Labs**
    *   **Modelo**: Cloud GPU tradicional.
    *   **Costo**: Muy competitivo (~$0.50/hora por A10).
    *   **Control**: Facturación mensual por tarjeta, es más difícil poner un "hard stop" automático.

### Arquitectura Sugerida (Híbrida)

Para optimizar costos, no corras la Web App (Frontend) en el servidor de GPU, porque estarías pagando GPU las 24hs solo para mostrar una página web.

1.  **Servidor Barato (VPS ~€5/mes)**:
    *   Aloja: Tu Frontend (React) y Backend (Python/FastAPI).
    *   Está prendido 24/7.
    *   Tiene la IP fija y el dominio (No-IP).

2.  **Servidor GPU (RunPod ~Pago por uso)**:
    *   Aloja: Solo el Modelo LLM (DeepSeek/GPT-OSS).
    *   **Lo prendés solo cuando vas a usarlo.**
    *   Te da una URL temporal (ej: `https://pod-12345.runpod.io`).

**Configuración:**
Cuando prendas el RunPod, copiás la URL que te da y actualizás la variable de entorno `LLM_API_URL` en tu VPS (o en tu panel de Portainer/Docker) y listo.

