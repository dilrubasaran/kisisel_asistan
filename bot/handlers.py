# 🤖 Telegram Handler Fonksiyonları

import edge_tts
from telegram import Update
from telegram.ext import ContextTypes
from pydub import AudioSegment
import os, logging, whisper, requests
import asyncio
import re
from datetime import datetime

from config.config import (
    LMSTUDIO_MODEL_NAME, LMSTUDIO_API_URL, VOICE_NAME, FFMPEG_PATH, AI_SERVICE, USER_CHAT_ID
)
from kayıt.logger import log_kaydi_ekle, mesaj_analiz_ayikla_ve_kaydet
from kayıt.zaman import calculate_timestamp
from ai.gemini import gemini_chat_with_system
from analysis.daily_report import gunluk_rapor_olustur
from analysis.weekly_report import haftalik_rapor_olustur

# AudioSegment ayarı
AudioSegment.converter = FFMPEG_PATH

# Geçici olarak kullanıcıya özel saat tutulacak
devam_suresi = {}

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

async def test_gece_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test için gece devam sorusunu manuel gönderir"""
    from bot.scheduler import sor_gece_devam
    await sor_gece_devam()
    await update.message.reply_text("🧪 Test gece devam sorusu gönderildi!")

async def test_gunluk_rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test için otomatik günlük rapor gönderir"""
    from bot.scheduler import otomatik_gunluk_rapor
    await update.message.reply_text("🧪 Test otomatik günlük rapor başlatılıyor...")
    await otomatik_gunluk_rapor()

async def test_haftalik_rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test için otomatik haftalık rapor gönderir"""
    from bot.scheduler import otomatik_haftalik_rapor
    await update.message.reply_text("🧪 Test otomatik haftalık rapor başlatılıyor...")
    await otomatik_haftalik_rapor()

async def gece_cevap_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gece çalışma devam cevabını işler"""
    try:
        user_id = update.message.chat_id
        if user_id != USER_CHAT_ID:
            return  # Başkasından geldiyse geç

        mesaj = update.message.text.strip().lower()

        # 1. Eğer kullanıcı "hayır", "bitirdim" gibi yanıt verdiyse
        if any(kelime in mesaj for kelime in ["hayır", "bitirdim", "yok", "devam etmeyeceğim", "kapatalım"]):
            await context.bot.send_message(chat_id=user_id, text="Anlaşıldı, bu akşam için hatırlatmaları durduruyorum. İyi akşamlar 🌙")
            await log_kaydi_ekle(await calculate_timestamp(), "Bot", "Gece Devam", "Kullanıcı devam etmeyecek.")
            return

        # 2. Kullanıcı saat belirttiyse (örn. 22:30, 10.30, 23)
        saat_eslesme = re.search(r'(\d{1,2})[:\.]?(\d{0,2})', mesaj)
        if saat_eslesme:
            saat = int(saat_eslesme.group(1))
            dakika = int(saat_eslesme.group(2)) if saat_eslesme.group(2) else 0
            if 0 <= saat <= 23 and 0 <= dakika < 60:
                simdi = datetime.now()
                bugun = simdi.date()
                hedef = datetime.combine(bugun, datetime.min.time()).replace(hour=saat, minute=dakika)

                logging.info(f"🌙 Gece devam: Şimdi={simdi.strftime('%H:%M')}, Hedef={hedef.strftime('%H:%M')}")

                # Saat geçmişse: yarına ait olmasın, sınırla
                if hedef <= simdi:
                    await context.bot.send_message(chat_id=user_id, text="Saat geçmiş görünüyor, lütfen gelecekte bir saat belirt.")
                    return

                # Scheduler'ı import et
                from bot.scheduler import scheduler, hatirlatma_gonder, job_listesi_log
                
                job_sayisi = 0
                # Her 30 dakikada bir hatırlatmalar kur
                temp_time = simdi.replace(second=0, microsecond=0)
                while temp_time < hedef:
                    # Sonraki 30 dakikalık dilime git
                    if temp_time.minute < 30:
                        temp_time = temp_time.replace(minute=30)
                    else:
                        temp_time = temp_time.replace(minute=0, hour=temp_time.hour + 1)
                    
                    if temp_time <= hedef:
                        job_id = f"extra_{temp_time.hour}_{temp_time.minute}"
                        scheduler.add_job(
                            hatirlatma_gonder,
                            'date',
                            run_date=temp_time,
                            id=job_id,
                            replace_existing=True
                        )
                        job_sayisi += 1
                        logging.info(f"📅 Gece job eklendi: {job_id} → {temp_time.strftime('%H:%M')}")

                logging.info(f"✅ Toplam {job_sayisi} adet gece hatırlatma job'u eklendi")
                # Güncellenmiş job listesini göster
                job_listesi_log()
                
                await context.bot.send_message(chat_id=user_id, text=f"⏳ Harika! Bugün {saat:02d}:{dakika:02d}'ye kadar hatırlatmalar devam edecek.")
                await log_kaydi_ekle(await calculate_timestamp(), "Bot", "Gece Devam", f"Kullanıcı saat verdi: {saat:02d}:{dakika:02d}")
                return

        # Eğer anlamsız bir şey yazdıysa:
        await context.bot.send_message(chat_id=user_id, text="Lütfen saat belirt (örn: 22:30) veya 'Hayır' yaz.")
    except Exception as e:
        logging.error(f"Gece cevap işleme hatası: {e}")
        await context.bot.send_message(chat_id=user_id, text="Yanıt işlenemedi.")

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
        
        # Önce gece cevap handler'ını dene
        if update.message.chat_id == USER_CHAT_ID:
            # Gece saat cevaplarını kontrol et
            mesaj_lower = user_input.strip().lower()
            if (any(kelime in mesaj_lower for kelime in ["hayır", "bitirdim", "yok", "devam etmeyeceğim", "kapatalım"]) or
                re.search(r'(\d{1,2})[:\.]?(\d{0,2})', mesaj_lower)):
                await gece_cevap_handler(update, context)
                return
        
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

# 📊 Rapor komutları
async def gunluk_rapor_komut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Günlük rapor komutu"""
    try:
        # Sadece belirli kullanıcıdan al
        if update.message.chat_id != USER_CHAT_ID:
            await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
            return
        
        await update.message.reply_text("📊 Günlük rapor hazırlanıyor...")
        
        # Günlük rapor oluştur
        sonuc = gunluk_rapor_olustur()
        
        # Yanıtı gönder
        await update.message.reply_text(sonuc)
        
        # PDF varsa gönder
        if "gunluk_rapor_" in sonuc and ".pdf" in sonuc:
            # PDF dosya yolunu çıkar
            pdf_yolu = sonuc.split("data/reports/")[1].split("\n")[0] if "data/reports/" in sonuc else None
            if pdf_yolu:
                try:
                    with open(f"data/reports/{pdf_yolu}", "rb") as pdf_file:
                        await update.message.reply_document(pdf_file, filename=pdf_yolu)
                except Exception as pdf_hatasi:
                    logging.warning(f"PDF gönderim hatası: {pdf_hatasi}")
        
        # Komutu kaydet
        await log_kaydi_ekle(await calculate_timestamp(), "Kullanıcı", "Komut", "/gunluk_rapor")
        
    except Exception as e:
        logging.error(f"Günlük rapor komutu hatası: {e}")
        await update.message.reply_text(f"❌ Günlük rapor oluşturulamadı: {str(e)}")

async def haftalik_rapor_komut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Haftalık rapor komutu"""
    try:
        # Sadece belirli kullanıcıdan al
        if update.message.chat_id != USER_CHAT_ID:
            await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
            return
        
        await update.message.reply_text("📅 Haftalık rapor hazırlanıyor...")
        
        # Haftalık rapor oluştur
        sonuc = haftalik_rapor_olustur()
        
        # Yanıtı gönder
        await update.message.reply_text(sonuc)
        
        # PDF varsa gönder
        if "haftalik_rapor_" in sonuc and ".pdf" in sonuc:
            # PDF dosya yolunu çıkar
            pdf_yolu = sonuc.split("data/reports/")[1].split("\n")[0] if "data/reports/" in sonuc else None
            if pdf_yolu:
                try:
                    with open(f"data/reports/{pdf_yolu}", "rb") as pdf_file:
                        await update.message.reply_document(pdf_file, filename=pdf_yolu)
                except Exception as pdf_hatasi:
                    logging.warning(f"PDF gönderim hatası: {pdf_hatasi}")
        
        # Komutu kaydet
        await log_kaydi_ekle(await calculate_timestamp(), "Kullanıcı", "Komut", "/haftalik_rapor")
        
    except Exception as e:
        logging.error(f"Haftalık rapor komutu hatası: {e}")
        await update.message.reply_text(f"❌ Haftalık rapor oluşturulamadı: {str(e)}") 