# 🤖 Gemini AI API Entegrasyonu

import requests
import logging
from config import GEMINI_API_KEY, GEMINI_API_URL

SYSTEM_INSTRUCTION = (
    "Sen kısa ve öz cevaplar veren kişisel asistansın. "
    "Kullanıcı '/Kategori/Proje/Açıklama' formatında mesaj atarsa: "
    "1) Anlayışla karşıla 2) O konuda 2-3 pratik öneri ver. "
    "Normal mesajlarda asistan gibi davran. KISA yanıtlar ver."
)

def gemini_api_chat(prompt: str) -> str:
    """Gemini API ile sohbet fonksiyonu"""
    headers = {
        "Content-Type": "application/json"
    }

    params = {
        "key": GEMINI_API_KEY
    }
    data = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=data)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logging.error(f"Gemini API hatası: {e}")
        return "⚠️ Gemini'den cevap alınamadı."

def gemini_chat_with_system(system_message: str, user_message: str) -> str:
    """Sistem mesajı ile Gemini sohbeti"""
    # Gemini için sistem mesajını kullanıcı mesajına dahil edelim
    full_prompt = f"Sistem: {system_message}\n\nKullanıcı: {user_message}"
    return gemini_api_chat(full_prompt) 