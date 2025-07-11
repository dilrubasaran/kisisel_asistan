# 📄 Görsel Ağırlıklı PDF Rapor Oluşturucu

from fpdf import FPDF
import os

def turkce_temizle(metin: str) -> str:
    """Türkçe karakterleri ASCII'ye kapsamlı şekilde çevirir"""
    if not metin:
        return ""
    
    # Türkçe karakter dönüşüm tablosu (ASCII safe)
    donusum = {
        'ç': 'c', 'Ç': 'C',
        'ğ': 'g', 'Ğ': 'G', 
        'ı': 'i', 'I': 'I',
        'ö': 'o', 'Ö': 'O',
        'ş': 's', 'Ş': 'S',
        'ü': 'u', 'Ü': 'U'
    }
    
    # Karakterleri değiştir
    for tr_char, en_char in donusum.items():
        metin = metin.replace(tr_char, en_char)
    
    # ASCII olmayan karakterleri kaldır
    try:
        metin = metin.encode('ascii', 'ignore').decode('ascii')
    except:
        pass
    
    return metin

class GorselRaporPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=False)  # Tek sayfa için
        
    def header(self):
        pass  # Özel header yapacağız
        
    def footer(self):
        pass  # Footer istemiyoruz

def puan_to_yildiz(puan: int) -> str:
    """Puanı yıldızlara çevirir"""
    if puan >= 90:
        return "***** MUKEMMEL!"
    elif puan >= 70:
        return "**** HARIKA!"
    elif puan >= 50:
        return "*** IYI"
    elif puan >= 30:
        return "** ORTA"
    else:
        return "* DUSUK"

def puan_emoji(puan: int) -> str:
    """Puan için basit karakter döndürür"""
    if puan >= 90:
        return "[HOT]"
    elif puan >= 70:
        return "[TOP]"
    elif puan >= 50:
        return "[OK]"
    elif puan >= 30:
        return "[LOW]"
    else:
        return "[ZZZ]"

def gorsel_rapor_pdf(dosya_adi: str, baslik: str, puan: int, grafik_yolu: str, 
                     toplam_sure: float, kategori_sayisi: int, en_cok_kategori: str, gemini_cevap: str):
    """Modern ve dikkat çekici tek sayfa rapor oluşturur"""
    pdf = GorselRaporPDF()
    pdf.add_page()
    
    # 🎯 BAŞLIK YAPISI (ASCII karakterlerle)
    pdf.set_font("Arial", "B", 22)
    pdf.set_text_color(25, 25, 112)  # Koyu mavi
    
    # Tarihi güzel formatta göster (ASCII)
    if "Gunluk Rapor - " in baslik or "Günlük Rapor - " in baslik:
        import pandas as pd
        tarih_str = baslik.replace("Günlük Rapor - ", "").replace("Gunluk Rapor - ", "")
        try:
            tarih_obj = pd.to_datetime(tarih_str)
            gun = tarih_obj.day
            ay_isim = tarih_obj.strftime('%B')
            # Türkçe ay isimlerini ASCII'ye çevir
            ay_dict = {
                'January': 'Ocak', 'February': 'Subat', 'March': 'Mart', 
                'April': 'Nisan', 'May': 'Mayis', 'June': 'Haziran',
                'July': 'Temmuz', 'August': 'Agustos', 'September': 'Eylul',
                'October': 'Ekim', 'November': 'Kasim', 'December': 'Aralik'
            }
            ay_isim = ay_dict.get(ay_isim, ay_isim)
            baslik_text = f"{gun} {ay_isim} - Gunluk Analiz Raporu"
        except:
            baslik_text = baslik.replace("Günlük Rapor - ", "").replace("Gunluk Rapor - ", "") + " - Gunluk Analiz Raporu"
    elif "Haftalik Rapor - " in baslik or "Haftalık Rapor - " in baslik:
        tarih_aralik = baslik.replace("Haftalık Rapor - ", "").replace("Haftalik Rapor - ", "")
        baslik_text = f"{tarih_aralik} - Haftalik Analiz Raporu"
    else:
        baslik_text = baslik
    
    pdf.cell(0, 12, baslik_text, ln=True, align='C')
    pdf.ln(8)
    
    # 🏆 URETKENLIK PUANI (Tek satırda yıldızlı, 10 üzerinden)
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(34, 139, 34)  # Yeşil (tek renk)

    
    if puan >= 9:
        seviye = "MUKEMMEL"
    elif puan >= 7:
        seviye = "HARIKA"
    elif puan >= 5:
        seviye = "IYI"
    elif puan >= 3:
        seviye = "ORTA"
    else:
        seviye = "DUSUK"
    
    # Tek satırda puan gösterimi (10 üzerinden)
    puan_satiri = f"Uretkenlik Puani: {puan}/10 - {seviye}"
    pdf.cell(0, 15, puan_satiri, ln=True, align='C')
    pdf.ln(10)
    
    # 📊 ANA GRAFIK (Sayfa ortası)
    if grafik_yolu and os.path.exists(grafik_yolu):
        pdf.image(grafik_yolu, x=10, y=pdf.get_y(), w=190, h=115)
        pdf.ln(120)
    else:
        # Grafik yoksa boşluk bırak
        pdf.ln(115)
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 10, "GRAFIK YUKLENEMEDI", ln=True, align='C')
        pdf.ln(10)
    
    # 📈 BILGI KUTULARI (Modern renkli arka planlar)
    pdf.set_text_color(0, 0, 0)  # Siyah
    pdf.set_font("Arial", "B", 11)
    
    stats_y = pdf.get_y()
    
    # Sol sütun (Açık mavi arka plan)
    pdf.set_fill_color(240, 248, 255)  # Açık mavi arka plan
    pdf.set_xy(15, stats_y)
    pdf.cell(85, 8, f"Toplam Sure: {toplam_sure:.1f} saat", ln=True, fill=True, border=0)
    pdf.set_x(15)
    pdf.cell(85, 8, f"Aktivite Sayisi: {kategori_sayisi} kayit", ln=True, fill=True, border=0)
    
    # Sağ sütun (Açık yeşil arka plan)
    pdf.set_fill_color(240, 255, 240)  # Açık yeşil arka plan
    pdf.set_xy(105, stats_y)
    # Türkçe karakterleri temizle
    en_cok_clean = turkce_temizle(en_cok_kategori) if en_cok_kategori else "Yok"
    pdf.cell(85, 8, f"En Cok Zaman: {en_cok_clean}", ln=True, fill=True, border=0)
    pdf.set_xy(105, stats_y + 8)
    tarih_clean = baslik_text.split(' - ')[0] if ' - ' in baslik_text else "Bilinmiyor"
    pdf.cell(85, 8, f"Rapor Tarihi: {tarih_clean}", ln=True, fill=True, border=0)
    
    pdf.ln(18)
    
    # 🤖 AI ONERISI (Modern açık mor arka plan)
    if pdf.get_y() > 240:  # Sayfa taştıysa daha az margin
        pdf.ln(2)
    
    # AI başlığı
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(138, 43, 226)  # Mor
    pdf.cell(0, 6, "AI YAPAY ZEKA ONERISI", ln=True, align='C')
    
    # AI kutusu (açık mor arka plan - 45 yükseklik)
    current_y = pdf.get_y()
    pdf.set_fill_color(245, 245, 255)  # Çok açık mor arka plan
    pdf.rect(15, current_y, 180, 45, 'DF')  # Kutu yüksekliği 45
    
    pdf.ln(3)
    pdf.set_font("Arial", size=9)
    pdf.set_text_color(0, 0, 0)  # Siyah
    
    # AI cevabını temizle ve ASCII'ye çevir
    if gemini_cevap:
        oneri_temiz = turkce_temizle(gemini_cevap)
        oneri_kisaltilmis = oneri_temiz[:400] + "..." if len(oneri_temiz) > 400 else oneri_temiz
        
        # Kutu içinde yazı (büyük kutu içinde)
        pdf.set_x(20)  # Sol margin
        pdf.multi_cell(170, 4, oneri_kisaltilmis)  # Daha kompakt satır aralığı
    
    # PDF'i kaydet
    pdf.output(dosya_adi)
    print(f"✅ Modern rapor olusturuldu: {dosya_adi}")

def gunluk_rapor_pdf(tarih: str, ozet: str, puan: int, gemini_cevap: str, grafik_yolu: str = None):
    """Günlük görsel rapor PDF'i oluşturur"""
    dosya_adi = f"data/reports/gunluk_rapor_{tarih}.pdf"
    baslik = f"Günlük Rapor - {tarih}"
    
    # Reports klasörünü oluştur
    os.makedirs("data/reports", exist_ok=True)
    
    # Özet'ten basit istatistikler çıkar
    lines = ozet.split('\n')
    toplam_sure = 0
    kategori_sayisi = 0
    en_cok_kategori = "Bilinmiyor"
    
    for line in lines:
        if "Toplam aktif süre:" in line:
            try:
                toplam_sure = float(line.split('(')[1].split(' saat')[0])
            except:
                toplam_sure = 0
        elif "Toplam kayıt sayısı:" in line:
            try:
                kategori_sayisi = int(line.split(':')[1].strip())
            except:
                kategori_sayisi = 0
        elif "•" in line and ":" in line:
            try:
                en_cok_kategori = line.split("•")[1].split(":")[0].strip()
                break
            except:
                pass
    
    gorsel_rapor_pdf(dosya_adi, baslik, puan, grafik_yolu, 
                     toplam_sure, kategori_sayisi, en_cok_kategori, gemini_cevap)
    return dosya_adi

def haftalik_rapor_pdf(baslangic: str, bitis: str, ozet: str, puan: int, gemini_cevap: str, grafik_yolu: str = None):
    """Haftalık görsel rapor PDF'i oluşturur"""
    dosya_adi = f"data/reports/haftalik_rapor_{baslangic}_{bitis}.pdf"
    baslik = f"Haftalık Rapor - {baslangic} / {bitis}"
    
    # Reports klasörünü oluştur
    os.makedirs("data/reports", exist_ok=True)
    
    # Haftalık özet'ten istatistikler çıkar
    lines = ozet.split('\n')
    toplam_sure = 0
    kategori_sayisi = 0
    en_cok_kategori = "Bilinmiyor"
    
    for line in lines:
        if "Toplam aktif süre:" in line:
            try:
                toplam_sure = float(line.split('(')[1].split(' saat')[0])
            except:
                toplam_sure = 0
        elif "Toplam aktivite:" in line:
            try:
                kategori_sayisi = int(line.split(':')[1].split()[0])
            except:
                kategori_sayisi = 0
        elif "En çok zaman:" in line:
            try:
                en_cok_raw = line.split(':')[1].strip()
                # Türkçe karakterleri temizle
                en_cok_kategori = turkce_temizle(en_cok_raw)
            except:
                en_cok_kategori = "Bilinmiyor"
    
    gorsel_rapor_pdf(dosya_adi, baslik, puan, grafik_yolu, 
                     toplam_sure, kategori_sayisi, en_cok_kategori, gemini_cevap)
    return dosya_adi 