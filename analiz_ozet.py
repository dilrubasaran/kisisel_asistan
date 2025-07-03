import pandas as pd
import os

def analiz_ozeti_goster():
    """Analiz verilerinin özetini gösterir"""
    dosya = "analiz_verisi.xlsx"
    
    if not os.path.exists(dosya):
        print("❌ Analiz verisi dosyası bulunamadı!")
        return
    
    try:
        df = pd.read_excel(dosya)
        
        if df.empty:
            print("📭 Henüz analiz verisi yok.")
            return
        
        print("📊 ANALIZ ÖZETİ")
        print("=" * 50)
        
        # Kategori ve Alt Başlık bazında süre toplamı
        ozet = df.groupby(["Kategori", "Alt Başlık"])["Süre (dk)"].sum().reset_index()
        print("\n🔍 Kategori ve Alt Başlık Bazında Süre Dağılımı:")
        print(ozet.to_string(index=False))
        
        # Sadece kategori bazında
        kategori_ozet = df.groupby("Kategori")["Süre (dk)"].sum().reset_index()
        print("\n📈 Kategori Bazında Toplam Süreler:")
        print(kategori_ozet.to_string(index=False))
        
        # Genel istatistikler
        toplam_sure = df["Süre (dk)"].sum()
        kayit_sayisi = len(df)
        ortalama_sure = df["Süre (dk)"].mean()
        
        print(f"\n📋 GENEL İSTATİSTİKLER:")
        print(f"   • Toplam Kayıt: {kayit_sayisi}")
        print(f"   • Toplam Süre: {toplam_sure} dakika ({toplam_sure/60:.1f} saat)")
        print(f"   • Ortalama Süre: {ortalama_sure:.1f} dakika")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    analiz_ozeti_goster() 