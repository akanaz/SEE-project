import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import LoadingSpinner from './components/LoadingSpinner';
import LanguageSelector from './components/LanguageSelector';
import VoiceControls from './components/VoiceControls';
import MapView from './components/MapView';
import { sendMessage, simplifyConversation, translateText } from './services/api';
import { getNearbyHospitals } from './services/places';
import './App.css';
import { speakText } from "./services/api";

function App() {
  const [chatHistory, setChatHistory] = useState([]);
  const [awaitingFollowup, setAwaitingFollowup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showSimplifyFor, setShowSimplifyFor] = useState(null);
  const [simplifying, setSimplifying] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [mapsData, setMapsData] = useState({});
  const [loadingMap, setLoadingMap] = useState({});
  const chatEndRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  // Extract disease type from response text
  const extractDiseaseType = (responseText) => {
    const diseases = [
      'heart', 'cardiac', 'chest pain', 'hypertension', 'stroke',
      'asthma', 'pneumonia', 'covid', 'cough', 'breathing',
      'migraine', 'epilepsy', 'headache', 'seizure', 'parkinson',
      'fracture', 'bone', 'arthritis', 'joint',
      'gastric', 'ulcer', 'digestive', 'stomach',
      'fever', 'infection', 'sepsis',
      'diabetes', 'glucose',
      'cancer', 'tumor',
      'kidney', 'renal', 'dialysis',
      'liver', 'hepatitis'
    ];

    const lowerText = responseText.toLowerCase();
    for (const disease of diseases) {
      if (lowerText.includes(disease)) {
        return disease.charAt(0).toUpperCase() + disease.slice(1);
      }
    }
    return '';
  };

  // Format medical response with structured sections
  const formatMedicalResponse = (responseText) => {
    const sections = {
      '**Overview**': { icon: '📋' },
      '**Possible Causes**': { icon: '🔍' },
      '**Common Symptoms**': { icon: '⚠️' },
      '**Recommended Actions**': { icon: '✅' },
      '**When to See a Doctor**': { icon: '🏥' },
      '**Medical Disclaimer**': { icon: '⚖️' }
    };

    let formatted = [];
    const lines = responseText.split('\n');
    let currentSection = null;
    let currentContent = [];

    lines.forEach((line) => {
      const lineTrimmed = line.trim();

      for (const [header, meta] of Object.entries(sections)) {
        if (lineTrimmed.includes(header)) {
          if (currentSection && currentContent.length > 0) {
            formatted.push({
              type: 'section',
              header: currentSection.header,
              icon: currentSection.icon,
              content: currentContent.filter((c) => c.trim())
            });
          }
          currentSection = { header, icon: meta.icon };
          currentContent = [];
          return;
        }
      }

      if (lineTrimmed && currentSection) {
        currentContent.push(lineTrimmed);
      }
    });

    if (currentSection && currentContent.length > 0) {
      formatted.push({
        type: 'section',
        header: currentSection.header,
        icon: currentSection.icon,
        content: currentContent.filter((c) => c.trim())
      });
    }

    return formatted.length > 0 ? formatted : null;
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, mapsData]);

  useEffect(() => {
    return () => {
      if (synthRef.current.speaking) {
        synthRef.current.cancel();
      }
    };
  }, []);

  const handleSendMessage = async (message) => {
    const newUserMessage = { role: 'user', content: message, id: Date.now() + '-u' };
    setChatHistory((prev) => [...prev, newUserMessage]);
    setLoading(true);

    try {
      const response = await sendMessage(message, chatHistory, awaitingFollowup);
      let responseText = response.response;

      // Translation for non‑English
      if (selectedLanguage !== 'en') {
        try {
          const translated = await translateText(responseText, selectedLanguage);
          if (translated && translated.translated) {
            responseText = translated.translated;
          }
        } catch (transError) {
          console.error('Translation error:', transError);
        }
      }

      const assistantId = Date.now();
      const extractedDisease = extractDiseaseType(responseText);

      const assistantMessage = {
        role: 'assistant',
        content: responseText,
        id: assistantId,
        isFollowup: response.awaiting_followup,
        diseaseType: extractedDisease,
        formatted: formatMedicalResponse(responseText)
      };

      setChatHistory((prev) => [...prev, assistantMessage]);
      setAwaitingFollowup(response.awaiting_followup);

      // Only fetch hospitals on final answer
      if (!response.awaiting_followup) {
        setShowSimplifyFor(assistantId);
        setLoadingMap((prev) => ({ ...prev, [assistantId]: true }));

        const centerLat = 12.9716;
        const centerLng = 77.5946;

        try {
          // Pass disease to backend and take top‑5 by rating
          const places = await getNearbyHospitals(centerLat, centerLng, extractedDisease);
          const sorted = (places || []).slice().sort(
            (a, b) => (b.rating || 0) - (a.rating || 0)
          );
          const topFive = sorted.slice(0, 5);

          setMapsData((prev) => ({
            ...prev,
            [assistantId]: {
              lat: centerLat,
              lng: centerLng,
              places: topFive,
              diseaseType: extractedDisease
            }
          }));
        } catch (err) {
          console.error('Error fetching nearby hospitals:', err);
          setMapsData((prev) => ({
            ...prev,
            [assistantId]: {
              lat: centerLat,
              lng: centerLng,
              places: [],
              diseaseType: extractedDisease
            }
          }));
        } finally {
          setLoadingMap((prev) => ({ ...prev, [assistantId]: false }));
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'assistant',
        content:
          '⚠️ Sorry, there was an error processing your request. Please try again.',
        id: Date.now(),
        isFollowup: false
      };
      setChatHistory((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSimplify = async (messageId) => {
    setSimplifying(true);
    try {
      const index = chatHistory.findIndex((msg) => msg.id === messageId);
      const messagesToSimplify =
        index >= 0 ? chatHistory.slice(0, index + 1) : chatHistory;
      const response = await simplifyConversation(messagesToSimplify);

      let simplifiedText = response.simplified;

      if (selectedLanguage !== 'en') {
        try {
          const translated = await translateText(simplifiedText, selectedLanguage);
          if (translated && translated.translated) {
            simplifiedText = translated.translated;
          }
        } catch (transError) {
          console.error('Translation error:', transError);
        }
      }

      const simplifiedMessage = {
        role: 'assistant',
        content: `🧒 **Simplified Summary:**\n\n${simplifiedText}`,
        id: Date.now(),
        isSimplified: true
      };
      setChatHistory((prev) => [...prev, simplifiedMessage]);
      setShowSimplifyFor(null);
    } catch (error) {
      console.error('Error simplifying:', error);
    } finally {
      setSimplifying(false);
    }
  };


   

const handleSpeak = async (text) => {
  try {
    setIsSpeaking(true);

    const result = await speakText(text, selectedLanguage);

    if (result.success && result.url) {

      // Build real backend URL
      let base = import.meta.env.VITE_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

      const audioUrl = `${base}${result.url}`;

      console.log("PLAYING AUDIO:", audioUrl); // MUST show http://localhost:8000/chat/audio/...

      const audio = new Audio(audioUrl);
      audio.play();

      audio.onended = () => setIsSpeaking(false);
      audio.onerror = (e) => {
        console.error("Audio Playback Error:", e);
        setIsSpeaking(false);
      };
    } else {
      console.error("TTS failed:", result.error);
      setIsSpeaking(false);
    }
  } catch (error) {
    console.error("TTS error:", error);
    setIsSpeaking(false);
  }
};



  const handleExampleClick = (text) => {
    if (!loading) {
      handleSendMessage(text);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-left">
            <h1>🏥 MEDICORE AI</h1>
            <p>Your AI Medical Assistant</p>
            <small>For educational purposes only – always consult a doctor.</small>
          </div>
          <div className="header-right">
            <LanguageSelector
              selectedLanguage={selectedLanguage}
              onLanguageChange={setSelectedLanguage}
            />
          </div>
        </div>
      </header>

      <main className="chat-section">
        <div className="chat-container">
          <div className="chat-messages">
            {chatHistory.length === 0 && (
              <div className="welcome-message">
                <h2>Welcome to Medicore AI</h2>
                <p>Describe your symptoms or ask a medical question to get started.</p>

                <div className="example-queries">
                  <strong>Try asking:</strong>
                  <ul>
                    <li
                      onClick={() =>
                        handleExampleClick('I have chest pain and shortness of breath')
                      }
                    >
                      "I have chest pain and shortness of breath"
                    </li>
                    <li
                      onClick={() =>
                        handleExampleClick('I have a severe headache and nausea')
                      }
                    >
                      "I have a severe headache and nausea"
                    </li>
                    <li
                      onClick={() =>
                        handleExampleClick('I have been coughing with fever for 3 days')
                      }
                    >
                      "I have been coughing with fever for 3 days"
                    </li>
                  </ul>
                </div>
              </div>
            )}

            {chatHistory.map((msg, index) => {
              const mapInfo = mapsData[msg.id];
              const isLast = index === chatHistory.length - 1;

              return (
                <div key={msg.id || index}>
                  <ChatMessage
                    message={msg}
                    formatted={msg.formatted}
                    onSpeak={handleSpeak}
                    isSpeaking={isSpeaking}
                  />

                  {mapInfo && (
                    <div className="map-section">
                      {loadingMap[msg.id] ? (
                        <div className="map-loading">⏳ Loading nearby medical facilities...</div>
                      ) : (
                        <>
                          <MapView
                            lat={mapInfo.lat}
                            lng={mapInfo.lng}
                            places={mapInfo.places}
                            label={
                              mapInfo.diseaseType
                                ? `Nearby ${mapInfo.diseaseType} facilities`
                                : 'Nearby Medical Locations'
                            }
                          />

                          {mapInfo.places.length > 0 && (
                            <div className="hospital-recs">
                              <h4>Top {mapInfo.places.length} hospitals (by rating)</h4>
                              <ol>
                                {mapInfo.places.map((h, i) => (
                                  <li key={h.place_id || h.name || i}>
                                    <strong>{i + 1}. {h.name}</strong><br />
                                    {h.address}<br />
                                    Rating: {h.rating ?? 'N/A'}
                                  </li>
                                ))}
                              </ol>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}

                  {showSimplifyFor === msg.id && !msg.isSimplified && (
                    <div className="simplify-row">
                      <button
                        className="simplify-btn"
                        onClick={() => handleSimplify(msg.id)}
                        disabled={simplifying}
                      >
                        {simplifying ? 'Simplifying...' : 'Simplify this explanation'}
                      </button>
                    </div>
                  )}

                  {isLast && <div ref={chatEndRef} />}
                </div>
              );
            })}

            {loading && (
              <div className="loading-row">
                <LoadingSpinner />
              </div>
            )}
          </div>

          <div className="input-row">
            <ChatInput onSend={handleSendMessage} disabled={loading} />
            <VoiceControls
              onSend={handleSendMessage}
              disabled={loading}
              selectedLanguage={selectedLanguage}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
