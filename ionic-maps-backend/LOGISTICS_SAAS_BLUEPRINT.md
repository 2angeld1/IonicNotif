# 🚢 Mega-Blueprint: SaaS de Automatización Logística (Caitlyn Logistics)

## 📝 1. Visión del Problema y Solución
- **El Dolor:** Los operadores logísticos pierden entre 30-60 minutos por booking haciendo copy-paste manual entre portales de navieras, sistemas de clientes, y plantillas de Word.
- **La Solución:** Un "Agente IA" (Caitlyn) que orqueste la extracción, cruce de datos y generación de documentos en un flujo de **3 clicks**.

---

## 💻 2. Estrategia de Plataforma (Web vs Mobile)
- **Decisión Senior:** La herramienta será una **Web App (Next.js)**, NO móvil.
- **Razón:** Los operadores logísticos trabajan en entornos multimonitor, manejan PDFs complejos y portales web pesados. La precisión necesaria para validar documentos técnicos se logra mejor en una pantalla de escritorio. El móvil queda descartado para la fase operativa por falta de eficiencia.

---

## 🖱️ 3. Flujo de Experiencia de Usuario (UX)
1.  **Configuración Inicial:** El usuario loguea su cuenta y guarda sus credenciales de navieras (encriptadas).
2.  **Input:** Ingreso del Booking Number o carga de archivo base.
3.  **Narración en Tiempo Real (Killer Feature):** Caitlyn informa vía Socket.io:
    - *"Iniciando sesión en MSC..."*
    - *"Extrayendo ETA y Vessel Name..."*
    - *"Cruzando con datos del cliente en tu base de datos..."*
4.  **Validación:** Visualizador de "Borrador" (Draft) donde el usuario ve el PDF generado y puede corregir campos detectados antes de finalizar.
5.  **Envío Automático:** Un click para enviar por correo el PDF final a los destinatarios preconfigurados.

---

## 🏗️ 4. Arquitectura Técnica y Herramientas
- **Frontend:** Next.js + Tailwind CSS + Socket.io-client.
- **Backend Operativo:** Node.js + Express (Gestión de usuarios, auditoría, encriptación).
- **Backend Inteligencia:** Python + FastAPI (Caitlyn Core).
- **Estrategia de Extracción de Datos:**
    - **APIs Oficiales (DCSA):** Prioridad para navieras modernas (Maersk, Hapag-Lloyd, MSC). Más rápido y estable.
    - **Agregadores (Shipsgo/Vizion):** Alternativa para centralizar múltiples navieras en un solo JSON.
    - **Playwright (Scraping Activo):** "Último recurso" para portales con login sin API. Funciona como las "manos" de Caitlyn.
- **Cerebro Vision:** Gemini 3 Flash (Structured Outputs para screenshots).
- **Generación de Documentos:**
    - `python-docx-template` (docxtpl) para rellenar plantillas Word diseñadas por el usuario.
    - `LibreOffice (Headless)` para exportación fiel de Word a PDF en servidor Linux.

---

## 🔐 5. Seguridad y Privacidad (Standard Senior)
- **Credenciales Propias:** Hashing con **Argon2id** (una vía, no reversible).
- **Credenciales de Navieras (Terceros):** Encriptación reversible **AES-256-GCM** (con IV único y Auth Tag).
- **Key Management:** Uso de Master Key inyectada en tiempo real vía Secret Manager (GCP/AWS) o variables de entorno protegidas. Nunca en el código.
- **Principio de Confianza:** Auditoría de logs de acceso y transparencia con el cliente sobre el uso de sus llaves solo para automatización.

---

## 🐳 6. Infraestructura y Dockerización
- **Dockerizar (SÍ):** Backend Node y AI Microservice (Python). Garantiza que las dependencias de sistema (LibreOffice, Playwright, librerías de C) funcionen igual en cualquier servidor.
- **Dockerizar (NO):** Mobile (en desarrollo). Expo Go es mejor manejarlo nativamente por temas de hardware/red.
- **Orquestación:** `docker-compose` para levantar el ecosistema completo localmente con un comando.

---

## 📊 7. Competencia y Oportunidad de Mercado
- **Enterprise (CargoWise, Magaya, Shipamax):** Caros (+$3k/mo), lentos de implementar, y NO automatizan la búsqueda activa de info en portales externos; solo procesan lo que tú ya tienes.
- **SaaS Moderno (cargo.one, Wisor, Raft):** Enfocados en ventas/cotizaciones o grandes cuentas.
- **Tu Hueco:** El operador de LATAM/Panamá que necesita automatizar el "trabajo sucio" administrativo a un precio accesible ($50-150). **Nadie está haciendo el flujo de scraping activo + IA + generación de docs personalizados para el mercado SMB.**

---

## 💰 8. Modelo de Negocio y Precios (Tiered/Hybrid)
Cobrar $150 a una empresa de 100 empleados es injusto. El modelo debe escalar con el valor entregado y el costo de IA.

1.  **Plan Solo ($49/mo):** 1 usuario, 30 bookings/mes. Ideal para freelancers.
2.  **Plan Equipo ($149/mo):** Hasta 5 usuarios, 150 bookings/mes. (Escalabilidad horizontal).
3.  **Plan Enterprise (Custom):** +10 usuarios, volumen masivo. Licencia de sitio (Site License).
4.  **Cargos por Uso:** Si se exceden de los bookings mensuales, se cobra un "Overload fee" ($1-$2 por doc) para cubrir costos de Gemini/Infra.

---

## 🗺️ 9. Roadmap de Implementación
1.  **Fase 1:** Script de Playwright para MSC + Extracción con Gemini JSON Schema.
2.  **Fase 2:** API de encriptación y guardado de credenciales.
3.  **Fase 3:** UI de revisión de borrador en Next.js.
4.  **Fase 4:** Motor de plantillas Word -> PDF.
5.  **Fase 5:** Integración con correo y piloto con tu esposa.

---
**Gosen Tech 2026** — *Innovación desde Panamá Oeste para el Mundo.*
