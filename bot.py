# 🤖 Sesli Hatırlatma Botu - Ana Dosya

import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config.config import BOT_TOKEN
from bot.handlers import sesli_mesaj, mesaj, sesli_yanit, test_gece_sorgu
from bot.scheduler import scheduler_init

# Logging ayarı
logging.basicConfig(level=logging.INFO)

# 🚀 Bot başlatma
if __name__ == "__main__":
    # Uygulama oluştur
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(scheduler_init)
        .build()
    )

    # Handler'ları ekle
    app.add_handler(CommandHandler("sesli", sesli_mesaj))
    app.add_handler(CommandHandler("test_gece", test_gece_sorgu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))
    app.add_handler(MessageHandler(filters.VOICE, sesli_yanit))

    print("🤖 Bot hazır...")
    print("📋 Kullanılabilir komutlar:")
    print("   /sesli - Test sesli mesajı gönder")
    print("   /test_gece - Test gece devam sorusu gönder")
    print("💬 Metin mesajı gönder veya sesli mesaj gönder")
    print("⏰ Hatırlatmalar: 08:00-20:00 arası her 30 dakikada")
    print("🌙 Gece devam sorusu: 20:00'de (saat belirt veya 'Hayır' yaz)")
    
    # Botu çalıştır
    app.run_polling() 