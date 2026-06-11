import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import os
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

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
# 1. KEMBALI KE FITUR INTI (Buang kolom region yang menjadi noise)
fitur_inti = ['Democracy Index', 'Inflation_Value', 'GDP_Growth_Lag1', 'Inflation_Lag1', 'Democracy_Index_Lag1']

df_master['Is_Recession'] = (df_master['GDP_Growth_Value'] < 0).astype(int)
df_clean = df_master.dropna(subset=fitur_inti)

X = df_clean[fitur_inti]
y = df_clean['Is_Recession']

# 2. ATURAN 80/20
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

cetak_log(f"Total Data Bersih: {len(X)} baris.")
cetak_log(f"-> Menggunakan {len(fitur_inti)} variabel metrik ekonomi murni (Tanpa Region).")

# 3. OPTIMASI ALGORITMA (Hapus max_depth, perbesar n_estimators)
# Kita hapus class_weight='balanced' karena pada Random Forest sering kali mengorbankan terlalu banyak precision
model_classifier = RandomForestClassifier(
    n_estimators=300,        # Pohon diperbanyak agar tebakan lebih presisi
    min_samples_split=4,     # Mencegah model terlalu menghafal (overfitting) pada data spesifik
    random_state=42
)
model_classifier.fit(X_train, y_train)

# 4. EVALUASI MODEL
y_pred_test = model_classifier.predict(X_test)
akurasi = accuracy_score(y_test, y_pred_test)

cetak_log(f"SUKSES: Evaluasi Model pada data uji menghasilkan akurasi sebesar {akurasi * 100:.2f}%")

print("\nLaporan Detail Klasifikasi (Perhatikan baris '1' untuk Resesi):")
print(classification_report(y_test, y_pred_test))
# =========================================================
# Setelah teruji akurat, model siap digunakan untuk prediksi batch (Scoring)
# ... (Lanjut ke kode df_clean['Prediksi_Resesi'] = model_classifier.predict(X) seperti sebelumnya) ...
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