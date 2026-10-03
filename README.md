<div align="center">
  <h1>🤖 BusinessOS AI</h1>
  <p><strong>Küçük ve orta ölçekli işletmeler için yapay zekâ destekli çok ajanlı işletme yönetim platformu</strong></p>
  
  <p>
    <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python" />
    <img src="https://img.shields.io/badge/TypeScript-5.0-blue.svg" alt="TypeScript" />
    <img src="https://img.shields.io/badge/FastAPI-0.100+-green.svg" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Next.js-16-black.svg" alt="Next.js" />
    <img src="https://img.shields.io/badge/PostgreSQL-pgvector-blue.svg" alt="PostgreSQL" />
    <img src="https://img.shields.io/badge/OpenAI-GPT--4-orange.svg" alt="OpenAI" />
  </p>
</div>

---

## 📋 1. Proje Hakkında

**BusinessOS AI**, küçük ve orta ölçekli işletmelerin (KOBİ) dijital dönüşümünü hızlandırmak için geliştirilmiş, **Çok Ajanlı (Multi-Agent) Yapay Zekâ** mimarisine sahip yeni nesil bir işletme yönetim (ERP/CRM) platformudur. Bu proje, üniversite bitirme tezi kapsamında geliştirilmiştir.

**Çözdüğü Problem:** Geleneksel işletme yazılımlarının karmaşık ve pahalı yapısına karşı; doğal dilde komut alabilen, işletme verilerini (RAG - Retrieval-Augmented Generation ile) okuyarak anında çözüm üretebilen akıllı bir sistem sunar.

**Temel İnovasyon:** **Multi-Agent AI + RAG (Gelişmiş Bilgi Getirimi)**. İşletme verileriniz kendi veritabanınızda vektörleştirilir ve her biri kendi alanında uzmanlaşmış yapay zekâ ajanları tarafından ortaklaşa kullanılır.

---

## ✨ 2. Özellikler

### 🧠 Yapay Zekâ Ajanları (Multi-Agent Sistemi)
Sistem, bir orkestratör ve ona bağlı 5 uzman ajandan (toplam 6 ajan yapısı) oluşur:
1. **Yönlendirici (Orchestrator) Ajan:** Kullanıcı taleplerini analiz ederek (Intent Classification) soruyu en doğru uzman ajana yönlendirir.
2. **Müşteri Destek Ajanı:** İşletmenin bilgi tabanını (RAG) kullanarak SSS, çalışma saatleri, iadeler ve genel müşteri sorularını yanıtlar.
3. **Randevu Ajanı:** Takvim müsaitliğini kontrol eder, yeni randevu oluşturur, iptal eder ve randevuları listeler.
4. **Satış ve Öneri Ajanı:** Mevcut ürün ve hizmetleri tarar, müşterinin ihtiyacına en uygun paketi ve fiyatlandırmayı önerir.
5. **Finansal Analiz Ajanı:** İşletmenin verilerini okuyarak istatistikler, kârlılık raporları ve performans analizi sunar.
6. **Pazarlama Ajanı:** Hedef kitleye özel kampanya fikirleri, promosyon stratejileri ve sosyal medya içerikleri üretir.

### 🏢 Temel Modüller
- **Kimlik ve Çoklu Kiracı Yönetimi (Auth & Multi-tenant):** Her işletme kendi izole veri alanında çalışır. Ekip üyeleri yönetimi ve davet sistemi.
- **Müşteri Yönetimi (CRM):** Müşteri kayıtları, geçmiş işlemler ve iletişim bilgileri.
- **Randevu Sistemi:** Gerçek zamanlı takvim yönetimi ve hatırlatıcılar.
- **Fatura ve Finans:** Fatura kesme, ödeme takibi ve gelir/gider analizi.
- **Bilgi Tabanı (Document & RAG):** İşletmeye ait PDF, metin ve dokümanların yüklenip pgvector ile indekslenmesi.
- **Bildirimler:** Gerçek zamanlı (Real-time) anlık bildirim sistemi.

---

## 🏗️ 3. Mimari (Architecture)

Proje modern, ölçeklenebilir ve mikroservis uyumlu bir mimaride tasarlanmıştır.

```mermaid
graph TD
    Client[Web İstemcisi / Next.js] --> |REST API / WebSocket| FastAPI[FastAPI Backend]
    
    subgraph Yapay Zeka Katmanı
        FastAPI --> Orchestrator[Orchestrator Ajan]
        Orchestrator --> |Intent Classification| Specialist1[Müşteri Destek]
        Orchestrator --> |Intent Classification| Specialist2[Randevu Ajanı]
        Orchestrator --> |Intent Classification| Specialist3[Satış Ajanı]
        Orchestrator --> |Intent Classification| Specialist4[Analiz Ajanı]
        Orchestrator --> |Intent Classification| Specialist5[Pazarlama Ajanı]
    end
    
    subgraph Veri Katmanı
        Specialist1 -.-> |Vektör Arama| RAG[RAG / Embedding Modülü]
        Specialist3 -.-> |Vektör Arama| RAG
        Specialist5 -.-> |Vektör Arama| RAG
        RAG --> |pgvector| DB[(PostgreSQL)]
        FastAPI --> |SQLAlchemy| DB
    end
    
    Yapay Zeka Katmanı --> OpenAI[OpenAI GPT-4 API]
```

**Çalışma Akışı:** Kullanıcı (veya işletme sahibi) sohbet ekranından bir komut girdiğinde, **Orkestratör Ajan** metni analiz eder. İhtiyaca göre (örneğin randevu almak) ilgili **Uzman Ajanı** çağırır. Uzman ajan, veritabanından güncel bilgileri (RAG) çeker, OpenAI üzerinden işler ve kullanıcıya doğal dilde sonuç veya fonksiyon çağrısı (Function Calling) döndürür.

---

## 🛠️ 4. Teknoloji Yığını (Tech Stack)

| Teknoloji | Kullanım Amacı | Sürüm |
| :--- | :--- | :--- |
| **Python** | Backend dili | 3.12+ |
| **FastAPI** | Yüksek performanslı asenkron API | Son Sürüm |
| **SQLAlchemy & Alembic** | ORM ve Veritabanı Migrasyonları | 2.0+ |
| **OpenAI API** | LLM ve Multi-Agent Zekâsı | GPT-4o / 3.5 |
| **Next.js** | Frontend Framework | 16.x |
| **TypeScript** | Frontend Tip Güvenliği | 5.x |
| **Tailwind CSS** | Modern ve hızlı arayüz tasarımı | 4.x |
| **Recharts & Lucide** | Veri görselleştirme ve ikonlar | Son Sürüm |
| **PostgreSQL & pgvector** | İlişkisel ve Vektörel Veritabanı (RAG için) | 15+ |
| **Docker & Compose** | Konteynerizasyon ve Altyapı | Son Sürüm |

---

## 📁 5. Proje Yapısı (Project Structure)

```text
BusinessOS-AI/
├── backend/                  # Python FastAPI Sunucusu
│   ├── app/
│   │   ├── ai/               # AI Ajanları ve Orchestrator (base, specialists, openai, rag)
│   │   ├── api/              # API Router (Tüm modüllerin rotaları)
│   │   ├── core/             # Ayarlar (Config) ve Güvenlik (Security)
│   │   ├── db/               # PostgreSQL Bağlantısı ve Session (pgvector)
│   │   └── modules/          # İş mantığı modülleri (auth, business, customers, vb.)
│   ├── requirements.txt      # Backend bağımlılıkları
│   └── main.py               # FastAPI başlangıç dosyası
│
├── frontend/                 # Next.js 16 Web Uygulaması
│   ├── app/
│   │   ├── (dashboard)/      # Kontrol Paneli Sayfaları (customers, invoices, vb.)
│   │   └── layout.tsx
│   ├── components/           # Tekrar kullanılabilir UI (Sidebar, Butonlar)
│   └── package.json          # Frontend bağımlılıkları
│
└── infrastructure/           # Dağıtım ve Altyapı
    └── docker-compose.yml    # Veritabanı ve servis orkestrasyonu
```

---

## 🚀 6. Kurulum (Installation)

### Ön Koşullar
- [Node.js](https://nodejs.org/) (v20+)
- [Python](https://www.python.org/) (3.12+)
- [Docker](https://www.docker.com/) ve Docker Compose
- OpenAI API Anahtarı

### Adım Adım Kurulum

**1. Repoyu Klonlayın**
```bash
git clone https://github.com/KULLANICI_ADI/BusinessOS-AI-anti.git
cd BusinessOS-AI-anti
```

**2. Altyapı ve Veritabanı (Docker)**
PostgreSQL ve pgvector eklentisini başlatmak için:
```bash
cd infrastructure
docker-compose up -d
```

**3. Backend Kurulumu**
```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # Windows için: venv\Scripts\activate
pip install -r requirements.txt

# .env dosyasını oluşturun ve yapılandırın
cp .env.example .env

# Veritabanı migrasyonlarını çalıştırın
alembic upgrade head

# Backend sunucusunu başlatın
uvicorn app.main:app --reload --port 8000
```

**4. Frontend Kurulumu**
```bash
cd ../frontend
npm install
npm run dev
```

Uygulama `http://localhost:3000` adresinde çalışacaktır. API dökümantasyonu ise `http://localhost:8000/docs` adresinde bulunabilir.

### `.env` Şablonu (Backend)
```env
PROJECT_NAME="BusinessOS AI"
DATABASE_URL="postgresql://postgres:password@localhost:5432/business_os"
OPENAI_API_KEY="sk-..."
SECRET_KEY="gizli_anahtariniz"
CORS_ORIGINS="http://localhost:3000"
```

---

## 📡 7. API Endpoints

Aşağıda temel API endpoint'lerinin bir özeti bulunmaktadır (Swagger UI üzerinden tamamına erişilebilir):

| Modül | Metot | Endpoint | Açıklama |
| :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/login` | Kullanıcı girişi ve JWT token üretimi |
| **Business** | `GET` | `/api/v1/business/` | Kiracıya (işletmeye) ait genel bilgileri getirir |
| **Customers**| `GET` | `/api/v1/customers/` | Müşteri listesini getirir |
| **Customers**| `POST` | `/api/v1/customers/` | Yeni müşteri ekler |
| **Appointments**| `POST` | `/api/v1/appointments/`| Yeni randevu oluşturur |
| **Invoices** | `POST` | `/api/v1/invoices/` | Yeni fatura keser |
| **Documents**| `POST` | `/api/v1/documents/upload`| RAG için belge yükler ve vektörleştirir |
| **Chat (AI)**| `POST` | `/api/v1/chat/message` | Ajanlara doğal dilde komut gönderir |
| **Admin** | `GET` | `/api/v1/admin/stats` | Sistem geneli istatistikleri getirir |

---

## 🧪 8. Testler

Proje kod kalitesini artırmak için birim (unit) testler ve entegrasyon testleri barındırır.

**Backend Testlerini Çalıştırmak İçin:**
```bash
cd backend
pytest -v --cov=app
```
*Kapsam: RAG vektör aramaları, Ajan yönlendirme (Orchestrator) doğruluğu, API uç noktalarının güvenlik doğrulukları.*

---

## 📸 9. Ekran Görüntüleri

> *Geliştirme tamamlandıkça uygulamanın ekran görüntüleri (Dashboard, Yapay Zeka Sohbet Ekranı, Randevu Takvimi vb.) buraya eklenecektir.*

<div align="center">
  <img src="https://via.placeholder.com/800x450?text=Dashboard+Ekran+Goruntusu" alt="Dashboard" width="80%">
</div>

---

## 🗺️ 10. Yol Haritası (Roadmap)

- [x] Temel veritabanı şemaları ve Multi-tenant yapısı
- [x] FastAPI ve Next.js kurulumları
- [x] RAG Sistemi ve pgvector entegrasyonu
- [x] Orchestrator ve Uzman Ajanların (5 adet) entegrasyonu
- [x] Müşteri, Randevu ve Fatura modülleri
- [ ] WhatsApp ve E-posta bildirim entegrasyonları
- [ ] Gelişmiş Finansal Grafik Raporları
- [ ] Sesli komut desteği

---

## 👨‍💻 11. Geliştirici

**[Adınız Soyadınız]**  
*Üniversite Adı - Bilgisayar Mühendisliği / Yazılım Mühendisliği Bölümü*  
Bitirme Tezi Projesi - 2026

---
> 💡 *Bu proje, KOBİ'lerin yapay zekâ devriminden en yüksek verimle faydalanması amacıyla akademik bir çalışma olarak geliştirilmiştir.*
