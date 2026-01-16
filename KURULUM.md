# 🚀 BATCH SİSTEM - KURULUM TALİMATI

## 📦 1. DOSYALARI ÇIKART

```bash
# İndirdiğin klasöre git
cd ~/Downloads  # veya nereye indirdiysen

# Arşivi çıkart
tar -xzf batch_system.tar.gz

# Oluşan klasöre git
cd batch_system/
```

---

## 🔑 2. API KEY GİR

```bash
# config.py dosyasını aç
nano config.py

# veya
vim config.py

# veya editörünle aç
code config.py
```

**Değiştir:**
```python
API_KEY = "PASTE_YOUR_API_KEY_HERE"
```

**Şununla:**
```python
API_KEY = "senin_gerçek_coinglass_api_keyin"
```

Kaydet ve kapat.

---

## 🧪 3. TESTİ KOŞTUR

```bash
# Python 3 kurulu mu kontrol et
python3 --version

# requests kütüphanesi gerekli
pip3 install requests

# Testi koştur
python3 run_integration_test.py
```

---

## 📊 4. SONUÇLARI KONTROL ET

Test bitince göreceksin:
- ✅ OK: 7-8/10 metrik (BAŞARILI)
- ❌ MISSING: 2-3/10 metrik (NORMAL)

**Çıktıyı buraya yapıştır!**

---

## 📁 KLASÖR YAPISI

Çıkarttıktan sonra şöyle görünecek:

```
batch_system/
├── batch2_engine/           # API Engine
│   ├── __init__.py
│   ├── coinglass.py
│   ├── response_models.py
│   └── param_manager.py
├── batch3_metrics_system/   # Metrics System
│   ├── metric_definitions.py
│   ├── metric_registry.py
│   ├── normalizer.py
│   ├── orchestrator.py
│   └── output.py
├── config.py               # API KEY BURAYA
├── run_integration_test.py # TEST RUNNER
└── README.md               # Bu dosya
```

---

## ⚠️ MUHTEMEL SORUNLAR

**"ModuleNotFoundError: No module named 'requests'"**
```bash
pip3 install requests
```

**"No API key provided"**
- config.py'yi düzenledin mi?
- API_KEY satırını değiştirdin mi?

**Test uzun sürüyor**
- Normal! 10-30 saniye sürebilir
- Her metrik için API'ye istek atıyor

---

## 🎯 ÖZET

1. ✅ Arşivi çıkart
2. ✅ config.py'ye API key gir
3. ✅ `python3 run_integration_test.py` çalıştır
4. ✅ Sonuçları buraya yapıştır

**Başarılar! 🚀**
