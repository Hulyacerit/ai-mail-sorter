# ai-mail-sorter


***

```markdown
# 🤖 AI Mail Sorter (Kurumsal AI Mail Asistanı)

Bu proje, şirketlere ve ekiplere gelen yoğun e-posta trafiğini yönetmek için geliştirilmiş yapay zeka destekli bir e-posta asistanıdır. Gelen e-postaları saniyeler içinde okur, konusuna göre kategorize eder, aciliyet derecesini belirler ve kullanıcıya göndermeye hazır profesyonel bir taslak yanıt sunar.

⚡ **Geliştirme Notu:** Bu proje, modern yapay zeka destekli kodlama süreçlerini deneyimlemek amacıyla **Cursor AI** kod editörü kullanılarak modüler ve hızlı bir mimaride geliştirilmiştir.

## ✨ Özellikler

* **Akıllı Analiz:** Google Gemini AI gücüyle e-posta metinlerinin niyetini ve içeriğini doğru bir şekilde anlar.
* **Otomatik Sınıflandırma:** E-postaları ilgili departmanlara (Satış, Destek, İnsan Kaynakları vb.) göre kategorize eder.
* **Aciliyet Tespiti:** Kriz veya acil durum içeren e-postaları tespit ederek aciliyet derecesini (Düşük, Orta, Yüksek) belirler.
* **Taslak Yanıt Üretimi:** E-postanın bağlamına ve şirket diline uygun, profesyonel ve çözüm odaklı taslak cevaplar hazırlar.
* **Modern Arayüz:** Streamlit ile geliştirilmiş, kullanıcı dostu ve hızlı yanıt veren web arayüzü.
* **Hata Yönetimi (Fallback):** API veya bağlantı kopukluklarında sistemin çökmesini engelleyen güvenli mimari.

## 🛠️ Kullanılan Teknolojiler

* **Dil:** Python
* **Arayüz (UI):** Streamlit
* **Yapay Zeka (LLM):** Google Gemini API (`gemini-1.5-flash` modeli)
* **Araçlar:** Cursor AI Editor, Git & GitHub, Dotenv

## 🚀 Kurulum ve Çalıştırma

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyebilirsiniz.

### 1. Depoyu Klonlayın
```bash
git clone [https://github.com/Hulyacerit/ai-mail-sorter.git](https://github.com/Hulyacerit/ai-mail-sorter.git)
cd ai-mail-sorter
```

### 2. Gerekli Kütüphaneleri Yükleyin
```bash
pip install -r requirements.txt
```

### 3. Çevre Değişkenlerini Ayarlayın (.env)
Projenin ana dizininde `.env` adında bir dosya oluşturun ve Google AI Studio'dan aldığınız API anahtarınızı içine ekleyin:
```text
GEMINI_API_KEY=sizin_api_anahtariniz_buraya_gelecek
```

### 4. Uygulamayı Başlatın
```bash
streamlit run app.py
```
Uygulama otomatik olarak tarayıcınızda `http://localhost:8501` adresinde açılacaktır.

## 📂 Proje Yapısı

```text
ai-mail-sorter/
├── core/
│   ├── __init__.py
│   └── agent.py         # Gemini API entegrasyonu ve analiz mantığı
├── app.py               # Streamlit web arayüzü
├── requirements.txt     # Bağımlılıklar
├── .env                 # API Anahtarları (Git'ten gizlenmiştir)
└── .gitignore           # Git tarafından takip edilmeyecek dosyalar
```

## 🤝 Katkıda Bulunma

Geliştirmelere ve yeni fikirlere her zaman açığız! Katkıda bulunmak isterseniz lütfen bir `Pull Request` açmaktan veya sorun bildirmek için bir `Issue` oluşturmaktan çekinmeyin.
```

***

