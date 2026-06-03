# Akıllı Otopark Simülasyon Sistemi

## Proje Açıklaması

Bu proje, akıllı otopark yönetimini simüle eden bir Python uygulamasıdır. SimPy ile ayrık olay simülasyonu yürütülürken Streamlit ile etkileşimli bir kullanıcı arayüzü sunulur. Amaç, park yeri doluluk durumunu gerçek zamanlı izlemek, araç tipine göre uygun yer atamak ve ödeme/raporlama verilerini görselleştirmektir.

## Özellikler

- **Simülasyon Motoru:** SimPy tabanlı geliş-park-çıkış süreçleri
- **Etkileşimli Arayüz:** Streamlit ile gerçek zamanlı görselleştirme
- **Dinamik Park Izgarası:** Seçili kat için 10 park yeri 5×2 düzeninde gösterim
- **Metrik Panelleri:** Doluluk oranı, elektrikli araç sayısı ve engelli araç rezervasyonları
- **Detaylı Loglar:** Araç giriş/çıkış işlemleri, ödeme türleri ve nedenleri
- **Finansal Özet:** Ödeme dağılımı ve toplam gelir raporu
- **CSV İndirme:** İşlem detaylarını dışa aktarma seçeneği
- **Deterministik Simülasyon:** Seed değeri kullanarak tekrarlanabilir sonuçlar

## Kurulum

1. Python 3.8 veya üzeri kurulu olduğundan emin olun.
2. Proje klasörüne gidin:
   ```bash
   cd "C:\Users\Win11\Desktop\otopark yönetim"
   ```
3. Gerekli paketleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

## Uygulamayı Çalıştırma

Aşağıdaki komutla uygulamayı başlatın:

```bash
streamlit run app.py
```

Windows ortamında alternatif:

```bash
py -3 -m streamlit run app.py
```

Uygulama açıldığında tarayıcıda otomatik olarak `http://localhost:8501` adresi görüntülenecektir.

## Kullanım

- Sağ kenardaki panelden simülasyon senaryosunu seçin.
- "Deterministik Simülasyon" seçeneğini aktif hale getirip seed değeri girerek aynı sonuçları tekrar üretebilirsiniz.
- Zaman kaydırıcısı ile simülasyonun farklı zaman noktalarını görüntüleyin.
- Park yeri ızgarasında seçili kat için dolu/boş durumu ve araç tipi raporlarını inceleyin.
- Log aramasını kullanarak belirli kayıtları filtreleyin.
- "📊 Özet Raporu" altından işlem detaylarını CSV olarak indirin.

## Teknik Detaylar

- Park yerleri programatik olarak oluşturulur ve proje varsayılan 30 adet spotu kullanır.
- Araç tipine göre özel yer atama kuralları uygulanır: elektrikli, engelli ve LPG araçları için öncelikler.
- Ödeme metodu verileri `payment_method` olarak kaydedilir ve toplam gelir hesaplanır.
- `main.py` simülasyon süreçlerini yönetir; `app.py` kullanıcı arayüzünü ve raporlama görünümünü sağlar.

## Notlar

- `requirements.txt` dosyasındaki paketler, uygulamanın çalışması için gerekli ana bağımlılıkları içerir.
- Dosya yollarında boşluk ve Türkçe karakter kullanımı bazen terminal komutlarında dikkat gerektirebilir.
- Uygulamayı ilk çalıştırmadan önce paketlerin doğru kurulduğundan emin olun.

## Hızlı Kontrol

Derleme/syntax kontrolü için:

```bash
py -3 -m py_compile main.py app.py
```

## Geliştirme Önerileri

- Raporlama paneline daha fazla filtre eklemek
- Export seçeneklerini Excel ve PDF olarak genişletmek
- Docker desteği eklemek
- Unit testler ile simülasyon mantığını doğrulamak
