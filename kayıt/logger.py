# 📊 Excel Kayıt Fonksiyonları

import pandas as pd
import os
import logging
from .zaman import calculate_timestamp
from config import LOG_FILE, ANALYSIS_FILE, DEFAULT_DURATION_MINUTES

async def log_kaydi_ekle(zaman: str, kaynak: str, mesaj_turu: str, icerik: str):
    """Genel log kaydı ekler"""
    dosya = LOG_FILE
    yeni_kayit = pd.DataFrame([[zaman, kaynak, mesaj_turu, icerik]], 
                               columns=["Zaman", "Kaynak", "Mesaj Türü", "İçerik"])
    
    if os.path.exists(dosya):
        eski_kayitlar = pd.read_excel(dosya)
        tum_kayitlar = pd.concat([eski_kayitlar, yeni_kayit], ignore_index=True)
    else:
        tum_kayitlar = yeni_kayit

    tum_kayitlar.to_excel(dosya, index=False)

async def analiz_kaydi_ekle(zaman: str, kategori: str, alt_baslik: str, aciklama: str, sure: int = None):
    """Analiz verisi kaydı ekler"""
    dosya = ANALYSIS_FILE
    yeni_kayit = pd.DataFrame([[zaman, kategori, alt_baslik, aciklama, sure]], 
                               columns=["Zaman", "Kategori", "Alt Başlık", "Açıklama", "Süre (dk)"])
    
    if os.path.exists(dosya):
        eski_kayitlar = pd.read_excel(dosya)
        tum_kayitlar = pd.concat([eski_kayitlar, yeni_kayit], ignore_index=True)
    else:
        tum_kayitlar = yeni_kayit

    tum_kayitlar.to_excel(dosya, index=False)

async def mesaj_analiz_ayikla_ve_kaydet(mesaj: str):
    """Mesajı analiz edip kategorize ederek kaydeder"""
    zaman = await calculate_timestamp()
    sure = DEFAULT_DURATION_MINUTES

    if "/" in mesaj:  # En az 1 ayırıcı varsa
        parcalar = [p.strip() for p in mesaj.split("/")]
        
        if len(parcalar) >= 3:  # 3 parça: kategori/alt_baslik/aciklama
            kategori = parcalar[0]
            alt_baslik = parcalar[1]
            aciklama = parcalar[2]
        elif len(parcalar) == 2:  # 2 parça: kategori/aciklama
            kategori = parcalar[0]
            alt_baslik = "Genel"
            aciklama = parcalar[1]
        else:  # 1 parça: sadece kategori
            kategori = parcalar[0]
            alt_baslik = "Genel"
            aciklama = "Belirtilmemiş"
    else:
        # Hiç "/" yok, analiz yapma
        return

    await analiz_kaydi_ekle(zaman, kategori, alt_baslik, aciklama, sure)
    logging.info(f"Analiz kaydı eklendi: {kategori} / {alt_baslik} / {aciklama}") 