# 🤖 Telegram Handler Fonksiyonları

import edge_tts
from telegram import Update
from telegram.ext import ContextTypes
from pydub import AudioSegment
import os, logging, whisper, requests
import asyncio

from config import (
    LMSTUDIO_MODEL_NAME, LMSTUDIO_API_URL, VOICE_NAME, FFMPEG_PATH, AI_SERVICE
)
from kayıt.logger import log_kaydi_ekle, mesaj_analiz_ayikla_ve_kaydet
from kayıt.zaman import calculate_timestamp
from ai.gemini import gemini_chat_with_system

# AudioSegment ayarı
AudioSegment.converter = FFMPEG_PATH

def get_ai_response(system_message: str, user_message: str) -> str:
    """AI servisinden yanıt alır (LM Studio veya Gemini)"""
    try:
        if AI_SERVICE == "gemini":
            # Gemini kullan
            return gemini_chat_with_system(system_message, user_message)
        else:
            # LM Studio kullan (varsayılan)
            payload = {
                "model": LMSTUDIO_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
            }
            response = requests.post(LMSTUDIO_API_URL, json=payload)
            response_data = response.json()
            return response_data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"AI yanıt hatası ({AI_SERVICE}): {e}")
        return f"⚠️ {AI_SERVICE.title()} servisinden cevap alınamadı."

# 🎤 /sesli komutu
async def sesli_mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = f"Merhaba! Bu ilk sesli mesajım. Şu an neyle meşgulsün? (AI: {AI_SERVICE.title()})"
        communicate = edge_tts.Communicate(text, voice=VOICE_NAME)
        await communicate.save("mesaj.mp3")
        ses = AudioSegment.from_mp3("mesaj.mp3")
        ses.export("mesaj.ogg", format="ogg", codec="libopus")
        await update.message.reply_voice(open("mesaj.ogg", "rb"))
        os.remove("mesaj.mp3")
        os.remove("mesaj.ogg")
    except Exception as e:
        logging.error(f"Hata oluştu: {e}")
        await update.message.reply_text("Sesli mesaj gönderilemedi.")

# ✉️ Metin mesajlarını AI'ya gönder
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_input = update.message.text
        
        # Kullanıcının mesajını kaydet
        await log_kaydi_ekle(await calculate_timestamp(), "Kullanıcı", "Mesaj", user_input)
        
        # Analiz mesajı kontrolü ve kayıt (hata olursa devam et)
        try:
            await mesaj_analiz_ayikla_ve_kaydet(user_input)
        except Exception as analiz_hatasi:
            logging.warning(f"Analiz kaydında hata (devam ediliyor): {analiz_hatasi}")
        
        # AI servisinden yanıt al
        system_message = "Sen kullanıcıya dostça yardımcı olan bir kişisel asistansın."
        cevap = get_ai_response(system_message, user_input)
        
        await update.message.reply_text(cevap)
        
        # Bot yanıtını kaydet
        await log_kaydi_ekle(await calculate_timestamp(), "Bot", f"Yanıt ({AI_SERVICE.title()})", cevap)
        
    except Exception as e:
        logging.error(f"Mesaj gönderim hatası: {e}")
        await update.message.reply_text("Cevap alınamadı.")

# 🎧 Sesli → yazı → AI → yazı+ses
async def sesli_yanit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive("input.ogg")
        ses = AudioSegment.from_ogg("input.ogg")
        ses.export("input.mp3", format="mp3")
        model = whisper.load_model("base")
        result = model.transcribe("input.mp3", language="tr")
        metin = result["text"]
        
        # Kullanıcının sesli mesajını kaydet
        await log_kaydi_ekle(await calculate_timestamp(), "Kullanıcı", "Sesli Mesaj", f"[Sesli] {metin}")
        
        await update.message.reply_text(f"📄 Yazıya çevrildi:\n{metin}")
        
        # AI servisinden yanıt al
        system_message = "Sen dostça yardımcı olan bir asistansın."
        yanit = get_ai_response(system_message, metin)
        
        await update.message.reply_text(f"🤖 Cevap ({AI_SERVICE.title()}):\n{yanit}")
        await yaniti_sesle_gonder(update, yanit)
        
        # Bot yanıtını kaydet
        await log_kaydi_ekle(await calculate_timestamp(), "Bot", f"Yanıt ({AI_SERVICE.title()})", yanit)
        
        os.remove("input.ogg")
        os.remove("input.mp3")
    except Exception as e:
        logging.error(f"Sesli yanıt hatası: {e}")
        await update.message.reply_text("Sesli mesaj işlenemedi.")

async def yaniti_sesle_gonder(update, text):
    """Verilen metni sesli mesaj olarak gönderir"""
    try:
        communicate = edge_tts.Communicate(text, voice=VOICE_NAME)
        await communicate.save("cevap.mp3")
        ses = AudioSegment.from_mp3("cevap.mp3")
        ses.export("cevap.ogg", format="ogg", codec="libopus")
        await update.message.reply_voice(open("cevap.ogg", "rb"))
        os.remove("cevap.mp3")
        os.remove("cevap.ogg")
    except Exception as e:
        logging.error(f"Yanıtı sese çevirme hatası: {e}")
        await update.message.reply_text("Sesli yanıt oluşturulamadı.") 