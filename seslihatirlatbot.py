import edge_tts
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from pydub import AudioSegment
import os, logging, whisper, requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pandas as pd
from datetime import datetime
import asyncio

# ⚙️ Ayarlar
BOT_TOKEN = "7701882660:AAGgYXamK4EQsG1I_UT8eI90xzqIL_B87so"
USER_CHAT_ID = 7534575038
LMSTUDIO_MODEL_NAME = "openhermes-2.5-mistral-7b"
LMSTUDIO_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
AudioSegment.converter = r"C:\\Users\\dilru\\Downloads\\ffmpeg-7.1.1-essentials_build\\ffmpeg-7.1.1-essentials_build\\bin\\ffmpeg.exe"

logging.basicConfig(level=logging.INFO)

# Global app değişkeni
app = None

# 🎤 /sesli komutu
async def sesli_mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = "Merhaba! Bu ilk sesli mesajım. Şu an neyle meşgulsün?"
        communicate = edge_tts.Communicate(text, voice="tr-TR-EmelNeural")
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
        await yaniti_excel_kaydet(await calculate_timestamp(), user_input, "Kullanıcı Mesajı")
        
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
        await yaniti_excel_kaydet(await calculate_timestamp(), cevap, "Bot Yanıtı")
        
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
        await yaniti_excel_kaydet(await calculate_timestamp(), f"[Sesli] {metin}", "Kullanıcı Mesajı")
        
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
        await yaniti_excel_kaydet(await calculate_timestamp(), yanit, "Bot Yanıtı")
        
        os.remove("input.ogg")
        os.remove("input.mp3")
    except Exception as e:
        logging.error(f"Sesli yanıt hatası: {e}")
        await update.message.reply_text("Sesli mesaj işlenemedi.")

async def yaniti_sesle_gonder(update, text):
    try:
        communicate = edge_tts.Communicate(text, voice="tr-TR-EmelNeural")
        await communicate.save("cevap.mp3")
        ses = AudioSegment.from_mp3("cevap.mp3")
        ses.export("cevap.ogg", format="ogg", codec="libopus")
        await update.message.reply_voice(open("cevap.ogg", "rb"))
        os.remove("cevap.mp3")
        os.remove("cevap.ogg")
    except Exception as e:
        logging.error(f"Yanıtı sese çevirme hatası: {e}")
        await update.message.reply_text("Sesli yanıt oluşturulamadı.")

# 📅 Zamanlı gönderim
scheduler = AsyncIOScheduler()

async def hatirlatma_gonder():
    global app
    if app is None:
        logging.error("App henüz başlatılmamış!")
        return
    try:
        metin = " Şu an ne yapıyorsun?"
        communicate = edge_tts.Communicate(metin, voice="tr-TR-EmelNeural")
        await communicate.save("hatirlatma.mp3")
        ses = AudioSegment.from_mp3("hatirlatma.mp3")
        ses.export("hatirlatma.ogg", format="ogg", codec="libopus")
        with open("hatirlatma.ogg", "rb") as voice_file:
            await app.bot.send_voice(chat_id=USER_CHAT_ID, voice=voice_file)
        
        # Hatırlatma gönderimini kaydet
        await yaniti_excel_kaydet(await calculate_timestamp(), "Hatırlatma sesli gönderildi", "Hatırlatma")
        
        os.remove("hatirlatma.mp3")
        os.remove("hatirlatma.ogg")
    except Exception as e:
        logging.error(f"Hatırlatma gönderiminde hata: {e}")

async def start_scheduler():
    for hour in range(8, 20):
        for minute in (0, 30):
            scheduler.add_job(hatirlatma_gonder, 'cron', hour=hour, minute=minute, id=f"hat_{hour}_{minute}", replace_existing=True)
    logging.info("🕒 Zamanlı mesajlar aktif (08:00-20:00 arası her 30 dakikada).")

async def scheduler_init(application):
    global app
    app = application
    loop = asyncio.get_running_loop()
    scheduler.configure(event_loop=loop)
    if not scheduler.running:
        scheduler.start()
        await start_scheduler()
        print("✅ Zamanlayıcı başlatıldı!")

# 📊 Excel'e kaydetme fonksiyonları
async def calculate_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def yaniti_excel_kaydet(zaman, icerik, tur):
    dosya = "yanitlar.xlsx"
    df = pd.DataFrame([[zaman, tur, icerik]], columns=["Zaman", "Tür", "Mesaj"])
    if os.path.exists(dosya):
        df_old = pd.read_excel(dosya)
        df = pd.concat([df_old, df], ignore_index=True)
    df.sort_values("Zaman", inplace=True)  # Kronolojik sıraya sok
    df.to_excel(dosya, index=False)

# 🚀 Bot başlatma
if __name__ == "__main__":
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(scheduler_init)
        .build()
    )

    app.add_handler(CommandHandler("sesli", sesli_mesaj))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))
    app.add_handler(MessageHandler(filters.VOICE, sesli_yanit))

    print("🤖 Bot LM Studio ile hazır...")
    app.run_polling()
