# 🚢 Mega-Blueprint: SaaS de Automatización Logística (Caitlyn Logistics)

## 📝 1. Visión del Problema y Solución
- **El Dolor:** Los operadores logísticos pierden entre 30-60 minutos por booking haciendo copy-paste manual entre portales de navieras, sistemas de clientes, y plantillas de Word. Además, los errores humanos en declaraciones de aduanas resultan en multas costosas y retrasos.
- **La Solución:** Un "Agente IA" (Caitlyn) que orqueste la extracción, validación cruzada y generación de documentos en un flujo de **3 clicks**, actuando como un filtro de seguridad contra errores.

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

## 📦 7. Módulos Especializados (Add-ons)

### A. Módulo Aduanero (Prioridad: ALTA) 🛡️
*   **Función:** Validación automática de declaraciones de aduana (SICEP/SIGA).
*   **Valor:** Caitlyn actúa como un "Auditor IA". Compara la factura comercial con la declaración para detectar discrepancias en códigos arancelarios, pesos o valores antes de la sumisión.
*   **Dolor que cura:** Evita multas por errores tipográficos y retrasos en puerto por datos incorrectos.

### B. Cotizador Inteligente (Prioridad: Media) 📈
*   **Función:** Scraping simultáneo de tarifas "Spot" en múltiples navieras para una ruta específica.
*   **Valor:** Genera una tabla comparativa de costos y márgenes de ganancia en segundos.
*   **Dolor que cura:** Elimina la pérdida de tiempo buscando precios en 5 sitios web distintos para responder a un cliente.

---

## 📊 8. Competencia y Oportunidad de Mercado
- **Enterprise (CargoWise, Magaya, Shipamax):** Caros (+$3k/mo), lentos de implementar, y NO automatizan la búsqueda activa de info en portales externos; solo procesan lo que tú ya tienes.
- **SaaS Moderno (cargo.one, Wisor, Raft):** Enfocados en ventas/cotizaciones o grandes cuentas.
- **Tu Hueco:** El operador de LATAM/Panamá que necesita automatizar el "trabajo sucio" administrativo a un precio accesible ($50-150). **Nadie está haciendo el flujo de scraping activo + IA + generación de docs personalizados para el mercado SMB.**

---

## 💰 9. Modelo de Negocio y Precios (Value-Based Tiers)

### 🥉 Tier Starter ($49/mo) - "El Operador"
*   **Ideal para:** Freelancers o agencias micro.
*   **Incluye:** 
    *   Automatización de Bookings básica (1 naviera a la vez).
    *   Límite de 30 documentos/mes.
    *   Generación de PDF estándar.

### 🥈 Tier Pro ($149/mo) - "La Agencia Eficiente" 🚀
*   **Ideal para:** Agencias de carga pymes (3-10 personas).
*   **Incluye:** 
    *   **Procesamiento en Paralelo (N por minuto):** Caitlyn abre múltiples hilos.
    *   **Cotizador Inteligente:** Comparativa de tarifas Spot integrada.
    *   **Lectura de Emails:** Caitlyn detecta confirmaciones en el Inbox automáticamente.
    *   Límite de 200 documentos/mes.

### 🥇 Tier Enterprise ($499+/mo) - "El Hub Logístico" 🛡️
*   **Ideal para:** Grandes agencias o departamentos logísticos corporativos.
*   **Incluye:** 
    *   **Módulo Aduanero (Auditor IA):** Validación contra multas incluida.
    *   **Whitelabel:** Documentos con branding premium y correos desde dominio propio.
    *   **Usuarios Ilimitados:** Ideal para equipos de 20+ personas.
    *   **Prioridad de Procesamiento:** Tus agentes de Playwright corren en servidores dedicados.

---

## 🗺️ 9. Roadmap de Implementación
1.  **Fase 1:** Script de Playwright para MSC + Extracción con Gemini JSON Schema.
2.  **Fase 2:** API de encriptación y guardado de credenciales.
3.  **Fase 3:** UI de revisión de borrador en Next.js.
4.  **Fase 4:** Motor de plantillas Word -> PDF.
5.  **Fase 5:** Integración con correo y piloto con tu esposa.

---
**Gosen Tech 2026** — *Innovación desde Panamá Oeste para el Mundo.*
