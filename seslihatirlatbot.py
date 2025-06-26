from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from gtts import gTTS
from pydub import AudioSegment
import os
import logging

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "7701882660:AAGgYXamK4EQsG1I_UT8eI90xzqIL_B87so"

async def sesli_mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = "Merhaba! Bu ilk sesli mesajım. Şu an neyle meşgulsün?"
        
        tts = gTTS(text, lang='tr')
        tts.save("mesaj.mp3")

        # FFMPEG yolu
        AudioSegment.converter = "C:\\Users\\dilru\\Downloads\\ffmpeg-7.1.1-essentials_build\\ffmpeg-7.1.1-essentials_build\\bin\\ffmpeg.exe"
        ses = AudioSegment.from_mp3("mesaj.mp3")
        ses.export("mesaj.ogg", format="ogg", codec="libopus")

        with open("mesaj.ogg", "rb") as voice_file:
            await update.message.reply_voice(voice=voice_file)

        os.remove("mesaj.mp3")
        os.remove("mesaj.ogg")

    except Exception as e:
        logging.error(f"Hata oluştu: {e}")
        await update.message.reply_text("Sesli mesaj gönderilemedi.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("sesli", sesli_mesaj))
    print("🤖 Bot sesli mesaj için hazır...")
    app.run_polling()
