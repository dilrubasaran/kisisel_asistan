# 📅 Haftalık Rapor ve Analiz Sistemi

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import os

# Local imports
from analysis.productivity_score import hesapla_urekenlik_puani
from ai.gemini import al_gemini_onerisi
from utils.pdf_generator import haftalik_rapor_pdf
from config.config import ANALYSIS_FILE

def veri_yukle() -> pd.DataFrame:
    """Analiz verilerini yükler"""
    try:
        dosya_yolu = f"data/logs/{ANALYSIS_FILE}"
        if os.path.exists(dosya_yolu):
            df = pd.read_excel(dosya_yolu)
            df['Zaman'] = pd.to_datetime(df['Zaman'])
            df['Tarih'] = df['Zaman'].dt.date
            df['Gun'] = df['Zaman'].dt.day_name()
            return df
        else:
            print("⚠️ Analiz dosyası bulunamadı!")
            return pd.DataFrame()
    except Exception as e:
        print(f"❌ Veri yükleme hatası: {e}")
        return pd.DataFrame()

def haftalik_veri_filtrele(df: pd.DataFrame, gun_sayisi: int = 7) -> pd.DataFrame:
    """Son N güne ait verileri filtreler"""
    son_tarih = datetime.now().date()
    baslangic_tarih = son_tarih - timedelta(days=gun_sayisi-1)
    
    haftalik_df = df[df['Tarih'] >= baslangic_tarih]
    return haftalik_df

def gecmis_hafta_karsilastir(df: pd.DataFrame) -> dict:
    """Bu hafta vs geçen hafta karşılaştırması"""
    bugün = datetime.now().date()
    
    # Bu hafta (son 7 gün)
    bu_hafta_baslangic = bugün - timedelta(days=6)
    bu_hafta = df[df['Tarih'] >= bu_hafta_baslangic]
    
    # Geçen hafta (7-14 gün önce)
    gecen_hafta_baslangic = bugün - timedelta(days=13)
    gecen_hafta_bitis = bugün - timedelta(days=7)
    gecen_hafta = df[(df['Tarih'] >= gecen_hafta_baslangic) & (df['Tarih'] <= gecen_hafta_bitis)]
    
    # Karşılaştırma
    bu_hafta_toplam = bu_hafta['Süre (dk)'].sum()
    gecen_hafta_toplam = gecen_hafta['Süre (dk)'].sum()
    
    if gecen_hafta_toplam > 0:
        degisim_yuzde = ((bu_hafta_toplam - gecen_hafta_toplam) / gecen_hafta_toplam) * 100
    else:
        degisim_yuzde = 0
    
    return {
        'bu_hafta_toplam': bu_hafta_toplam,
        'gecen_hafta_toplam': gecen_hafta_toplam,
        'degisim_yuzde': degisim_yuzde,
        'bu_hafta_df': bu_hafta,
        'gecen_hafta_df': gecen_hafta
    }

def gunluk_trend_analizi(df: pd.DataFrame) -> pd.DataFrame:
    """Haftalık günlük trend analizi"""
    gunluk_ozet = df.groupby('Tarih').agg({
        'Süre (dk)': 'sum',
        'Kategori': 'count'
    }).reset_index()
    
    gunluk_ozet.columns = ['Tarih', 'Toplam_Sure', 'Aktivite_Sayisi']
    gunluk_ozet['Ortalama_Sure'] = gunluk_ozet['Toplam_Sure'] / gunluk_ozet['Aktivite_Sayisi']
    
    return gunluk_ozet

def kategori_dagili_analizi(df: pd.DataFrame) -> dict:
    """Kategorilerin haftalık dağılımı"""
    kategori_sure = df.groupby('Kategori')['Süre (dk)'].sum()
    toplam_sure = kategori_sure.sum()
    
    kategori_yuzde = (kategori_sure / toplam_sure * 100).round(1)
    
    return {
        'kategori_sure': kategori_sure,
        'kategori_yuzde': kategori_yuzde,
        'en_cok': kategori_sure.idxmax() if not kategori_sure.empty else None,
        'en_az': kategori_sure.idxmin() if not kategori_sure.empty else None
    }

def haftalik_grafik_olustur(df: pd.DataFrame, dosya_adi: str) -> str:
    """Detaylı haftalık grafik oluşturur"""
    try:
        if df.empty:
            return None
        
        # Figure ve subplotlar
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Haftalık Detaylı Analiz', fontsize=16, fontweight='bold')
        
        # 1. Günlük Trend
        gunluk_trend = gunluk_trend_analizi(df)
        ax1.plot(gunluk_trend['Tarih'], gunluk_trend['Toplam_Sure'], marker='o', linewidth=2, markersize=6)
        ax1.set_title('Günlük Toplam Süre Trendi')
        ax1.set_ylabel('Süre (Dakika)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # 2. Kategori Dağılımı (Pasta)
        kategori_analiz = kategori_dagili_analizi(df)
        if not kategori_analiz['kategori_sure'].empty:
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#D63031', '#00B894']
            ax2.pie(kategori_analiz['kategori_sure'], labels=kategori_analiz['kategori_sure'].index, 
                   autopct='%1.1f%%', colors=colors[:len(kategori_analiz['kategori_sure'])])
            ax2.set_title('Kategori Dağılımı')
        
        # 3. Günlük Aktivite Sayısı
        ax3.bar(gunluk_trend['Tarih'], gunluk_trend['Aktivite_Sayisi'], color='#74B9FF', alpha=0.7)
        ax3.set_title('Günlük Aktivite Sayısı')
        ax3.set_ylabel('Aktivite Sayısı')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3)
        
        # 4. Kategori Bar Chart
        if not kategori_analiz['kategori_sure'].empty:
            bars = ax4.bar(kategori_analiz['kategori_sure'].index, kategori_analiz['kategori_sure'], 
                          color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'][:len(kategori_analiz['kategori_sure'])])
            ax4.set_title('Kategori Bazında Toplam Süre')
            ax4.set_ylabel('Süre (Dakika)')
            ax4.tick_params(axis='x', rotation=45)
            
            # Bar'ların üzerine değer yazma
            for bar in bars:
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + 5,
                        f'{int(height)}', ha='center', va='bottom')
        
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

def detayli_ozet_olustur(df: pd.DataFrame, karsilastirma: dict) -> str:
    """Detaylı haftalık özet oluşturur"""
    if df.empty:
        return "Bu hafta için veri bulunamadı."
    
    # Temel istatistikler
    toplam_sure = df['Süre (dk)'].sum()
    gunluk_ortalama = toplam_sure / 7
    aktivite_sayisi = len(df)
    
    # Kategori analizi
    kategori_analiz = kategori_dagili_analizi(df)
    
    # Günlük trend
    gunluk_trend = gunluk_trend_analizi(df)
    en_verimli_gun = gunluk_trend.loc[gunluk_trend['Toplam_Sure'].idxmax(), 'Tarih'] if not gunluk_trend.empty else None
    
    ozet = f"📊 HAFTALIK DETAYLI ANALİZ\n"
    ozet += f"═" * 40 + "\n\n"
    
    ozet += f"⏱️ ZAMAN ANALİZİ:\n"
    ozet += f"• Toplam aktif süre: {toplam_sure} dakika ({toplam_sure/60:.1f} saat)\n"
    ozet += f"• Günlük ortalama: {gunluk_ortalama:.1f} dakika\n"
    ozet += f"• Toplam aktivite: {aktivite_sayisi} kayıt\n"
    if en_verimli_gun:
        ozet += f"• En verimli gün: {en_verimli_gun}\n"
    ozet += "\n"
    
    ozet += f"📈 KARŞILAŞTIRMA:\n"
    if karsilastirma['gecen_hafta_toplam'] > 0:
        if karsilastirma['degisim_yuzde'] > 0:
            ozet += f"• Geçen haftaya göre %{karsilastirma['degisim_yuzde']:.1f} artış ⬆️\n"
        else:
            ozet += f"• Geçen haftaya göre %{abs(karsilastirma['degisim_yuzde']):.1f} azalış ⬇️\n"
    else:
        ozet += f"• Geçen hafta veri yok\n"
    ozet += "\n"
    
    ozet += f"🎯 KATEGORİ DAĞILIMI:\n"
    for kategori, sure in kategori_analiz['kategori_sure'].items():
        yuzde = kategori_analiz['kategori_yuzde'][kategori]
        ozet += f"• {kategori}: {sure} dk ({yuzde}%)\n"
    
    if kategori_analiz['en_cok']:
        ozet += f"\n🏆 En çok zaman: {kategori_analiz['en_cok']}\n"
    
    # Günlük detaylar
    ozet += f"\n📅 GÜNLÜK DAĞILIM:\n"
    for _, gun in gunluk_trend.iterrows():
        ozet += f"• {gun['Tarih']}: {gun['Toplam_Sure']} dk ({gun['Aktivite_Sayisi']} aktivite)\n"
    
    return ozet

def haftalik_rapor_olustur(gun_sayisi: int = 7) -> str:
    """Detaylı haftalık rapor oluşturur"""
    print("📅 Detaylı haftalık rapor oluşturuluyor...")
    
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
    
    # Karşılaştırma analizi
    karsilastirma = gecmis_hafta_karsilastir(df)
    
    # Üretkenlik puanı hesapla
    puan, yorumlar = hesapla_urekenlik_puani(haftalik_df)
    
    # Detaylı özet oluştur
    ozet = detayli_ozet_olustur(haftalik_df, karsilastirma)
    
    # Grafik oluştur
    grafik_yolu = haftalik_grafik_olustur(haftalik_df, f"haftalik_detay_{baslangic_tarih}_{son_tarih}.png")
    
    # Gemini önerisi al (haftalık odaklı)
    haftalik_prompt = f"{ozet}\n\nBu haftalık performansa göre gelecek hafta için stratejik öneriler ver."
    gemini_cevap = al_gemini_onerisi(haftalik_prompt, puan)
    
    # PDF oluştur
    pdf_yolu = haftalik_rapor_pdf(baslangic_tarih, son_tarih, ozet, puan, gemini_cevap, grafik_yolu)
    
    # Geçici dosyaları temizle
    if grafik_yolu and os.path.exists(grafik_yolu):
        os.remove(grafik_yolu)
    
    return f"✅ Haftalık rapor oluşturuldu: {pdf_yolu}\n📊 Puan: {puan}/100\n📈 Geçen haftaya göre: {karsilastirma['degisim_yuzde']:+.1f}%"

def haftalik_trend_raporu(hafta_sayisi: int = 4) -> str:
    """Son N haftalık trend raporu"""
    print(f"📊 Son {hafta_sayisi} haftalık trend analizi...")
    
    df = veri_yukle()
    if df.empty:
        return "❌ Veri bulunamadı."
    
    haftalik_veriler = []
    
    for i in range(hafta_sayisi):
        hafta_sonu = datetime.now().date() - timedelta(days=i*7)
        hafta_baslangici = hafta_sonu - timedelta(days=6)
        
        hafta_df = df[(df['Tarih'] >= hafta_baslangici) & (df['Tarih'] <= hafta_sonu)]
        
        if not hafta_df.empty:
            toplam_sure = hafta_df['Süre (dk)'].sum()
            puan, _ = hesapla_urekenlik_puani(hafta_df)
            
            haftalik_veriler.append({
                'hafta': f"{hafta_baslangici} - {hafta_sonu}",
                'toplam_sure': toplam_sure,
                'puan': puan,
                'hafta_no': i + 1
            })
    
    if not haftalik_veriler:
        return "❌ Trend analizi için yeterli veri yok."
    
    # Trend analizi
    trend_ozet = "📈 HAFTALIK TREND ANALİZİ\n"
    trend_ozet += "=" * 40 + "\n\n"
    
    for veri in reversed(haftalik_veriler):
        trend_ozet += f"📅 {veri['hafta']}: {veri['toplam_sure']} dk, {veri['puan']}/100 puan\n"
    
    # Ortalamalar
    ortalama_sure = sum([v['toplam_sure'] for v in haftalik_veriler]) / len(haftalik_veriler)
    ortalama_puan = sum([v['puan'] for v in haftalik_veriler]) / len(haftalik_veriler)
    
    trend_ozet += f"\n📊 Ortalamalar:\n"
    trend_ozet += f"• Haftalık süre: {ortalama_sure:.1f} dakika\n"
    trend_ozet += f"• Haftalık puan: {ortalama_puan:.1f}/100\n"
    
    return trend_ozet

# Ana fonksiyonlar
def kisa_haftalik_rapor() -> str:
    """Kısa haftalık özet"""
    return haftalik_rapor_olustur(7)

def uzun_haftalik_rapor() -> str:
    """Uzun haftalık rapor (14 gün)"""
    return haftalik_rapor_olustur(14)

# Test fonksiyonu
if __name__ == "__main__":
    print("📅 Haftalık Rapor Testleri:\n")
    
    print("1️⃣ Standart Haftalık Rapor:")
    print(kisa_haftalik_rapor())
    
    print("\n2️⃣ Trend Analizi:")
    print(haftalik_trend_raporu())
    
    print("\n3️⃣ Uzun Dönem Rapor:")
    print(uzun_haftalik_rapor()) 