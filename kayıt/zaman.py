# ⏰ Zaman Yardımcı Fonksiyonları

from datetime import datetime

def zaman_al():
    """Şuanki zamanı string olarak döndürür"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def calculate_timestamp():
    """Async zaman hesaplama fonksiyonu"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S") 