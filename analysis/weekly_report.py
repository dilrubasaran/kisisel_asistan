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

def veri_yukle() -> pd.DataFrame:
    """Analiz verilerini yükler"""
    try:
        # ANALYSIS_FILE zaten full path içeriyor (config'ten)
        dosya_yolu = ANALYSIS_FILE
        if os.path.exists(dosya_yolu):
            df = pd.read_excel(dosya_yolu)
            df['Zaman'] = pd.to_datetime(df['Zaman'])
            df['Tarih'] = df['Zaman'].dt.date
            df['Gun'] = df['Zaman'].dt.day_name()
            return df
        else:
            print(f"⚠️ Analiz dosyası bulunamadı: {dosya_yolu}")
            return pd.DataFrame()
    except Exception as e:
        print(f"❌ Veri yükleme hatası: {e}")
        return pd.DataFrame()

def haftalik_veri_filtrele(df: pd.DataFrame, gun_sayisi: int = 7) -> pd.DataFrame:
    """Son N güne ait verileri filtreler"""
    son_tarih = datetime.now().date()
    baslangic_tarih = son_tarih - timedelta(days=gun_sayisi-1)
    
    haftalik_df = df[df['Zaman'].dt.date >= baslangic_tarih]
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
    """Detaylı haftalık grafik oluşturur (modern tasarım, saat cinsinden, yüksek kalite)"""
    try:
        if df.empty:
            return None
        
        # Süreleri saat cinsinden hesapla
        df_saat = df.copy()
        df_saat['Süre (saat)'] = df_saat['Süre (dk)'] / 60
        
        # 🎨 MODERN FONT AYARLARI (Günlük rapor stilinde)
        plt.rcParams.update({
            "font.size": 12,
            "axes.titlesize": 18,
            "axes.labelsize": 14,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "font.weight": "bold"
        })
        
        # Figure ve 4 panel (yüksek kalite, modern tasarım)
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 11))
        fig.patch.set_facecolor('#f8f9fa')  # Modern açık gri arka plan
        fig.suptitle('Haftalik Detayli Analiz', fontsize=22, fontweight='bold', y=0.93, color='#2c3e50')
        
        # 1. Günlük Trend - Modern tasarım
        gunluk_trend = gunluk_trend_analizi(df)
        gunluk_trend['Toplam_Sure_Saat'] = gunluk_trend['Toplam_Sure'] / 60  # Dakikadan saate
        
        # Modern line plot
        ax1.plot(gunluk_trend['Tarih'], gunluk_trend['Toplam_Sure_Saat'], 
                marker='o', linewidth=3, markersize=8, color='#3498db', 
                markerfacecolor='#2980b9', markeredgecolor='white', markeredgewidth=2)
        ax1.set_title('GUNLUK TOPLAM SURE TRENDI', fontsize=18, fontweight='bold', color='#2c3e50', pad=25)
        ax1.set_ylabel('Sure (Saat)', fontsize=14, fontweight='bold')
        ax1.tick_params(axis='x', rotation=45, labelsize=12)
        ax1.grid(True, alpha=0.4, color='#bdc3c7', linewidth=1)
        ax1.set_facecolor('#ecf0f1')
        
        # Veri noktaları üzerine değer yazma
        for i, (tarih, sure) in enumerate(zip(gunluk_trend['Tarih'], gunluk_trend['Toplam_Sure_Saat'])):
            ax1.text(tarih, sure + 0.2, f'{sure:.1f}h', ha='center', va='bottom', 
                    fontweight='bold', fontsize=11, color='#2c3e50')
        
        # 2. Kategori Dağılımı (Modern pasta) - Saat cinsinden, temiz karakterler
        kategori_analiz = kategori_dagili_analizi(df)
        if not kategori_analiz['kategori_sure'].empty:
            # Kategori isimlerini temizle ve saat cinsinden hesapla
            kategori_ascii = {}
            for kategori, sure_dk in kategori_analiz['kategori_sure'].items():
                kategori_clean = turkce_temizle(kategori)
                sure_saat = sure_dk / 60
                kategori_ascii[kategori_clean] = sure_saat
            
            # Modern renk paleti (günlük rapor ile aynı)
            colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
            wedges, texts, autotexts = ax2.pie(kategori_ascii.values(), labels=kategori_ascii.keys(), 
                   autopct='%1.1f%%', colors=colors[:len(kategori_ascii)], startangle=90,
                   textprops={'fontsize': 13, 'fontweight': 'bold'},
                   wedgeprops={'linewidth': 3, 'edgecolor': 'white'})
            ax2.set_title('KATEGORI DAGILIMI', fontsize=18, fontweight='bold', color='#2c3e50', pad=25)
            
            # Pasta grafiği yazıları daha büyük ve belirgin
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_fontweight('bold')
        
        # 3. Günlük Aktivite Sayısı - Modern bar chart
        # Gradyan renkler aktivite sayısına göre
        bar_colors = ['#2980b9' if v > 15 else '#3498db' if v > 10 else '#74b9ff' for v in gunluk_trend['Aktivite_Sayisi']]
        bars = ax3.bar(gunluk_trend['Tarih'], gunluk_trend['Aktivite_Sayisi'], 
                      color=bar_colors, alpha=0.9, width=0.6,
                      edgecolor='#1e3799', linewidth=2)
        
        ax3.set_title('GUNLUK AKTIVITE SAYISI', fontsize=18, fontweight='bold', color='#2c3e50', pad=25)
        ax3.set_ylabel('Aktivite Sayisi', fontsize=14, fontweight='bold')
        ax3.tick_params(axis='x', rotation=45, labelsize=12)
        ax3.grid(True, alpha=0.4, color='#bdc3c7', axis='y', linewidth=1)
        ax3.set_facecolor('#ecf0f1')
        
        # Bar değerleri üzerine yazma
        for i, v in enumerate(gunluk_trend['Aktivite_Sayisi']):
            if v > 0:
                ax3.text(gunluk_trend['Tarih'].iloc[i], v + 0.5, f'{int(v)}', ha='center', va='bottom', 
                        fontweight='bold', fontsize=12, color='#2c3e50')
        
        # 4. Kategori Bar Chart - Modern tasarım, saat cinsinden, temiz karakterler
        if not kategori_analiz['kategori_sure'].empty:
            # Kategori isimlerini temizle ve saat cinsinden hesapla
            kategori_ascii = {}
            for kategori, sure_dk in kategori_analiz['kategori_sure'].items():
                kategori_clean = turkce_temizle(kategori)
                sure_saat = sure_dk / 60
                kategori_ascii[kategori_clean] = sure_saat
            
            # Profesyonel renkler (günlük rapor ile aynı)
            bright_colors = ['#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c'][:len(kategori_ascii)]
            bars = ax4.bar(kategori_ascii.keys(), kategori_ascii.values(), 
                          color=bright_colors, alpha=0.9, edgecolor='white', linewidth=3)
            
            ax4.set_title('KATEGORI BAZINDA TOPLAM SURE', fontsize=18, fontweight='bold', color='#2c3e50', pad=25)
            ax4.set_ylabel('Sure (Saat)', fontsize=14, fontweight='bold')
            ax4.tick_params(axis='x', rotation=45, labelsize=12)
            ax4.set_facecolor('#ecf0f1')
            ax4.grid(True, alpha=0.4, color='#bdc3c7', axis='y', linewidth=1)
            
            # Bar değerleri üzerine yazma (saat cinsinden)
            for bar in bars:
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{height:.1f}h', ha='center', va='bottom', fontweight='bold', 
                        fontsize=13, color='#2c3e50')
        
        # Layout düzenle (daha fazla boşluk)
        plt.tight_layout()
        plt.subplots_adjust(top=0.85, hspace=0.55, wspace=0.35)
        
        # Kaydet (ultra yüksek kalite - günlük rapor ile aynı)
        os.makedirs("temp", exist_ok=True)
        grafik_yolu = f"temp/{dosya_adi}"
        plt.savefig(grafik_yolu, dpi=600, bbox_inches='tight', facecolor='#f8f9fa', 
                   edgecolor='none', format='png')
        plt.close()
        
        print(f"✅ Modern haftalik grafik kaydedildi: {grafik_yolu}")
        return grafik_yolu
    except Exception as e:
        print(f"❌ Haftalik grafik olusturma hatasi: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def kompakt_haftalik_ozet_olustur(df: pd.DataFrame) -> str:
    """Kompakt haftalık özet metin oluşturur"""
    if df.empty:
        return "Bu hafta için veri bulunamadı."
    
    toplam_sure = df['Süre (dk)'].sum()
    kategori_sure = df.groupby('Kategori')['Süre (dk)'].sum()
    en_cok = kategori_sure.idxmax() if not kategori_sure.empty else "Bilinmiyor"
    
    # Minimal özet
    ozet = f"Toplam aktif süre: {toplam_sure} dakika ({toplam_sure/60:.1f} saat)\n"
    ozet += f"Toplam aktivite: {len(df)} kayıt\n"
    
    # En çok zaman harcanan kategoriyi göster
    if not kategori_sure.empty:
        en_cok_sure = kategori_sure.max()
        ozet += f"En çok zaman: {en_cok} ({en_cok_sure} dk)\n"
        
        # Sadece en önemli kategorileri göster
        for kategori, sure in kategori_sure.head(3).items():  # Sadece ilk 3
            yuzde = (sure / toplam_sure) * 100
            ozet += f"• {kategori}: {sure} dk ({yuzde:.0f}%)\n"
    
    return ozet

def haftalik_rapor_olustur(gun_sayisi: int = 7) -> str:
    """Görsel ağırlıklı haftalık rapor oluşturur (daily_report.py'dan taşındı)"""
    print("📊 Görsel haftalık rapor oluşturuluyor...")
    
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
    
    # Kompakt özet oluştur
    ozet = kompakt_haftalik_ozet_olustur(haftalik_df)
    
    # Haftalık 4-panel grafik
    grafik_yolu = haftalik_grafik_olustur(haftalik_df, f"haftalik_dashboard_{baslangic_tarih}_{son_tarih}.png")
    
    # Gemini önerisi al (kısa haftalık)
    kisa_prompt = f"Haftalık özet: {ozet}\nPuan: {puan}/10\n\nHaftalık performans için kısa ve strategik öneri (max 200 kelime)."
    gemini_cevap = al_gemini_onerisi(kisa_prompt, puan)
    
    # PDF oluştur (yeni görsel tasarım)
    pdf_yolu = haftalik_rapor_pdf(baslangic_tarih, son_tarih, ozet, puan, gemini_cevap, grafik_yolu)
    
    # Geçici dosyaları temizle
    if grafik_yolu and os.path.exists(grafik_yolu):
        os.remove(grafik_yolu)
    
    return f"✅ Görsel haftalık rapor: {pdf_yolu}\n📊 Puan: {puan}/10"

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

def detayli_haftalik_rapor_olustur(gun_sayisi: int = 7) -> str:
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
    haftalik_prompt = f"{ozet}\n\nBu haftalık performansa göre gelecek hafta için strategik öneriler ver."
    gemini_cevap = al_gemini_onerisi(haftalik_prompt, puan)
    
    # PDF oluştur
    pdf_yolu = haftalik_rapor_pdf(baslangic_tarih, son_tarih, ozet, puan, gemini_cevap, grafik_yolu)
    
    # Geçici dosyaları temizle
    if grafik_yolu and os.path.exists(grafik_yolu):
        os.remove(grafik_yolu)
    
    return f"✅ Haftalık rapor oluşturuldu: {pdf_yolu}\n📊 Puan: {puan}/10\n📈 Geçen haftaya göre: {karsilastirma['degisim_yuzde']:+.1f}%"

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
        trend_ozet += f"📅 {veri['hafta']}: {veri['toplam_sure']} dk, {veri['puan']}/10 puan\n"
    
    # Ortalamalar
    ortalama_sure = sum([v['toplam_sure'] for v in haftalik_veriler]) / len(haftalik_veriler)
    ortalama_puan = sum([v['puan'] for v in haftalik_veriler]) / len(haftalik_veriler)
    
    trend_ozet += f"\n📊 Ortalamalar:\n"
    trend_ozet += f"• Haftalık süre: {ortalama_sure:.1f} dakika\n"
    trend_ozet += f"• Haftalık puan: {ortalama_puan:.1f}/10\n"
    
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
    
    print("\n4️⃣ Detaylı Haftalık Rapor:")
    print(detayli_haftalik_rapor_olustur()) 