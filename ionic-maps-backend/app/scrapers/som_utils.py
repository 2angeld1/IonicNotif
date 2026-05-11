"""
Utilidades para Set-of-Mark (SOM) en Playwright.
Inyecta JavaScript en la página para numerar visualmente los elementos interactivos,
penetrando Shadow DOMs e IFrames.
"""

SOM_JS = """
() => {
    if (document.getElementById('som-container')) return;

    let counter = 1;
    const somContainer = document.createElement('div');
    somContainer.id = 'som-container';
    somContainer.style.position = 'absolute';
    somContainer.style.top = '0';
    somContainer.style.left = '0';
    somContainer.style.width = '100%';
    somContainer.style.height = '100%';
    somContainer.style.pointerEvents = 'none';
    somContainer.style.zIndex = '999999';
    document.body.appendChild(somContainer);

    const validTags = ['INPUT', 'BUTTON', 'SELECT', 'TEXTAREA', 'A'];
    
    function isValidTarget(el) {
        if (!el || !el.tagName) return false;
        const tag = el.tagName.toUpperCase();
        if (validTags.includes(tag)) {
            if (tag === 'INPUT' && el.type === 'hidden') return false;
            return true;
        }
        const role = el.getAttribute('role');
        if (role === 'button' || role === 'combobox' || role === 'searchbox') return true;
        // Identificar Web Components personalizados (ej. Maersk <mc-input>)
        if (tag.startsWith('MC-')) return true;
        return false;
    }

    function processElement(el, offsetX = 0, offsetY = 0) {
        if (isValidTarget(el)) {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            
            if (rect.width >= 5 && rect.height >= 5 && style.visibility !== 'hidden' && style.display !== 'none' && style.opacity !== '0') {
                const scrollX = window.scrollX || window.pageXOffset;
                const scrollY = window.scrollY || window.pageYOffset;
                
                // Etiquetamos el elemento real
                el.setAttribute('data-som-id', counter);
                
                const tag = document.createElement('div');
                tag.innerText = `[${counter}]`;
                tag.style.position = 'absolute';
                tag.style.top = `${rect.top + scrollY + offsetY - 10}px`;
                tag.style.left = `${rect.left + scrollX + offsetX - 10}px`;
                tag.style.backgroundColor = 'red';
                tag.style.color = 'white';
                tag.style.fontSize = '14px';
                tag.style.fontWeight = 'bold';
                tag.style.padding = '2px 4px';
                tag.style.border = '2px solid black';
                tag.style.zIndex = '999999';
                tag.style.boxShadow = '0 0 5px rgba(0,0,0,0.5)';
                
                somContainer.appendChild(tag);
                counter++;
            }
        }

        // Penetrar Shadow DOM (Maersk)
        if (el.shadowRoot) {
            el.shadowRoot.querySelectorAll('*').forEach(child => processElement(child, offsetX, offsetY));
        }
        
        // Penetrar IFrames del mismo origen (COSCO)
        if (el.tagName === 'IFRAME') {
            try {
                const rect = el.getBoundingClientRect();
                if (el.contentDocument && el.contentDocument.body) {
                    el.contentDocument.body.querySelectorAll('*').forEach(child => 
                        processElement(child, offsetX + rect.left, offsetY + rect.top)
                    );
                }
            } catch (e) {
                // Dominio cruzado bloqueado (Seguridad del navegador)
            }
        }
    }

    // Iniciar escaneo masivo desde el documento principal
    document.querySelectorAll('*').forEach(el => processElement(el));
}
"""
