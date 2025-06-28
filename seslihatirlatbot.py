from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from gtts import gTTS
from pydub import AudioSegment
import os
import logging
import whisper
import requests

# Telegram Bot Token
BOT_TOKEN = "7701882660:AAGgYXamK4EQsG1I_UT8eI90xzqIL_B87so"

# 1️⃣ LM Studio model ismi
LMSTUDIO_MODEL_NAME = "openhermes-2.5-mistral-7b"

# LM Studio API endpoint'i - Yerel AI sunucusu adresi
LMSTUDIO_API_URL = "http://127.0.0.1:1234/v1/chat/completions"

# ffmpeg yolu - Ses dosyası dönüştürme için gerekli
AudioSegment.converter = r"C:\Users\dilru\Downloads\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"

# Logging ayarları - Hata takibi için
logging.basicConfig(level=logging.INFO)

# 1️⃣ Komut: /sesli → bot sesli mesaj atar
async def sesli_mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Gönderilecek metni belirle
        text = "Merhaba! Bu ilk sesli mesajım. Şu an neyle meşgulsün?"
        
        # Metni ses dosyasına çevir (Türkçe)
        tts = gTTS(text, lang='tr')
        tts.save("mesaj.mp3")
        
        # MP3'ü OGG formatına çevir (Telegram ses formatı)
        ses = AudioSegment.from_mp3("mesaj.mp3")
        ses.export("mesaj.ogg", format="ogg", codec="libopus")
        
        # Ses dosyasını Telegram'a gönder
        with open("mesaj.ogg", "rb") as voice_file:
            await update.message.reply_voice(voice=voice_file)
        
        # Geçici dosyaları temizle
        os.remove("mesaj.mp3")
        os.remove("mesaj.ogg")
    except Exception as e:
        logging.error(f"Hata oluştu: {e}")
        await update.message.reply_text("Sesli mesaj gönderilemedi.")

# Metin mesajlarını işle ve AI'dan cevap al
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Kullanıcı mesajını al
        user_input = update.message.text
        
        # LM Studio'ya gönderilecek veriyi hazırla
        payload = {
            "model": LMSTUDIO_MODEL_NAME,
            "messages": [
                {"role": "system", "content": "Sen kullanıcıya dostça yardımcı olan bir kişisel asistansın."},
                {"role": "user", "content": user_input}
            ]
        }
        
        # AI'dan cevap al
        response = requests.post(LMSTUDIO_API_URL, json=payload)
        response_data = response.json()
        cevap = response_data["choices"][0]["message"]["content"]
        
        # Cevabı kullanıcıya gönder
        await update.message.reply_text(cevap)
    except Exception as e:
        logging.error(f"Mesaj gönderim hatası: {e}")
        await update.message.reply_text("Cevap alınamadı.")

# Sesli mesajları yazıya çevir ve AI'dan cevap al
async def sesli_yanit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Ses dosyasını al ve indir
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive("input.ogg")
        
        # OGG'yi MP3'e çevir (Whisper MP3 bekler)
        ses = AudioSegment.from_ogg("input.ogg")
        ses.export("input.mp3", format="mp3")
        
        # Whisper modelini yükle ve sesi yazıya çevir
        model = whisper.load_model("base")
        result = model.transcribe("input.mp3", language="tr")
        metin = result["text"]
        
        # Yazıya çevrilen metni göster
        await update.message.reply_text(f"📄 Yazıya çevrildi:\n{metin}")

        # Yazıya çevrilen metni LM Studio’ya gönder
        payload = {
            "model": LMSTUDIO_MODEL_NAME,
            "messages": [
                {"role": "system", "content": "Sen dostça yardımcı olan bir asistansın."},
                {"role": "user", "content": metin}
            ]
        }
        
        # AI'dan cevap al ve gönder
        response = requests.post(LMSTUDIO_API_URL, json=payload)
        yanit = response.json()["choices"][0]["message"]["content"]
        
        # Metin cevabını gönder
        await update.message.reply_text(f"🤖 Cevap:\n{yanit}")
        
        # Sesli cevabı da gönder
        await yaniti_sesle_gonder(update, yanit)

        # Geçici dosyaları temizle
        os.remove("input.ogg")
        os.remove("input.mp3")

    except Exception as e:
        logging.error(f"Sesli yanıt hatası: {e}")
        await update.message.reply_text("Sesli mesaj işlenemedi.")

# LM cevabını sesli mesaja çevirip Telegram'a gönder
async def yaniti_sesle_gonder(update, text):
    try:
        tts = gTTS(text=text, lang="tr")
        tts.save("cevap.mp3")
        ses = AudioSegment.from_mp3("cevap.mp3")
        ses.export("cevap.ogg", format="ogg", codec="libopus")

        with open("cevap.ogg", "rb") as voice_file:
            await update.message.reply_voice(voice=voice_file)

        os.remove("cevap.mp3")
        os.remove("cevap.ogg")
    except Exception as e:
        logging.error(f"Yanıtı sese çevirme hatası: {e}")
        await update.message.reply_text("Sesli yanıt oluşturulamadı.")

# 4️ Bot Başlat
if __name__ == "__main__":
    # Bot uygulamasını oluştur
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Komut işleyicilerini ekle
    app.add_handler(CommandHandler("sesli", sesli_mesaj))  # /sesli komutu
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))  # Metin mesajları
    app.add_handler(MessageHandler(filters.VOICE, sesli_yanit))  # Sesli mesajlar
    
    print("🤖 Bot LM Studio ile hazır...")
    app.run_polling()
