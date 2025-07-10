# 📄 PDF Rapor Oluşturucu

from fpdf import FPDF
import os

def raporu_pdf_yap(dosya_adi: str, baslik: str, ozet: str, grafik_yolu: str, puan: int, gemini_cevap: str):
    """PDF raporu oluşturur"""
    pdf = FPDF()
    pdf.add_page()
    
    # Başlık
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, baslik.encode('latin-1', 'replace').decode('latin-1'), ln=True)

    # Özet
    pdf.set_font("Arial", size=12)
    ozet_clean = ozet.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, ozet_clean)
    
    # Grafik ekleme
    if grafik_yolu and os.path.exists(grafik_yolu):
        pdf.image(grafik_yolu, x=10, y=None, w=180)

    pdf.ln(10)
    
    # Üretkenlik puanı
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Uretkenlik Puani: {puan}/100", ln=True)

    # Gemini önerisi
    pdf.set_font("Arial", size=12)
    gemini_clean = gemini_cevap.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, f"AI Onerisi: {gemini_clean}")

    # PDF'i kaydet
    pdf.output(dosya_adi)
    print(f"✅ PDF raporu oluşturuldu: {dosya_adi}")

def gunluk_rapor_pdf(tarih: str, ozet: str, puan: int, gemini_cevap: str, grafik_yolu: str = None):
    """Günlük rapor PDF'i oluşturur"""
    dosya_adi = f"data/reports/gunluk_rapor_{tarih}.pdf"
    baslik = f"Gunluk Rapor - {tarih}"
    
    # Reports klasörünü oluştur
    os.makedirs("data/reports", exist_ok=True)
    
    raporu_pdf_yap(dosya_adi, baslik, ozet, grafik_yolu, puan, gemini_cevap)
    return dosya_adi

def haftalik_rapor_pdf(baslangic: str, bitis: str, ozet: str, puan: int, gemini_cevap: str, grafik_yolu: str = None):
    """Haftalık rapor PDF'i oluşturur"""
    dosya_adi = f"data/reports/haftalik_rapor_{baslangic}_{bitis}.pdf"
    baslik = f"Haftalik Rapor - {baslangic} - {bitis}"
    
    # Reports klasörünü oluştur
    os.makedirs("data/reports", exist_ok=True)
    
    raporu_pdf_yap(dosya_adi, baslik, ozet, grafik_yolu, puan, gemini_cevap)
    return dosya_adi 