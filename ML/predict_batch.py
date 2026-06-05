import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import os
from datetime import datetime

# =========================================================================
# 1. KONFIGURASI PATH & DATABASE
# =========================================================================
DB_PATH = 'stabilitas_ekonomi_politik.db'

def cetak_log(pesan):
    """Fungsi pembantu untuk mencetak log sistem dengan timestamp murni terminal"""
    waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{waktu}] [ML-ENGINE] {pesan}")

# Validasi Keberadaan Database
if not os.path.exists(DB_PATH):
    cetak_log(f"EROR: Database '{DB_PATH}' tidak ditemukan!")
    exit(1)

cetak_log("Memulai pipeline otomatisasi Machine Learning tanpa interface...")

# =========================================================================
# 2. PENGAMBILAN DATA DARI SQL (EXTRACT FOR ML)
# =========================================================================
conn = sqlite3.connect(DB_PATH)

cetak_log("Membaca data fitur dari tabel 'tabel_features_ml'...")
query_source = "SELECT * FROM tabel_features_ml"
df_master = pd.read_sql_query(query_source, conn)

# =========================================================================
# 3. PRE-PROCESSING & PELATIHAN MODEL (TRAINING ON THE FLY)
# =========================================================================
# Definisikan Fitur Prediktor
fitur_cols = ['Democracy Index', 'Inflation_Value', 'GDP_Growth_Lag1', 'Inflation_Lag1', 'Democracy_Index_Lag1']

# Membuat label target tiruan berbasis logika resesi (GDP < 0) untuk melatih model
df_master['Is_Recession'] = (df_master['GDP_Growth_Value'] < 0).astype(int)

# Hapus baris yang memiliki nilai kosong pada fitur utama
df_clean = df_master.dropna(subset=fitur_cols)

X = df_clean[fitur_cols]
y = df_clean['Is_Recession']

cetak_log(f"Melatih model Random Forest menggunakan {len(df_clean)} baris data historis...")
model_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
model_classifier.fit(X, y)
cetak_log("Pelatihan model selesai dengan sukses.")

# =========================================================================
# 4. PROSES PREDIKSI BATCH (SCORING)
# =========================================================================
cetak_log("Menjalankan prediksi risiko resesi untuk seluruh baris data...")

# Melakukan prediksi kelas (0 atau 1) dan probabilitasnya (%)
df_clean['Prediksi_Resesi'] = model_classifier.predict(X)
df_clean['Probabilitas_Resesi_Persen'] = model_classifier.predict_proba(X)[:, 1] * 100

# Menentukan status teks berdasarkan hasil prediksi kelas biner
df_clean['Status_Sistem'] = df_clean['Prediksi_Resesi'].apply(lambda x: 'BAHAYA RESESI' if x == 1 else 'AMAN')

# Memilih kolom-kolom penting saja untuk disimpan sebagai output akhir
kolom_output = [
    'Country Name', 'Country Code', 'Year', 
    'GDP_Growth_Value', 'Inflation_Value', 'Democracy Index',
    'Probabilitas_Resesi_Persen', 'Status_Sistem'
]
df_output_final = df_clean[kolom_output]

# =========================================================================
# 5. MENULIS KEMBALI HASIL KE DATABASE (LOAD TO TARGET TABLE)
# =========================================================================
cetak_log("Memindahkan hasil prediksi ke tabel target 'tabel_output_prediksi' di SQLite...")

# Jika tabel sudah ada, timpa dengan data hasil kalkulasi terbaru (if_exists='replace')
df_output_final.to_sql('tabel_output_prediksi', conn, if_exists='replace', index=False)

# Tutup koneksi database
conn.close()

cetak_log("SUKSES: Seluruh hasil prediksi telah disimpan kembali ke database SQL.")
cetak_log("Pipeline ML selesai dijalankan secara headless.")
print("="*60)