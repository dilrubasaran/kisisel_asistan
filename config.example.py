# ⚙️ Konfigürasyon Ayarları - ÖRNEK DOSYASI
# Bu dosyayı config.py olarak kopyalayın ve gerçek değerlerle doldurun

# Bot ayarları
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # @BotFather'dan alacağınız token
USER_CHAT_ID = 123456789  # Telegram kullanıcı ID'niz

# AI Servisi Seçimi ("lmstudio" veya "gemini")
AI_SERVICE = "gemini"  # Hangi AI servisini kullanacağınızı seçin

# LM Studio ayarları
LMSTUDIO_MODEL_NAME = "openhermes-2.5-mistral-7b"  # Kullandığınız model adı
LMSTUDIO_API_URL = "http://127.0.0.1:1234/v1/chat/completions"  # LM Studio API URL

# Gemini AI ayarları
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Google AI Studio'dan alacağınız API key
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Ses ayarları
VOICE_NAME = "tr-TR-EmelNeural"  # Microsoft Edge TTS ses modeli

# Dosya yolları
FFMPEG_PATH = r"C:\path\to\your\ffmpeg.exe"  # FFmpeg dosyasının tam yolu

# Hatırlatma ayarları
REMINDER_START_HOUR = 8  # Hatırlatma başlangıç saati
REMINDER_END_HOUR = 20   # Hatırlatma bitiş saati
REMINDER_INTERVAL_MINUTES = 30  # Hatırlatma aralığı (dakika)

# Excel dosya adları
LOG_FILE = "log_kayitlari.xlsx"
ANALYSIS_FILE = "analiz_verisi.xlsx"

# Analiz ayarları
DEFAULT_DURATION_MINUTES = 30  # Varsayılan aktivite süresi (dakika) 