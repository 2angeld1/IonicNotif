import React, { useRef, useEffect } from 'react';
import { 
  IonModal, IonContent, IonIcon 
} from '@ionic/react';
import { sendOutline, micOutline, closeOutline } from 'ionicons/icons';
import { useAIChat } from '../hooks/useAIChat';

interface AIChatModalProps {
  isOpen: boolean;
  onClose: () => void;
  userLocation: { lat: number; lng: number } | null;
  onNavigateTo: (destination: string) => void;
  onSearchPlaces: (query: string) => void;
}

const AIChatModal: React.FC<AIChatModalProps> = (props) => {
  const {
      messages,
      inputText,
      setInputText,
      isProcessing,
      isListening,
      handleSend,
      handleMicClick
  } = useAIChat(props);

  const { isOpen, onClose } = props;
  const inputRef = useRef<HTMLInputElement>(null);
  const contentRef = useRef<HTMLIonContentElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 500);
      scrollToBottom();
    }
  }, [isOpen, messages]);

  const scrollToBottom = () => {
    contentRef.current?.scrollToBottom(300);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSend();
  };

  return (
    <IonModal 
        isOpen={isOpen} 
        onDidDismiss={onClose} 
        initialBreakpoint={0.6} 
        breakpoints={[0, 0.6, 0.9]}
        className="rounded-t-2xl"
    >
      <div className="flex flex-col h-full bg-gray-50">
        {/* Header */}
        <div className="bg-white p-4 flex items-center justify-between border-b border-gray-100 shadow-sm z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center text-white shadow-md animate-pulse-slow">
              <span className="text-xl">🤖</span>
            </div>
            <div>
                <h2 className="font-bold text-gray-800">Calitin AI</h2>
                <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                    <span className="text-xs text-gray-500 font-medium">En línea</span>
                </div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 bg-gray-100 rounded-full text-gray-500 hover:bg-gray-200 transition-colors">
            <IonIcon icon={closeOutline} />
          </button>
        </div>

        {/* Chat Content */}
        <IonContent ref={contentRef} className="bg-gray-50">
           <div className="flex flex-col p-4 gap-4">
              {messages.map(msg => (
                  <div key={msg.id} className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className={`max-w-[85%] p-4 rounded-2xl shadow-sm text-sm font-medium leading-relaxed ${
                          msg.sender === 'user' 
                          ? 'bg-blue-600 text-white rounded-tr-none' 
                          : 'bg-white text-gray-700 rounded-tl-none border border-gray-100'
                      }`}>
                          {msg.text}
                      </div>
                      
                      {/* Acciones sugeridas */}
                      {msg.actions && msg.actions.length > 0 && (
                          <div className="mt-2 flex gap-2">
                              {msg.actions.map((action, idx) => (
                                  <button 
                                    key={idx}
                                    onClick={action.action}
                                    className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-xl shadow-lg hover:bg-indigo-700 transition-all active:scale-95 text-xs font-bold"
                                  >
                                      {action.icon && <IonIcon icon={action.icon} />}
                                      {action.label}
                                  </button>
                              ))}
                          </div>
                      )}
                  </div>
              ))}
              {isProcessing && (
                  <div className="flex items-start">
                      <div className="bg-white p-4 rounded-2xl rounded-tl-none shadow-sm flex gap-1">
                          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                      </div>
                  </div>
              )}
           </div>
        </IonContent>

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-gray-100 pb-8">
            <div className={`flex items-center gap-2 bg-gray-100 p-2 rounded-full border transition-all ${isListening ? 'border-red-500 ring-2 ring-red-100' : 'border-gray-200 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100'}`}>
                <input 
                    ref={inputRef}
                    type="text" 
                    value={inputText}
                    onChange={e => setInputText(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder={isListening ? "Escuchando..." : "Escribe algo..."}
                    className="flex-1 bg-transparent px-4 py-2 outline-none text-gray-700 font-medium placeholder:text-gray-400"
                />
                
                {inputText.trim() ? (
                    <button onClick={handleSend} className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center shadow-md hover:bg-blue-700 transition-colors">
                        <IonIcon icon={sendOutline} />
                    </button>
                ) : (
                    <button 
                        onClick={handleMicClick}
                        className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                            isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-gray-200 text-gray-500 hover:bg-gray-300'
                        }`}
                    >
                        <IonIcon icon={micOutline} />
                    </button>
                )}
            </div>
        </div>
      </div>
    </IonModal>
  );
};

export default AIChatModal;
