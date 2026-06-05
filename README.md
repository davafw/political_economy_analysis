# Data-Engineering-Kelompok-4
# Analisis Pengaruh Stabilitas Politik terhadap Pertumbuhan Ekonomi Dunia Berbasis Data Terbuka dengan Pendekatan Machine Learning

**D4 Teknologi Rekayasa Perangkat Lunak - Politeknik Negeri Madiun**

## 👥 Kontributor 
| Nama Lengkap | NIM | Peran |
| :--- | :---: | :---: |
| Alivia Rizka Wardani | 234311035 | Data Analyst |
| Dava Febri Wardana | 234311039 | Project Manager |
| Moch. Arrizal Syach Putra | 234311047 | Data Engineer |

## 📖 Deskripsi Proyek 
Proyek ini dikembangkan untuk mengidentifikasi pola hubungan antara stabilitas politik (diukur melalui *Democracy Index*) dengan pertumbuhan ekonomi global (*GDP Growth* dan Inflasi) pada rentang tahun 2006–2024. Data diekstraksi dari sumber terbuka (World Bank dan Our World in Data), dibersihkan dan ditransformasi, lalu dimuat ke dalam *cloud database* PostgreSQL (Aiven). Tujuannya adalah membangun sistem analitik terpusat yang mendukung eksplorasi data dan prediksi menggunakan Machine Learning.

## 🎯 Manfaat Data / Use Case
- **Tujuan Proyek:** Menyediakan dataset global yang terintegrasi dan tervalidasi untuk menganalisis dampak kondisi politik suatu negara terhadap stabilitas ekonominya, serta mengotomatisasi pipeline dari penarikan data hingga visualisasi.
- **Manfaat:** Memberikan wawasan berbasis data bagi peneliti ekonomi dan pembuat kebijakan, membuka peluang penggunaan Machine Learning untuk memprediksi kategori pertumbuhan ekonomi berdasarkan indikator politik, serta menjadi referensi implementasi *Data Engineering* untuk pengolahan data panel berskala global.

## 📊 Serving Analisis
Data hasil pipeline ETL disimpan secara *live* dalam PostgreSQL di layanan *cloud* Aiven. Penyimpanan terpusat ini memungkinkan eksplorasi data lebih lanjut menggunakan Google Colab, serta disajikan dalam bentuk *dashboard* visualisasi interaktif (menggunakan Looker Studio atau Streamlit). Analisis difokuskan pada korelasi antar-indikator, perbandingan antar-negara (menggunakan kode ISO), dan tren historis selama krisis global (seperti pandemi 2020).

## 🤖 Serving Machine Learning
Dataset yang telah bersih (*clean data*) digunakan untuk membangun model Machine Learning berjenis **Klasifikasi** (seperti *Random Forest* atau *Decision Tree*). Model ini bertugas memprediksi dan mengelompokkan negara ke dalam kategori pertumbuhan ekonomi (*High Growth*, *Stagnant*, *Recession*) berdasarkan input skor demokrasi dan tingkat inflasi. Hasil prediksi ini divisualisasikan bersama dengan analisis data historis untuk menemukan pola tersembunyi.

## ⚙️ Pipeline ETL

### 1. Extract (Pengambilan Data)
- **Sumber Data:**
  - Democracy Index (2006-2024) – *Our World in Data* (Format: CSV)-https://ourworldindata.org/grapher/democracy-index-eiu
  - Inflation, Consumer Prices – *World Bank* (Format: CSV)-https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG
  - GDP Growth (Annual %) – *World Bank* (Format: CSV)-https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG
- **Metode Pengambilan:**
  - Penarikan data *direct download* (CSV) untuk data Our World in Data dan World Bank.

### 2. Transform (Pembersihan & Transformasi)
- **Pembersihan Data:**
  - Menghapus kolom yang tidak relevan dan menstandarkan penamaan kolom menjadi format *snake_case*.
  - Menangani *missing values* (terutama untuk negara kecil atau wilayah konflik) menggunakan metode imputasi atau *drop*.
  - Menstandarkan kunci penggabungan menggunakan **ISO Alpha-3 Country Code** (misal: IDN, USA) agar tidak terjadi ketidakcocokan nama negara saat *merging*.
- **Transformasi Data:**
  - Menggabungkan (*merge*) ketiga dataset berdasarkan `country_code` dan `year` menjadi format data panel yang konsisten.
  - Membuat fitur baru (misalnya: label `kategori_pertumbuhan`) untuk mempermudah pelatihan model Machine Learning.

### 3. Load (Pemindahan ke Target)
- **Target:** Database PostgreSQL yang di-*hosting* secara *online* di Aiven (*Cloud Database*).
- **Proses Load:**
  - Data akhir yang sudah berbentuk *DataFrame* dikirim langsung ke PostgreSQL menggunakan fungsi `to_sql()` dari *library* Pandas.
  - Koneksi ke Aiven diatur menggunakan objek *engine* dari `SQLAlchemy`.
  - Menerapkan penanganan integritas data untuk mencegah duplikasi entri (menggunakan kombinasi *primary key* `country_code` dan `year`).

## 🏗️ Arsitektur / Workflow ETL
- **Alur Modular:** Proses ETL dirancang secara sekuensial di dalam Google Colab. Dimulai dari ekstraksi data (via API/CSV), dilanjutkan dengan proses pembersihan dan transformasi menggunakan Pandas, dan diakhiri dengan proses *load* data ke PostgreSQL (Aiven) melalui *engine* SQLAlchemy. Data di Aiven kemudian siap diakses oleh *tools* analitik.
- **Teknologi yang Digunakan:**
  - **ETL:** Python, Pandas, Numpy, SQLAlchemy, `wbgapi`
  - **Database:** PostgreSQL (Aiven)
  - **Machine Learning:** Scikit-Learn
  - **Visualisasi:** Looker Studio / Streamlit / Matplotlib / Seaborn

## 💻 Kode Program
- **Struktur Kode:**
  - Tersusun rapi dan terbagi menjadi dua ruang kerja (Notebook) utama: satu untuk Pipeline ETL dan satu untuk *Machine Learning*.
  - Menggunakan penamaan fungsi dan variabel yang deskriptif untuk memastikan *pipeline* dapat dibaca dan digunakan ulang.
- **Machine Learning:**
  - Menggunakan algoritma klasifikasi untuk analisis prediktif.

## 🔗 Link Proyek
- **ETL Pipeline:** `[Isi dengan link Google Colab atau file .ipynb di GitHub]`
- **Machine Learning:** ``
- **Dashboard / Visualisasi:** ``
