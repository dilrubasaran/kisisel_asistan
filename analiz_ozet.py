# 📊 Analiz Özet Raporu

import pandas as pd
from datetime import datetime
from config.config import ANALYSIS_FILE

def analiz_ozet_olustur():
    """Analiz verilerinin özetini oluşturur"""
    try:
        # Data/logs klasöründen veri oku
        dosya_yolu = f"data/logs/{ANALYSIS_FILE}"
        df = pd.read_excel(dosya_yolu)
        
        print("📊 ANALİZ ÖZET RAPORU")
        print("=" * 40)
        
        # Toplam istatistikler
        toplam_kayit = len(df)
        toplam_sure = df["Süre (dk)"].sum()
        
        print(f"📈 Toplam Kayıt Sayısı: {toplam_kayit}")
        print(f"⏱️ Toplam Süre: {toplam_sure} dakika ({toplam_sure/60:.1f} saat)")
        
        # Kategori bazında özet
        print(f"\n🎯 KATEGORİ BAZINDA ÖZET:")
        kategori_ozet = df.groupby("Kategori").agg({
            "Süre (dk)": ["sum", "count", "mean"]
        }).round(1)
        
        for kategori in kategori_ozet.index:
            toplam = kategori_ozet.loc[kategori, ("Süre (dk)", "sum")]
            adet = kategori_ozet.loc[kategori, ("Süre (dk)", "count")]
            ortalama = kategori_ozet.loc[kategori, ("Süre (dk)", "mean")]
            print(f"• {kategori}: {toplam} dk ({adet} kayıt, ort: {ortalama} dk)")
        
        # En popüler aktiviteler
        print(f"\n🏆 EN POPÜLER AKTİVİTELER:")
        top_aktiviteler = df["Açıklama"].value_counts().head(5)
        for i, (aktivite, sayi) in enumerate(top_aktiviteler.items(), 1):
            print(f"{i}. {aktivite}: {sayi} kez")
        
        print("\n" + "=" * 40)
        
    except FileNotFoundError:
        print("❌ Analiz dosyası bulunamadı!")
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    analiz_ozet_olustur() 