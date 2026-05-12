# 🧠 Guía de Supervivencia: Caitlyn en Docker

¡Hola! Aquí tienes el diagnóstico de por qué Caitlyn pudo haber tenido problemas en tu HP Pavilion Gaming y cómo solucionarlo paso a paso.

## 🕵️ ¿Qué pudo haber fallado?

1.  **El "Apretón de Manos" con MongoDB:**
    *   **Problema:** Por defecto, Caitlyn buscaba la base de datos en `127.0.0.1`. Dentro de Docker, eso significa "dentro de sí mismo". Al no encontrar a nadie, el proceso de inicio se quedaba colgado intentando conectar.
    *   **Solución:** Ya agregamos un `timeout` de 2 segundos y un modo "Offline" para que la app no muera si la DB no responde.

2.  **Descarga Incompleta (Playwright):**
    *   **Problema:** Los navegadores de Playwright (Chromium) pesan cientos de MB. Si la conexión falló un momento durante el `docker build`, la instalación puede quedar corrupta.
    *   **Solución:** Forzar un rebuild limpio de la imagen.

3.  **Hardware de Gaming (NVIDIA/HP):**
    *   **Problema:** Al ser una laptop gaming, a veces Docker intenta usar aceleración por hardware que no está disponible dentro del contenedor.
    *   **Solución:** Usamos `xvfb-run` (pantalla virtual) para que el navegador corra de forma 100% "headless" y por software.

---

## 🚀 Comandos de Poder (Docker)

Ejecuta estos comandos en tu terminal dentro de la carpeta `ionic-maps-backend`:

### 1. Limpieza y Reconstrucción
Esto asegura que no usemos capas viejas o corruptas.
```bash
# Borra imágenes anteriores para empezar de cero
docker rmi caitlyn-backend -f

# Construye la imagen (esto puede tardar por la descarga de Chromium)
docker build -t caitlyn-backend .
```

### 2. Arranque Maestro
Para que Caitlyn vea tu máquina real (el host), usamos `--add-host`.
```bash
docker run -d \
  --name caitlyn-container \
  -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  --env-file .env \
  caitlyn-backend
```

### 3. Ver qué está pasando (Logs)
Si algo no arranca, este comando te dirá exactamente el porqué:
```bash
docker logs -f caitlyn-container
```

### 4. Entrar al contenedor (Debug)
Si quieres ver si los archivos están ahí dentro:
```bash
docker exec -it caitlyn-container bash
```

---

## 💡 Tips Pro para tu HP Pavilion (Linux)
*   Si MongoDB está en tu máquina local, asegúrate de que el archivo `.env` use `MONGODB_URL=mongodb://172.17.0.1:27017` o `mongodb://host.docker.internal:27017`.
*   Si ves errores de "Shared library missing", avísame; significa que nos falta una librería de sistema en el `Dockerfile`.

¡Dale fuego a esos comandos! 🚀
