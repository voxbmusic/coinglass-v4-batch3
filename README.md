# 🚀 BATCH 2 + BATCH 3 - READY TO TEST

## ⚡ HIZLI BAŞLANGIÇ (3 ADIM)

### 1️⃣ API KEY GİR (TEK SEFER)

```bash
# config.py dosyasını aç
nano config.py

# veya
vim config.py

# veya kendi editörünle aç
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

### 2️⃣ TESTİ KOŞTUR

```bash
python3 run_integration_test.py
```

Hepsi bu kadar! Script otomatik olarak config.py'den key'i okuyacak.

---

### 3️⃣ SONUÇLARI İNCELE

Test bitince şunları göreceksin:
- ✅ OK: 7-8/10 (BAŞARILI)
- ❌ MISSING: 2-3/10 (NORMAL)
- 📄 Output dosyaları: `/tmp/integration_test_output.json` ve `.txt`

**Beklenen:**
```
Daily metrics OK: 7/10  ← İDEAL
Daily metrics OK: 8/10  ← MÜKEMMEL
```

**Eğer 7+ OK gelirse:**
✅ Sistem canlıya hazır
✅ Final paket oluşturulabilir

---

## 📋 ALTERNATIF YÖNTEMLER

Eğer config.py kullanmak istemezsen:

**Yöntem 2: Komut satırı**
```bash
python3 run_integration_test.py --api-key SENIN_KEYIN
```

**Yöntem 3: Environment variable**
```bash
export COINGLASS_API_KEY="senin_keyin"
python3 run_integration_test.py
```

---

## 🔒 GÜVENLİK

- `config.py` otomatik olarak `.gitignore`'a eklendi
- API key asla commit edilmeyecek
- Güvenle kullanabilirsin

---

## 📊 SİSTEM DURUMU

**HAZIR:**
- ✅ Batch 2 (API Engine)
- ✅ Batch 3 (Metrics System)
- ✅ Entegrasyon
- ✅ Test Runner

**EKSİK:**
- 🔑 API Key (senin gireceğin)

---

## ❓ SORUN ÇIKARSA

**"No API key provided" hatası:**
- config.py'yi kontrol et
- API_KEY = "..." kısmını düzgün doldurdun mu?

**"Import error" hatası:**
- Doğru klasörde misin? `/home/claude/`
- Python 3 kullanıyor musun? `python3 --version`

**Test başarısız (< 7 OK):**
- API key doğru mu?
- Plan tier yeterli mi? (bazı endpoint'ler premium gerektirir)
- Sonuçları Lupo'ya göster, analiz eder

---

## 🎯 ÖZET

1. **config.py** aç → API key yapıştır → kaydet
2. **python3 run_integration_test.py** çalıştır
3. **Sonuçları** kontrol et (7+ OK bekleniyor)
4. **Lupo'ya** raporla

**Bu kadar basit!** 🚀
