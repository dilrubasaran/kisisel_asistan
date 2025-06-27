from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from gtts import gTTS
from pydub import AudioSegment
import os
import logging
import whisper
import openai

# 🔐 OpenAI API anahtarını buraya yaz
openai.api_key = "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"

# ffmpeg yolu
AudioSegment.converter = "C:\\Users\\dilru\\Downloads\\ffmpeg-7.1.1-essentials_build\\ffmpeg-7.1.1-essentials_build\\bin\\ffmpeg.exe"

# Logging aktif
logging.basicConfig(level=logging.INFO)

import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = "7701882660:AAGgYXamK4EQsG1I_UT8eI90xzqIL_B87so"
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "model": "local-model",  # LM Studio’da adı neyse o (genelde “local-model” olur)
        "messages": [
            {"role": "system", "content": "Sen bir kişisel asistan botsun."},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.7
    }

    response = requests.post("http://127.0.0.1:1234", headers=headers, json=data)
    response_data = response.json()
    cevap = response_data['choices'][0]['message']['content']

    await update.message.reply_text(cevap)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

print("🤖 LM Studio destekli bot hazır...")
app.run_polling()


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

# 2️⃣ Kullanıcıdan gelen sesli mesajı yakala → yazıya çevir → GPT-4 ile cevapla
async def sesli_yanit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice = update.message.voice
        if not voice:
            await update.message.reply_text("Sesli mesaj bekleniyor.")
            return

        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive("input.ogg")
        await update.message.reply_text("Sesli mesaj alındı. Yazıya çevriliyor...")

        ses = AudioSegment.from_ogg("input.ogg")
        ses.export("input.mp3", format="mp3")

        model = whisper.load_model("base")
        result = model.transcribe("input.mp3", language="tr")
        metin = result["text"]
        await update.message.reply_text(f"📄 Yazıya çevrildi:\n\n{metin}")

        # GPT-4 ile yanıt
        gpt_cevap = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Sen bir kişisel asistansın. Dostça ve kısa cevaplar ver."},
                {"role": "user", "content": metin}
            ]
        )["choices"][0]["message"]["content"]

        await update.message.reply_text(f"🤖 Asistan:\n{gpt_cevap}")

        # Geçici dosyaları temizle
        os.remove("input.ogg")
        os.remove("input.mp3")

    except Exception as e:
        logging.error(f"Sesli yanıt sırasında hata: {e}")
        await update.message.reply_text("Sesli mesaj işlenirken bir hata oluştu.")

# 3️⃣ Bot başlatma
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Komut /sesli → bot sesli mesaj atar
    app.add_handler(CommandHandler("sesli", sesli_mesaj))

    # Kullanıcının gönderdiği sesli mesajı yakala
    app.add_handler(MessageHandler(filters.VOICE, sesli_yanit))

    print("🤖 Bot sesli mesaj için hazır...")
    app.run_polling()
