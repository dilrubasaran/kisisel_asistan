# 📊 Günlük Rapor Sistemi

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

# Local imports
from analysis.productivity_score import hesapla_urekenlik_puani
from ai.gemini import al_gemini_onerisi
from utils.pdf_generator import gunluk_rapor_pdf
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
            return df
        else:
            print(f"⚠️ Analiz dosyası bulunamadı: {dosya_yolu}")
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

def gunluk_dashboard_grafik(df: pd.DataFrame, dosya_adi: str, tarih: str) -> str:
    """4-panel günlük dashboard oluşturur (saat cinsinden, yüksek kalite)"""
    try:
        if df.empty:
            return None
        
        # Süreleri saat cinsinden hesapla
        df_saat = df.copy()
        df_saat['Süre (saat)'] = df_saat['Süre (dk)'] / 60
        
        # 🎨 GENEL FONT AYARLARI
        plt.rcParams.update({
            "font.size": 12,
            "axes.titlesize": 18,
            "axes.labelsize": 14,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "font.weight": "bold"
        })
        
        # Figure ve 4 panel (yüksek kalite) - başlık kaldırıldı
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 11))
        fig.patch.set_facecolor('#f8f9fa')  # Açık gri arka plan
        
        # 1. Kategori Dağılımı (Pasta) - Saat cinsinden
        kategori_sure = df_saat.groupby('Kategori')['Süre (saat)'].sum()
        if not kategori_sure.empty:
            # Kategori isimlerini temizle
            kategori_ascii = {}
            for kategori, sure in kategori_sure.items():
                kategori_clean = turkce_temizle(kategori)
                kategori_ascii[kategori_clean] = sure
            
            # Modern renkler
            colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
            wedges, texts, autotexts = ax1.pie(kategori_ascii.values(), labels=kategori_ascii.keys(), 
                   autopct='%1.1f%%', colors=colors[:len(kategori_ascii)], startangle=90,
                   textprops={'fontsize': 13, 'fontweight': 'bold'},
                   wedgeprops={'linewidth': 3, 'edgecolor': 'white'})
            ax1.set_title('KATEGORI DAGILIMI', fontsize=18, fontweight='bold', color='#2c3e50', pad=25)
            
            # Pasta grafiği yazıları daha büyük ve belirgin
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_fontweight('bold')
        
        # 2. Saatlik Trend - Saat cinsinden
        df_copy = df_saat.copy()
        df_copy['Saat'] = df_copy['Zaman'].dt.hour
        saatlik = df_copy.groupby('Saat')['Süre (saat)'].sum()
        
        if not saatlik.empty:
            # Gradyan renkler
            bar_colors = ['#2980b9' if v > 0.7 else '#3498db' if v > 0.3 else '#74b9ff' for v in saatlik.values]
            bars = ax2.bar(saatlik.index, saatlik.values, color=bar_colors, alpha=0.9, width=0.6,
                          edgecolor='#1e3799', linewidth=2)
            
            ax2.set_title('SAATLIK AKTIVITE', fontsize=18, fontweight='bold', color='#2c3e50', pad=25)
            ax2.set_xlabel('Saat', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Sure (saat)', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.4, color='#bdc3c7', linewidth=1)
            ax2.set_xlim(7, 19)  # Çalışma saatleri
            ax2.set_facecolor('#ecf0f1')
            
            # Bar değerleri (saat cinsinden)
            for i, v in enumerate(saatlik.values):
                if v > 0:
                    ax2.text(saatlik.index[i], v + 0.05, f'{v:.1f}h', ha='center', va='bottom', 
                            fontweight='bold', fontsize=12, color='#2c3e50')
        
        # 3. Aktivite Sıklığı - Temiz kategoriler
        aktivite_sayisi = df.groupby('Kategori').size()
        if not aktivite_sayisi.empty:
            # Kategori isimlerini temizle
            aktivite_ascii = {}
            for kategori, sayisi in aktivite_sayisi.items():
                kategori_clean = turkce_temizle(kategori)
                aktivite_ascii[kategori_clean] = sayisi
            
            # Profesyonel renkler
            bright_colors = ['#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c'][:len(aktivite_ascii)]
            bars = ax3.bar(aktivite_ascii.keys(), aktivite_ascii.values(), 
                          color=bright_colors, alpha=0.9, edgecolor='white', linewidth=3)
            
            ax3.set_title('AKTIVITE SIKLIGI', fontsize=18, fontweight='bold', color='#2c3e50', pad=25)
            ax3.set_ylabel('Kayit Sayisi', fontsize=14, fontweight='bold')
            ax3.tick_params(axis='x', rotation=45, labelsize=12)
            ax3.set_facecolor('#ecf0f1')
            ax3.grid(True, alpha=0.4, color='#bdc3c7', axis='y', linewidth=1)
            
            # Bar değerleri
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + 0.15,
                        f'{int(height)}', ha='center', va='bottom', fontweight='bold', 
                        fontsize=13, color='#2c3e50')
        
        # 4. Verimlilik Analizi - Saat cinsinden
        verim_data = df_saat.groupby('Kategori').agg({
            'Süre (saat)': 'sum',
            'Kategori': 'count'
        }).rename(columns={'Kategori': 'Sayı'})
        
        if not verim_data.empty:
            # Premium renkli noktalar
            scatter_colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6'][:len(verim_data)]
            scatter = ax4.scatter(verim_data['Sayı'], verim_data['Süre (saat)'], 
                                c=scatter_colors, s=400, alpha=0.8, 
                                edgecolors='white', linewidth=4)
            
            # Kategori adları (temiz)
            for i, kategori in enumerate(verim_data.index):
                kategori_clean = turkce_temizle(kategori)
                ax4.annotate(kategori_clean, 
                           (verim_data.iloc[i]['Sayı'], verim_data.iloc[i]['Süre (saat)']),
                           xytext=(10, 10), textcoords='offset points', 
                           fontsize=11, fontweight='bold', color='#2c3e50',
                           bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9, edgecolor='gray'))
            
            ax4.set_title('VERIMLILIK HARITASI', fontsize=18, fontweight='bold', color='#2c3e50', pad=25)
            ax4.set_xlabel('Aktivite Sayisi', fontsize=14, fontweight='bold')
            ax4.set_ylabel('Toplam Sure (saat)', fontsize=14, fontweight='bold')
            ax4.grid(True, alpha=0.4, color='#bdc3c7', linewidth=1)
            ax4.set_facecolor('#ecf0f1')
        
        # Layout düzenle (daha fazla boşluk)
        plt.tight_layout()
        plt.subplots_adjust(hspace=0.55, wspace=0.35)
        
        # Kaydet (ultra yüksek kalite - 600 DPI)
        os.makedirs("temp", exist_ok=True)
        grafik_yolu = f"temp/{dosya_adi}"
        plt.savefig(grafik_yolu, dpi=600, bbox_inches='tight', facecolor='#f8f9fa', 
                   edgecolor='none', format='png')
        plt.close()
        
        print(f"✅ Yuksek kalite grafik kaydedildi: {grafik_yolu}")
        return grafik_yolu
    except Exception as e:
        print(f"❌ Grafik olusturma hatasi: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def kompakt_ozet_olustur(df: pd.DataFrame) -> str:
    """Kompakt özet metin oluşturur (günlük raporlar için)"""
    if df.empty:
        return "Bu dönem için veri bulunamadı."
    
    toplam_sure = df['Süre (dk)'].sum()
    kategori_sure = df.groupby('Kategori')['Süre (dk)'].sum()
    en_cok = kategori_sure.idxmax() if not kategori_sure.empty else "Yok"
    
    # Minimal özet
    ozet = f"Toplam aktif süre: {toplam_sure} dakika ({toplam_sure/60:.1f} saat)\n"
    ozet += f"Toplam kayıt sayısı: {len(df)}\n"
    
    # En çok zaman harcanan kategoriyi göster
    if not kategori_sure.empty:
        en_cok_sure = kategori_sure.max()
        ozet += f"En çok zaman: {en_cok} ({en_cok_sure} dk)\n"
        
        # Sadece en önemli kategorileri göster
        for kategori, sure in kategori_sure.head(3).items():  # Sadece ilk 3
            yuzde = (sure / toplam_sure) * 100
            ozet += f"• {kategori}: {sure} dk ({yuzde:.0f}%)\n"
    
    return ozet

def gunluk_rapor_olustur(tarih: str = None) -> str:
    """Modern görsel ağırlıklı günlük rapor oluşturur"""
    import shutil
    print("📊 Modern günlük rapor oluşturuluyor...")
    
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
    
    # Kompakt özet oluştur (daha az metin)
    ozet = kompakt_ozet_olustur(gunluk_df)
    
    # 4-panel modern dashboard grafik oluştur
    grafik_yolu = gunluk_dashboard_grafik(gunluk_df, f"gunluk_dashboard_{tarih}.png", tarih)
    
    # Gemini önerisi al (kısa tutmasını söyle)
    kisa_prompt = f"Günlük özet: {ozet}\nPuan: {puan}/10\n\nKısa ve motive edici öneride bulun (max 150 kelime)."
    gemini_cevap = al_gemini_onerisi(kisa_prompt, puan)
    
    # PDF oluştur (yeni modern tasarım)
    pdf_yolu = gunluk_rapor_pdf(tarih, ozet, puan, gemini_cevap, grafik_yolu)
    
    # Geçici dosyaları ve temp klasörünü temizle
    if grafik_yolu and os.path.exists(grafik_yolu):
        os.remove(grafik_yolu)
    
    # Temp klasörünü tamamen temizle
    try:
        shutil.rmtree("temp", ignore_errors=True)
        print("🧹 Geçici dosyalar temizlendi")
    except:
        pass
    
    return f"✅ Modern günlük rapor: {pdf_yolu}\n📊 Puan: {puan}/10"

# Test fonksiyonu
if __name__ == "__main__":
    print("🔍 Günlük Rapor Testi:")
    print(gunluk_rapor_olustur()) 