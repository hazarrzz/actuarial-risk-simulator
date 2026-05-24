# Aktüeryal Risk Simülatörü ve Karar Destek Sistemi

Bu proje, "Hayat Dışı Sigortacılıkta Hasar Kuyruk Davranışlarının İflas Olasılığına Etkisi" başlıklı lisans bitirme projesi kapsamında geliştirilmiştir. Çalışma, geleneksel ince kuyruklu (Log-Normal) ve katastrofik kalın kuyruklu (Pareto) hasar dağılımlarının sigorta şirketlerinin iflas riskleri üzerindeki etkilerini karşılaştırmalı olarak analiz etmektedir.

## Proje Bileşenleri

- **Monte Carlo Simülasyon Motoru (`main_simulation1.py`):** 10.000 iterasyonluk bileşik Poisson risk süreci altında, başlangıç sermayesi ve güvenlik yüklemesi değişkenleri ile iflas olasılığı matrislerini (ısı haritalarını) üretir.
- **Etkileşimli Karar Destek Sistemi (`risk_explorer_dashboard.py`):** Streamlit tabanlı arayüz; $\alpha$ (kuyruk kalınlığı), $u$ (sermaye) ve $d$ (reasürans limiti) gibi parametrelerin anlık değiştirilmesine ve sonuçların (VaR, TVaR) görselleştirilmesine olanak tanır.

## Gereksinimler

Projenin yerel ortamda çalışması için gerekli kütüphaneler:

```bash
pip install -r requirements.txt

Nasıl Çalıştırılır?
Gerekli kütüphaneleri yükledikten sonra terminalde proje dizinine gidin.

Dashboard'u başlatmak için şu komutu kullanın:
streamlit run risk_explorer_dashboard.py

Literatür ve Metodoloji
Çalışma, Solvency II standartları ve güncel aktüeryal literatür (Klugman vd., Bulut & Erdemir) baz alınarak kurgulanmıştır.

Bu çalışma, [Çukurova Üniversitesi/İstatistik] Bitirme Araştırma Projesi kapsamında hazırlanmıştır.
