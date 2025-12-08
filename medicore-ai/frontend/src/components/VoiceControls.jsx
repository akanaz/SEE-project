// VoiceControls.jsx
import React, { useState, useRef, useEffect } from 'react';

const VoiceControls = ({ onSend, disabled, selectedLanguage }) => {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;

      const languageCodes = {
        en: 'en-US',
        es: 'es-ES',
        fr: 'fr-FR',
        de: 'de-DE',
        zh: 'zh-CN',
        ar: 'ar-SA',
        hi: 'hi-IN',
        ta: 'ta-IN',
        te: 'te-IN',
        mr: 'mr-IN',
        bn: 'bn-IN',
        kn: 'kn-IN',
      };

      recognitionRef.current.lang =
        languageCodes[selectedLanguage] || 'en-US';

      recognitionRef.current.onresult = (event) => {
        const speechToText = event.results[0][0].transcript;
        onSend(speechToText);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [selectedLanguage, onSend]);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert(
        'Speech recognition is not supported in your browser. Please use Chrome or Edge.'
      );
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  return (
    <button
      type="button"
      className={`voice-mic-btn ${isListening ? 'listening' : ''}`}
      onClick={toggleListening}
      disabled={disabled}
      title={isListening ? 'Stop listening' : 'Tap to speak'}
    >
      🎤
    </button>
  );
};

export default VoiceControls;
