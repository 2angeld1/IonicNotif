import { useState, useCallback } from 'react';
import { navigateOutline, searchOutline } from 'ionicons/icons';
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
  onSearchPlaces: (query: string) => void;
  onClose: () => void;
  userLocation: { lat: number; lng: number } | null;
}

export const useAIChat = ({ onNavigateTo, onSearchPlaces, onClose, userLocation }: UseAIChatProps) => {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', text: '¡Hola! Soy Calitin 🤖. ¿A dónde quieres ir hoy?', sender: 'agent' }
  ]);
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);

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
            agentMsg.actions = [{
                label: 'Ver Resultados',
                icon: searchOutline,
                action: () => {
                    onSearchPlaces(data.query);
                    onClose();
                }
            }];
        }
        setMessages(prev => [...prev, agentMsg]);
      } else {
        throw new Error("No response from agent");
      }

    } catch (error) {
       setMessages(prev => [...prev, { 
           id: Date.now().toString(), 
           text: 'Lo siento, tuve un problema de conexión. ¿Puedes repetirlo?', 
           sender: 'agent' 
       }]);
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
