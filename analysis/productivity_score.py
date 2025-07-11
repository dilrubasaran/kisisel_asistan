# 📊 Üretkenlik Puanlama Sistemi (10 Puan Üzerinden)

import pandas as pd
from typing import Tuple, List

def hesapla_urekenlik_puani(df: pd.DataFrame) -> Tuple[int, List[str]]:
    """Verilen DataFrame'den üretkenlik puanı hesaplar (10 puan üzerinden)"""
    puan = 0
    yorumlar = []

    toplam_sure = df["Süre (dk)"].sum() / 60
    calisma_sure = df[df["Kategori"] == "Çalışma"]["Süre (dk)"].sum() / 60
    dinlenme_sure = df[df["Kategori"] == "Dinlenme"]["Süre (dk)"].sum() / 60
    aciklamalar = df["Açıklama"].dropna().tolist()

    # 10 puan üzerinden hesaplama
    if toplam_sure >= 6:
        puan += 4  # 40% -> 4 puan
        yorumlar.append("Toplam 6 saatten fazla çalıştın.")
    if calisma_sure >= 4:
        puan += 3  # 30% -> 3 puan
        yorumlar.append("Yoğun çalıştın.")
    if dinlenme_sure <= 2:
        puan += 2  # 20% -> 2 puan
        yorumlar.append("Odak seviyen yüksekti.")
    if len(aciklamalar) > 2:
        puan += 1  # 10% -> 1 puan
        yorumlar.append("Açıklamalarla detaylı notlar tuttun.")

    return int(puan), yorumlar 