# 📊 Günlük ve Haftalık Rapor Sistemi

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

# Local imports
from analysis.productivity_score import hesapla_urekenlik_puani
from ai.gemini import al_gemini_onerisi
from utils.pdf_generator import gunluk_rapor_pdf, haftalik_rapor_pdf
from config.config import ANALYSIS_FILE

def veri_yukle() -> pd.DataFrame:
    """Analiz verilerini yükler"""
    try:
        dosya_yolu = f"data/logs/{ANALYSIS_FILE}"
        if os.path.exists(dosya_yolu):
            df = pd.read_excel(dosya_yolu)
            df['Zaman'] = pd.to_datetime(df['Zaman'])
            return df
        else:
            print("⚠️ Analiz dosyası bulunamadı!")
            return pd.DataFrame()
    except Exception as e:
        print(f"❌ Veri yükleme hatası: {e}")
        return pd.DataFrame()

def gunluk_veri_filtrele(df: pd.DataFrame, tarih: str = None) -> pd.DataFrame:
    """Belirli bir güne ait verileri filtreler"""
    if tarih is None:
        tarih = datetime.now().strftime('%Y-%m-%d')
    
    # Tarihi datetime'a çevir
    hedef_tarih = pd.to_datetime(tarih).date()
    
    # O güne ait verileri filtrele
    gunluk_df = df[df['Zaman'].dt.date == hedef_tarih]
    return gunluk_df

def haftalik_veri_filtrele(df: pd.DataFrame, gun_sayisi: int = 7) -> pd.DataFrame:
    """Son N güne ait verileri filtreler"""
    son_tarih = datetime.now().date()
    baslangic_tarih = son_tarih - timedelta(days=gun_sayisi-1)
    
    haftalik_df = df[df['Zaman'].dt.date >= baslangic_tarih]
    return haftalik_df

def grafik_olustur(df: pd.DataFrame, dosya_adi: str, baslik: str) -> str:
    """Kategori dağılımı grafiği oluşturur"""
    try:
        if df.empty:
            return None
            
        # Kategori bazında süre topla
        kategori_sure = df.groupby('Kategori')['Süre (dk)'].sum()
        
        if kategori_sure.empty:
            return None
        
        # Grafik oluştur
        plt.figure(figsize=(10, 6))
        kategori_sure.plot(kind='bar', color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
        plt.title(baslik)
        plt.xlabel('Kategori')
        plt.ylabel('Süre (Dakika)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Kaydet
        os.makedirs("temp", exist_ok=True)
        grafik_yolu = f"temp/{dosya_adi}"
        plt.savefig(grafik_yolu, dpi=300, bbox_inches='tight')
        plt.close()
        
        return grafik_yolu
    except Exception as e:
        print(f"❌ Grafik oluşturma hatası: {e}")
        return None

def ozet_olustur(df: pd.DataFrame) -> str:
    """Özet metin oluşturur"""
    if df.empty:
        return "Bu dönem için veri bulunamadı."
    
    toplam_sure = df['Süre (dk)'].sum()
    kategori_sure = df.groupby('Kategori')['Süre (dk)'].sum()
    
    ozet = f"Toplam aktif süre: {toplam_sure} dakika ({toplam_sure/60:.1f} saat)\n\n"
    ozet += "Kategori dağılımı:\n"
    
    for kategori, sure in kategori_sure.items():
        yuzde = (sure / toplam_sure) * 100
        ozet += f"• {kategori}: {sure} dk ({yuzde:.1f}%)\n"
    
    if not df['Açıklama'].dropna().empty:
        ozet += f"\nToplam kayıt sayısı: {len(df)}\n"
        ozet += f"Detaylı açıklama sayısı: {len(df['Açıklama'].dropna())}"
    
    return ozet

def gunluk_rapor_olustur(tarih: str = None) -> str:
    """Günlük rapor oluşturur"""
    print("📊 Günlük rapor oluşturuluyor...")
    
    # Veri yükle
    df = veri_yukle()
    if df.empty:
        return "❌ Veri bulunamadığı için rapor oluşturulamadı."
    
    # Günlük veriyi filtrele
    if tarih is None:
        tarih = datetime.now().strftime('%Y-%m-%d')
    
    gunluk_df = gunluk_veri_filtrele(df, tarih)
    
    if gunluk_df.empty:
        return f"❌ {tarih} tarihine ait veri bulunamadı."
    
    # Üretkenlik puanı hesapla
    puan, yorumlar = hesapla_urekenlik_puani(gunluk_df)
    
    # Özet oluştur
    ozet = ozet_olustur(gunluk_df)
    
    # Grafik oluştur
    grafik_yolu = grafik_olustur(gunluk_df, f"gunluk_grafik_{tarih}.png", f"Günlük Aktivite - {tarih}")
    
    # Gemini önerisi al
    gemini_cevap = al_gemini_onerisi(ozet, puan)
    
    # PDF oluştur
    pdf_yolu = gunluk_rapor_pdf(tarih, ozet, puan, gemini_cevap, grafik_yolu)
    
    # Geçici dosyaları temizle
    if grafik_yolu and os.path.exists(grafik_yolu):
        os.remove(grafik_yolu)
    
    return f"✅ Günlük rapor oluşturuldu: {pdf_yolu}\n📊 Puan: {puan}/100"

def haftalik_rapor_olustur(gun_sayisi: int = 7) -> str:
    """Haftalık rapor oluşturur"""
    print("📊 Haftalık rapor oluşturuluyor...")
    
    # Veri yükle
    df = veri_yukle()
    if df.empty:
        return "❌ Veri bulunamadığı için rapor oluşturulamadı."
    
    # Haftalık veriyi filtrele
    haftalik_df = haftalik_veri_filtrele(df, gun_sayisi)
    
    if haftalik_df.empty:
        return f"❌ Son {gun_sayisi} güne ait veri bulunamadı."
    
    # Tarih aralığı
    son_tarih = datetime.now().strftime('%Y-%m-%d')
    baslangic_tarih = (datetime.now() - timedelta(days=gun_sayisi-1)).strftime('%Y-%m-%d')
    
    # Üretkenlik puanı hesapla (haftalık ortalama)
    puan, yorumlar = hesapla_urekenlik_puani(haftalik_df)
    
    # Özet oluştur
    ozet = ozet_olustur(haftalik_df)
    
    # Grafik oluştur
    grafik_yolu = grafik_olustur(haftalik_df, f"haftalik_grafik_{baslangic_tarih}_{son_tarih}.png", f"Haftalık Aktivite - {baslangic_tarih} / {son_tarih}")
    
    # Gemini önerisi al
    gemini_cevap = al_gemini_onerisi(ozet, puan)
    
    # PDF oluştur
    pdf_yolu = haftalik_rapor_pdf(baslangic_tarih, son_tarih, ozet, puan, gemini_cevap, grafik_yolu)
    
    # Geçici dosyaları temizle
    if grafik_yolu and os.path.exists(grafik_yolu):
        os.remove(grafik_yolu)
    
    return f"✅ Haftalık rapor oluşturuldu: {pdf_yolu}\n📊 Puan: {puan}/100"

# Test fonksiyonu
if __name__ == "__main__":
    print("🔍 Günlük Rapor Testi:")
    print(gunluk_rapor_olustur())
    
    print("\n🔍 Haftalık Rapor Testi:")
    print(haftalik_rapor_olustur()) 