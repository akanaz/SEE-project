import React from 'react';
import ReactMarkdown from 'react-markdown';

const ChatMessage = ({ message, formatted, onSpeak, isSpeaking }) => {
  const isUser = message.role === 'user';

  if (!isUser && formatted && formatted.length > 0) {
    return (
      <div className="message assistant-message">
        <div className="message-content">
          <div className="message-text">
            {formatted.map((section, idx) => (
              <div key={idx} className="medical-response">
                <div className="response-section-heading">
                  <span className="section-icon">{section.icon}</span>
                  <span>{section.header.replace(/\*\*/g, '')}</span>
                </div>
                <div className="response-section-content">
                  {section.content.map((line, i) => (
                    <ReactMarkdown key={i}>{line}</ReactMarkdown>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <button
            className={`speak-btn-inline ${isSpeaking ? 'speaking' : ''}`}
            onClick={() => onSpeak(message.content)}
            title={isSpeaking ? 'Stop speaking' : 'Speak this response'}
          >
            🔊
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-content">
        <div className="message-text">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        {!isUser && (
          <button
            className={`speak-btn-inline ${isSpeaking ? 'speaking' : ''}`}
            onClick={() => onSpeak(message.content)}
            title={isSpeaking ? 'Stop speaking' : 'Speak this response'}
          >
            🔊
          </button>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
