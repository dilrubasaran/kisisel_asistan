# 📊 Üretkenlik Puanlama Sistemi

import pandas as pd
from typing import Tuple, List

def hesapla_urekenlik_puani(df: pd.DataFrame) -> Tuple[int, List[str]]:
    """Verilen DataFrame'den üretkenlik puanı hesaplar"""
    puan = 0
    yorumlar = []

    toplam_sure = df["Süre (dk)"].sum() / 60
    calisma_sure = df[df["Kategori"] == "Çalışma"]["Süre (dk)"].sum() / 60
    dinlenme_sure = df[df["Kategori"] == "Dinlenme"]["Süre (dk)"].sum() / 60
    aciklamalar = df["Açıklama"].dropna().tolist()

    if toplam_sure >= 6:
        puan += 40
        yorumlar.append("Toplam 6 saatten fazla çalıştın.")
    if calisma_sure >= 4:
        puan += 30
        yorumlar.append("Yoğun çalıştın.")
    if dinlenme_sure <= 2:
        puan += 20
        yorumlar.append("Odak seviyen yüksekti.")
    if len(aciklamalar) > 2:
        puan += 10
        yorumlar.append("Açıklamalarla detaylı notlar tuttun.")

    return int(puan), yorumlar 