# ⏰ Zamanlı Hatırlatma Sistemi

import edge_tts
from pydub import AudioSegment
import os, logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import (
    USER_CHAT_ID, VOICE_NAME, FFMPEG_PATH,
    REMINDER_START_HOUR, REMINDER_END_HOUR, REMINDER_INTERVAL_MINUTES
)
from kayıt.logger import log_kaydi_ekle
from kayıt.zaman import calculate_timestamp

# Global değişkenler
scheduler = AsyncIOScheduler()
app = None

# AudioSegment ayarı
AudioSegment.converter = FFMPEG_PATH

async def hatirlatma_gonder():
    """Hatırlatma mesajını gönderir"""
    global app
    if app is None:
        logging.error("App henüz başlatılmamış!")
        return
    try:
        metin = " Hocam Merhaba! Şu an ne yapıyorsun? Nasıl gidiyor?"
        communicate = edge_tts.Communicate(metin, voice=VOICE_NAME)
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
    """Zamanlayıcıyı başlatır"""
    for hour in range(REMINDER_START_HOUR, REMINDER_END_HOUR):
        for minute in (0, 30):
            scheduler.add_job(hatirlatma_gonder, 'cron', hour=hour, minute=minute, id=f"hat_{hour}_{minute}", replace_existing=True)
    logging.info(f"🕒 Zamanlı mesajlar aktif ({REMINDER_START_HOUR}:00-{REMINDER_END_HOUR}:00 arası her {REMINDER_INTERVAL_MINUTES} dakikada).")

async def scheduler_init(application):
    """Zamanlayıcıyı initialize eder"""
    global app
    app = application
    loop = asyncio.get_running_loop()
    scheduler.configure(event_loop=loop)
    if not scheduler.running:
        scheduler.start()
        await start_scheduler()
        print("✅ Zamanlayıcı başlatıldı!") 