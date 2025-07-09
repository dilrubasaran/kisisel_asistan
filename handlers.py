# 🤖 Telegram Handler Fonksiyonları

import edge_tts
from telegram import Update
from telegram.ext import ContextTypes
from pydub import AudioSegment
import os, logging, whisper, requests
import asyncio

from config import (
    LMSTUDIO_MODEL_NAME, LMSTUDIO_API_URL, VOICE_NAME, FFMPEG_PATH
)
from kayıt.logger import log_kaydi_ekle, mesaj_analiz_ayikla_ve_kaydet
from kayıt.zaman import calculate_timestamp

# AudioSegment ayarı
AudioSegment.converter = FFMPEG_PATH

# 🎤 /sesli komutu
async def sesli_mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = "Merhaba! Bu ilk sesli mesajım. Şu an neyle meşgulsün?"
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
        
        payload = {
            "model": LMSTUDIO_MODEL_NAME,
            "messages": [
                {"role": "system", "content": "Sen kullanıcıya dostça yardımcı olan bir kişisel asistansın."},
                {"role": "user", "content": user_input}
            ]
        }
        
        response = requests.post(LMSTUDIO_API_URL, json=payload)
        response_data = response.json()
        cevap = response_data["choices"][0]["message"]["content"]
        await update.message.reply_text(cevap)
        
        # Bot yanıtını kaydet
        await log_kaydi_ekle(await calculate_timestamp(), "Bot", "Yanıt", cevap)
        
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
        
        payload = {
            "model": LMSTUDIO_MODEL_NAME,
            "messages": [
                {"role": "system", "content": "Sen dostça yardımcı olan bir asistansın."},
                {"role": "user", "content": metin}
            ]
        }
        response = requests.post(LMSTUDIO_API_URL, json=payload)
        yanit = response.json()["choices"][0]["message"]["content"]
        await update.message.reply_text(f"🤖 Cevap:\n{yanit}")
        await yaniti_sesle_gonder(update, yanit)
        
        # Bot yanıtını kaydet
        await log_kaydi_ekle(await calculate_timestamp(), "Bot", "Yanıt", yanit)
        
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