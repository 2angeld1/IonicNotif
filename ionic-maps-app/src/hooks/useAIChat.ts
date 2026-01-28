import { useState, useCallback } from 'react';
import { navigateOutline, locationOutline } from 'ionicons/icons';
import { parseAgentMessage } from '../services/apiService';

// Definición manual para Web Speech API
interface SpeechRecognitionEvent extends Event {
  results: {
    [index: number]: {
      [index: number]: {
        transcript: string;
      };
    };
  };
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

declare global {
  interface Window {
    webkitSpeechRecognition: any;
  }
}

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'agent';
  actions?: {
    label: string;
    icon?: string;
    action: () => void;
  }[];
}

interface UseAIChatProps {
  onNavigateTo: (destination: string) => void;
  onSearchPlaces: (query: string, count: number) => Promise<any[]>;
  onReportIncident: (type: string) => void;
  onCheckWeather: (location: string) => Promise<string>;
  onPlaceDetails: (place: string) => Promise<string>;
  onClose: () => void;
  userLocation: { lat: number; lng: number } | null;
}

export const useAIChat = ({
  onNavigateTo,
  onSearchPlaces,
  onReportIncident,
  onCheckWeather,
  onPlaceDetails,
  onClose,
  userLocation
}: UseAIChatProps) => {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', text: '¡Hola! Soy Calitin 🤖. ¿A dónde quieres ir hoy?', sender: 'agent' }
  ]);
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);

  // Importar iconos dinámicamente o usar los que ya están
  // Asumimos que están importados arriba, si no, hay que añadir import

  // Función para Text-to-Speech
  const speak = useCallback((text: string) => {
    if (!('speechSynthesis' in window)) return;

    // Cancelar cualquier speech anterior y limpiar emojis para que no los lea literalmente
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'es-ES';
    utterance.pitch = 0.8; // Voz más grave (masculina)
    utterance.rate = 1.0;

    // Intentar seleccionar una voz masculina preferida si está disponible
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v =>
      v.lang.startsWith('es') && (
        v.name.toLowerCase().includes('pablo') ||
        v.name.toLowerCase().includes('male') ||
        v.name.toLowerCase().includes('google español')
      )
    );
    if (preferredVoice) utterance.voice = preferredVoice;

    window.speechSynthesis.speak(utterance);
  }, []);

  const handleSend = async () => {
    if (!inputText.trim()) return;

    const userMsg: Message = { 
        id: Date.now().toString(), 
        text: inputText, 
        sender: 'user' 
    };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsProcessing(true);

    try {
      // Usar el servicio centralizado
      const result = await parseAgentMessage(userMsg.text, userLocation);

      if (result) {
        const { intent, message, data } = result;
        
        const agentMsg: Message = {
          id: (Date.now() + 1).toString(),
          text: message,
          sender: 'agent',
          actions: []
        };

        if (intent === 'navigate') {
            agentMsg.actions = [{
                label: 'Trazar Ruta',
                icon: navigateOutline,
                action: () => {
                    onNavigateTo(data.destination);
                    onClose();
                }
            }];
        } else if (intent === 'search_places') {
          // Buscamos los lugares y esperamos los resultados para mostrarlos en el chat
          const count = data.count || 4;
          const results = await onSearchPlaces(data.query, count);

          if (results && results.length > 0) {
            const queryText = data.query || 'lugares';
            agentMsg.text = `Encontré estos ${queryText} cerca de tu ubicación. ¿A cuál te gustaría ir? 📍`;
            agentMsg.actions = results.map((place: any) => ({
              label: `${place.display_name.split(',')[0]} - Trazar Ruta`,
              icon: locationOutline,
              action: () => {
                onNavigateTo(place.display_name);
                onClose();
              }
            }));
          } else {
            agentMsg.text = `Lo siento, no encontré "${data.query}" abiertos en este momento. 😕`;
          }
        } else if (intent === 'report_incident') {
            agentMsg.actions = [{
              label: `Confirmar Reporte de ${data.type === 'police' ? 'Policía' : data.type === 'accident' ? 'Accidente' : 'Incidente'}`,
              icon: locationOutline, // Podría ser alertCircleOutline
                action: () => {
                  onReportIncident(data.type);
                  const confirmText = '✅ Reporte enviado a la comunidad. ¡Gracias por avisar!';
                  setMessages(prev => [...prev, {
                    id: Date.now().toString(),
                    text: confirmText,
                    sender: 'agent'
                  }]);
                  speak('Reporte enviado a la comunidad. Gracias.');
                }
            }];
        } else if (intent === 'check_weather') {
          // Procesar clima asíncronamente y responder
          const weatherInfo = await onCheckWeather(data.location);
          agentMsg.text = `${message}\n\n${weatherInfo}`;
        } else if (intent === 'place_details') {
          const placeInfo = await onPlaceDetails(data.place);
          agentMsg.text = `${message}\n\n${placeInfo}`;
        }

        setMessages(prev => [...prev, agentMsg]);
        speak(agentMsg.text);
      } else {
        throw new Error("No response from agent");
      }

    } catch (error) {
      const errorMsg = 'Lo siento, tuve un problema de conexión. ¿Puedes repetirlo?';
       setMessages(prev => [...prev, { 
           id: Date.now().toString(), 
         text: errorMsg, 
           sender: 'agent' 
       }]);
      speak(errorMsg);
    } finally {
        setIsProcessing(false);
    }
  };

  const handleMicClick = useCallback(() => {
    if (!window.webkitSpeechRecognition) {
      alert("Tu navegador no soporta reconocimiento de voz. Intenta usar Chrome.");
      return;
    }

    const recognition = new window.webkitSpeechRecognition();
    recognition.lang = 'es-ES';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = event.results[0][0].transcript;
      setInputText(transcript);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error("Error speech recognition", event.error);
      setIsListening(false);
    };

    recognition.start();
  }, []);

  return {
    messages,
    inputText,
    setInputText,
    isProcessing,
    isListening,
    handleSend,
    handleMicClick
  };
};
