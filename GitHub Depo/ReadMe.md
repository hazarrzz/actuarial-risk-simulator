# Aktüeryal Risk Simülatörü ve Karar Destek Sistemi

Bu depo, "Hayat Dışı Sigortacılıkta Hasar Kuyruk Davranışlarının İflas Olasılığına Etkisi" başlıklı araştırma projesinin kaynak kodlarını ve simülasyon altyapısını içerir.

## Proje Bileşenleri
- **Statik Motor:** `main_simulation1.py` ile 10.000 iterasyonluk Monte Carlo simülasyonları gerçekleştirilmiştir.
- **Etkileşimli Dashboard:** `risk_explorer_dashboard.py` ile Streamlit tabanlı, parametrelerin anlık değiştirilebildiği karar destek sistemi geliştirilmiştir.

## Nasıl Çalıştırılır?
1. Gerekli kütüphaneleri yükleyin: `pip install -r requirements.txt`
2. Simülatörü başlatın: `streamlit run risk_explorer_dashboard.py`