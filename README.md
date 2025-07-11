# 🤖 Sesli Hatırlatma Botu

Bu bot LM Studio veya Gemini AI ile çalışan Türkçe sesli asistan botudur.

## 🚀 Kurulum

### 1. Repository'yi klonlayın
```bash
git clone <repo-url>
cd ka
```

### 2. Gerekli paketleri yükleyin
```bash
pip install -r requirements.txt
```

### 3. Konfigürasyon ayarları
```bash
# config.example.py dosyasını kopyalayın
cp config.example.py config.py

# config.py dosyasını kendi değerlerinizle düzenleyin:
# - BOT_TOKEN: @BotFather'dan alacağınız token
# - USER_CHAT_ID: Telegram kullanıcı ID'niz
# - AI_SERVICE: "gemini" veya "lmstudio" 
# - GEMINI_API_KEY: Google AI Studio'dan API key (Gemini için)
# - FFMPEG_PATH: FFmpeg dosyasının tam yolu
```

### 4. AI Servisi Seçimi

#### **Seçenek A: Gemini AI (Önerilen)** 🌟
- [Google AI Studio](https://aistudio.google.com/)'ya gidin
- API key oluşturun
- `config.py` içinde `AI_SERVICE = "gemini"` yapın
- `GEMINI_API_KEY` değerini doldurun

#### **Seçenek B: LM Studio**
- LM Studio'yu indirin ve kurun
- openhermes-2.5-mistral-7b modelini yükleyin
- Server'ı port 1234'te başlatın
- `config.py` içinde `AI_SERVICE = "lmstudio"` yapın

### 5. Botu çalıştırın
```bash
python bot.py
```

## 📁 Proje Yapısı

```
📁 ka/
├── bot.py                # Ana bot dosyası
├── config.py             # Kişisel ayarlar (Git'e dahil değil)
├── config.example.py     # Örnek konfigürasyon dosyası
├── handlers.py           # Telegram mesaj işleyicileri
├── scheduler.py          # Zamanlı hatırlatma sistemi
├── ai/
│   ├── __init__.py       # AI paketi init dosyası
│   └── gemini.py         # Gemini AI entegrasyonu
├── kayıt/
│   ├── logger.py         # Excel kayıt fonksiyonları
│   └── zaman.py          # Zaman yardımcı fonksiyonları
└── requirements.txt      # Gerekli Python paketleri
```

## 🔧 Özellikler

- ✅ **Çoklu AI Desteği** (Gemini AI / LM Studio)
- ✅ Metin mesajlarına AI yanıtı
- ✅ Sesli mesaj desteği (Whisper + Edge TTS)
- ✅ Zamanlı hatırlatmalar (08:00-20:00 arası)
- ✅ Excel'e otomatik kayıt
- ✅ Aktivite kategorileme sistemi

## 📝 Kullanım

### Komutlar:
- `/sesli` - Test sesli mesajı (hangi AI kullanıldığını gösterir)

### Mesaj formatları:
- Normal mesaj: AI ile sohbet
- Sesli mesaj: Otomatik yazıya çevrilir ve yanıtlanır
- Kategori mesajı: `kategori/alt_başlık/açıklama` (Excel'e kaydedilir)

## 🤖 AI Servisleri

### **Gemini AI** (Google)
- ✅ Ücretsiz kullanım limitli
- ✅ Kurulum gerektirmez
- ✅ Güçlü dil modeli
- ✅ Hızlı yanıt

### **LM Studio** (Lokal)
- ✅ Tamamen offline çalışır
- ✅ Veriler dışarı çıkmaz
- ⚠️ Güçlü donanım gerektirir
- ⚠️ Manuel kurulum

## 🛡️ Güvenlik

**config.py dosyası .gitignore'da bulunur ve hassas bilgiler içerir:**
- Bot token'ı
- Kullanıcı ID'si
- Gemini API key'i
- Dosya yolları

**Lütfen config.py dosyasını paylaşmayın!** 