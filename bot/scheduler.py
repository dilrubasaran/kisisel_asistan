# ⏰ Zamanlı Hatırlatma Sistemi

import edge_tts
from pydub import AudioSegment
import os, logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

from config.config import (
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

def job_listesi_log():
    """Aktif job'ların listesini log'a yazdırır"""
    jobs = scheduler.get_jobs()
    logging.info(f"📋 Aktif job sayısı: {len(jobs)}")
    for job in jobs:
        logging.info(f"   - {job.id}: {job.next_run_time}")

async def hatirlatma_gonder():
    """Hatırlatma mesajını gönderir"""
    global app
    if app is None:
        logging.error("❌ App henüz başlatılmamış!")
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
        
        logging.info(f"✅ Hatırlatma başarıyla gönderildi: {datetime.now().strftime('%H:%M')}")
    except Exception as e:
        logging.error(f"Hatırlatma gönderiminde hata: {e}")

async def sor_gece_devam():
    """Gün bitimi için kullanıcıya devam edip etmeyeceğini sorar"""
    global app
    if app is None:
        logging.error("❌ App başlatılmamış (gece devam sorusu).")
        return

    try:
        metin = " Bugünkü plan sona erdi Dilruba. Bu akşam çalışmaya devam edecek misin?\nLütfen saat belirt (örn: 22:30) ya da 'Hayır' yaz."
        communicate = edge_tts.Communicate(metin, voice=VOICE_NAME)
        await communicate.save("gece.mp3")
        ses = AudioSegment.from_mp3("gece.mp3")
        ses.export("gece.ogg", format="ogg", codec="libopus")
        with open("gece.ogg", "rb") as voice_file:
            await app.bot.send_voice(chat_id=USER_CHAT_ID, voice=voice_file)
        await app.bot.send_message(chat_id=USER_CHAT_ID, text=metin)

        await log_kaydi_ekle(await calculate_timestamp(), "Bot", "Gece Sorgu", "Günün sonunda çalışma devam sorusu gönderildi.")

        os.remove("gece.mp3")
        os.remove("gece.ogg")
        
        logging.info(f"🌙 Gece devam sorusu gönderildi: {datetime.now().strftime('%H:%M')}")
    except Exception as e:
        logging.error(f"Gece devam sorusu gönderilemedi: {e}")

async def otomatik_gunluk_rapor():
    """Otomatik günlük rapor oluşturur ve gönderir"""
    global app
    if app is None:
        logging.error("❌ App başlatılmamış (günlük rapor).")
        return
    
    try:
        from analysis.daily_report import gunluk_rapor_olustur
        
        # Rapor oluştur
        sonuc = gunluk_rapor_olustur()
        
        # Kullanıcıya mesaj gönder
        await app.bot.send_message(
            chat_id=USER_CHAT_ID, 
            text=f"📊 **Otomatik Günlük Rapor**\n\n{sonuc}"
        )
        
        # PDF varsa gönder
        if "gunluk_rapor_" in sonuc and ".pdf" in sonuc:
            try:
                pdf_yolu = sonuc.split("data/reports/")[1].split("\n")[0] if "data/reports/" in sonuc else None
                if pdf_yolu:
                    with open(f"data/reports/{pdf_yolu}", "rb") as pdf_file:
                        await app.bot.send_document(
                            chat_id=USER_CHAT_ID, 
                            document=pdf_file, 
                            filename=pdf_yolu,
                            caption="📊 Günlük Rapor PDF"
                        )
            except Exception as pdf_hatasi:
                logging.warning(f"PDF gönderim hatası: {pdf_hatasi}")
        
        # Log kaydet
        await log_kaydi_ekle(await calculate_timestamp(), "Bot", "Otomatik Rapor", "Günlük rapor otomatik oluşturuldu ve gönderildi")
        
        logging.info(f"✅ Otomatik günlük rapor gönderildi: {datetime.now().strftime('%H:%M')}")
        
    except Exception as e:
        logging.error(f"Otomatik günlük rapor hatası: {e}")
        await app.bot.send_message(
            chat_id=USER_CHAT_ID, 
            text=f"❌ Otomatik günlük rapor oluşturulamadı: {str(e)}"
        )

async def otomatik_haftalik_rapor():
    """Otomatik haftalık rapor oluşturur ve gönderir"""
    global app
    if app is None:
        logging.error("❌ App başlatılmamış (haftalık rapor).")
        return
    
    try:
        from analysis.weekly_report import haftalik_rapor_olustur
        
        # Rapor oluştur
        sonuc = haftalik_rapor_olustur()
        
        # Kullanıcıya mesaj gönder
        await app.bot.send_message(
            chat_id=USER_CHAT_ID, 
            text=f"📅 **Otomatik Haftalık Rapor**\n\n{sonuc}"
        )
        
        # PDF varsa gönder
        if "haftalik_rapor_" in sonuc and ".pdf" in sonuc:
            try:
                pdf_yolu = sonuc.split("data/reports/")[1].split("\n")[0] if "data/reports/" in sonuc else None
                if pdf_yolu:
                    with open(f"data/reports/{pdf_yolu}", "rb") as pdf_file:
                        await app.bot.send_document(
                            chat_id=USER_CHAT_ID, 
                            document=pdf_file, 
                            filename=pdf_yolu,
                            caption="📅 Haftalık Rapor PDF"
                        )
            except Exception as pdf_hatasi:
                logging.warning(f"PDF gönderim hatası: {pdf_hatasi}")
        
        # Log kaydet
        await log_kaydi_ekle(await calculate_timestamp(), "Bot", "Otomatik Rapor", "Haftalık rapor otomatik oluşturuldu ve gönderildi")
        
        logging.info(f"✅ Otomatik haftalık rapor gönderildi: {datetime.now().strftime('%H:%M')}")
        
    except Exception as e:
        logging.error(f"Otomatik haftalık rapor hatası: {e}")
        await app.bot.send_message(
            chat_id=USER_CHAT_ID, 
            text=f"❌ Otomatik haftalık rapor oluşturulamadı: {str(e)}"
        )

async def start_scheduler():
    """Zamanlayıcıyı başlatır"""
    # Normal çalışma saatleri hatırlatmaları
    for hour in range(REMINDER_START_HOUR, REMINDER_END_HOUR):
        for minute in (0, 30):
            scheduler.add_job(hatirlatma_gonder, 'cron', hour=hour, minute=minute, id=f"hat_{hour}_{minute}", replace_existing=True)
    
    # Gece devam sorusu (20:00'de)
    scheduler.add_job(sor_gece_devam, 'cron', hour=20, minute=0, id="gece_devam_sor", replace_existing=True)
    
    # 📊 Otomatik günlük rapor (her gece 23:30'da)
    scheduler.add_job(otomatik_gunluk_rapor, 'cron', hour=23, minute=30, id="otomatik_gunluk_rapor", replace_existing=True)
    
    # 📅 Otomatik haftalık rapor (her Pazar 23:00'da)
    scheduler.add_job(otomatik_haftalik_rapor, 'cron', day_of_week=6, hour=23, minute=0, id="otomatik_haftalik_rapor", replace_existing=True)
    
    logging.info(f"🕒 Zamanlı mesajlar aktif ({REMINDER_START_HOUR}:00-{REMINDER_END_HOUR}:00 arası her {REMINDER_INTERVAL_MINUTES} dakikada).")
    logging.info(f"🌙 Gece devam sorusu aktif (20:00'de)")
    logging.info(f"📊 Otomatik günlük rapor aktif (her gece 23:30'da)")
    logging.info(f"📅 Otomatik haftalık rapor aktif (her Pazar 23:00'da)")
    
    # Job listesini log'a yazdır
    job_listesi_log()

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