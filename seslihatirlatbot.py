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
        await log_kaydi_ekle(await calculate_timestamp(), "Kullanıcı", "Mesaj", user_input)
        
        # Analiz mesajı kontrolü ve kayıt
        await mesaj_analiz_ayikla_ve_kaydet(user_input)
        
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
        await log_kaydi_ekle(await calculate_timestamp(), "Bot", "Hatırlatma", "Hatırlatma sesli gönderildi")
        
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
def zaman_al():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def calculate_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def mesaj_analiz_ayikla_ve_kaydet(user_text: str):
    if "/" in user_text:
        kategori, aciklama = [k.strip() for k in user_text.split("/", 1)]
        await analiz_kaydi_ekle(
            zaman=zaman_al(),
            kategori=kategori,
            alt_baslik="",  # daha sonra AI ile çıkarılabilir
            aciklama=aciklama,
            sure=None  # sonra eklenecek
        )

async def log_kaydi_ekle(zaman: str, kaynak: str, mesaj_turu: str, icerik: str):
    dosya = "log_kayitlari.xlsx"
    yeni_kayit = pd.DataFrame([[zaman, kaynak, mesaj_turu, icerik]], 
                               columns=["Zaman", "Kaynak", "Mesaj Türü", "İçerik"])
    
    if os.path.exists(dosya):
        eski_kayitlar = pd.read_excel(dosya)
        tum_kayitlar = pd.concat([eski_kayitlar, yeni_kayit], ignore_index=True)
    else:
        tum_kayitlar = yeni_kayit

    tum_kayitlar.to_excel(dosya, index=False)

async def analiz_kaydi_ekle(zaman: str, kategori: str, alt_baslik: str, aciklama: str, sure: int = None):
    dosya = "analiz_verisi.xlsx"
    yeni_kayit = pd.DataFrame([[zaman, kategori, alt_baslik, aciklama, sure]], 
                               columns=["Zaman", "Kategori", "Alt Başlık", "Açıklama", "Süre (dk)"])
    
    if os.path.exists(dosya):
        eski_kayitlar = pd.read_excel(dosya)
        tum_kayitlar = pd.concat([eski_kayitlar, yeni_kayit], ignore_index=True)
    else:
        tum_kayitlar = yeni_kayit

    tum_kayitlar.to_excel(dosya, index=False)

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
