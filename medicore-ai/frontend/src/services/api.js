import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ------------- MAIN CHAT -----------------
export const sendMessage = async (message, history, awaiting) => {
  const response = await api.post("/chat/message", {
    message: message,
    chat_history: history,
    awaiting_followup: awaiting,
  });
  return response.data;
};

// ------------- SIMPLIFY -----------------
export const simplifyConversation = async (history) => {
  const response = await api.post("/chat/simplify", {
    chat_history: history,
  });
  return response.data;
};

// ------------- TRANSLATE -----------------
export const translateText = async (text, language) => {
  const response = await api.post("/chat/translate", {
    text,
    language,
  });
  return response.data;
};

// ------------- TEXT TO SPEECH (gTTS) -----------------
export const speakText = async (text, lang) => {
  const response = await api.post("/chat/speak", { text, lang });
  return response.data;
};

// ------------- HEALTH CHECK -----------------
export const healthCheck = async () => {
  const response = await api.get("/health");
  return response.data;
};

export default api;
