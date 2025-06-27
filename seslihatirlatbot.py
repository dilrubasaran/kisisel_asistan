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

# 2️⃣ LM Studio API endpoint'i
LMSTUDIO_API_URL = "http://127.0.0.1:1234/v1/chat/completions"

# ffmpeg yolu
AudioSegment.converter = r"C:\Users\dilru\Downloads\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"

# Logging
logging.basicConfig(level=logging.INFO)

# 1️⃣ Komut: /sesli → bot sesli mesaj atar
async def sesli_mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = "Merhaba! Bu ilk sesli mesajım. Şu an neyle meşgulsün?"
        tts = gTTS(text, lang='tr')
        tts.save("mesaj.mp3")
        ses = AudioSegment.from_mp3("mesaj.mp3")
        ses.export("mesaj.ogg", format="ogg", codec="libopus")
        with open("mesaj.ogg", "rb") as voice_file:
            await update.message.reply_voice(voice=voice_file)
        os.remove("mesaj.mp3")
        os.remove("mesaj.ogg")
    except Exception as e:
        logging.error(f"Hata oluştu: {e}")
        await update.message.reply_text("Sesli mesaj gönderilemedi.")

# 2️⃣ Metin mesajlarını LM Studio’ya gönder
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_input = update.message.text
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
    except Exception as e:
        logging.error(f"Mesaj gönderim hatası: {e}")
        await update.message.reply_text("Cevap alınamadı.")

# 3️⃣ Sesli mesajları yazıya çevir → LM Studio’ya gönder
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
        await update.message.reply_text(f"📄 Yazıya çevrildi:\n{metin}")

        # LM Studio’ya gönder
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

        os.remove("input.ogg")
        os.remove("input.mp3")

    except Exception as e:
        logging.error(f"Sesli yanıt hatası: {e}")
        await update.message.reply_text("Sesli mesaj işlenemedi.")

# 4️⃣ Bot Başlat
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("sesli", sesli_mesaj))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))
    app.add_handler(MessageHandler(filters.VOICE, sesli_yanit))
    print("🤖 Bot LM Studio ile hazır...")
    app.run_polling()
