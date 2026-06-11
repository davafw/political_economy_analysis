import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# =========================================================================
# 1. KONFIGURASI KREDENSIAL & DATABASE AIVEN POSTGRESQL
# =========================================================================
def cetak_log(pesan):
    """Fungsi pembantu untuk mencetak log sistem dengan timestamp murni terminal"""
    waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{waktu}] [ML-ENGINE] {pesan}")

# Memuat variabel lingkungan dari file .env di folder yang sama
load_dotenv()

user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME', 'defaultdb')

# Validasi awal konfigurasi .env
if not all([user, password, host, port]):
    cetak_log("EROR: Kredensial di file .env belum lengkap atau tidak ditemukan!")
    exit(1)

cetak_log("Memulai pipeline otomatisasi Machine Learning Cloud (Headless Mode)...")

# Membuat Engine Koneksi ke Aiven PostgreSQL
db_uri = f"postgresql://{user}:{password}@{host}:{port}/{db_name}?sslmode=require"
engine = create_engine(db_uri)

# =========================================================================
# 2. PENGAMBILAN DATA DARI CLOUD SQL (EXTRACT FOR ML)
# =========================================================================
try:
    cetak_log("Menghubungkan ke Aiven PostgreSQL Cloud...")
    cetak_log("Membaca data fitur dari tabel 'tabel_features_ml'...")
    
    # Menggunakan objek text() dari SQLAlchemy agar aman dan kompatibel dengan PostgreSQL
    query_source = text("SELECT * FROM tabel_features_ml")
    df_master = pd.read_sql_query(query_source, engine)
    
except Exception as e:
    cetak_log(f"EROR: Gagal mengambil data dari Aiven Cloud: {e}")
    exit(1)

# =========================================================================
# 3. PRE-PROCESSING & PELATIHAN MODEL (TRAINING ON THE FLY)
# =========================================================================
# 1. KEMBALI KE FITUR INTI (Buang kolom region yang menjadi noise)
fitur_inti = ['Democracy Index', 'Inflation_Value', 'GDP_Growth_Lag1', 'Inflation_Lag1', 'Democracy_Index_Lag1']

df_master['Is_Recession'] = (df_master['GDP_Growth_Value'] < 0).astype(int)
df_clean = df_master.dropna(subset=fitur_inti).copy()

X = df_clean[fitur_inti]
y = df_clean['Is_Recession']

# 2. ATURAN 80/20
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

cetak_log(f"Total Data Bersih dari Cloud: {len(X)} baris.")
cetak_log(f"-> Menggunakan {len(fitur_inti)} variabel metrik ekonomi murni (Tanpa Region).")

# 3. OPTIMASI ALGORITMA
model_classifier = RandomForestClassifier(
    n_estimators=300,        # Pohon diperbanyak agar tebakan lebih presisi
    min_samples_split=4,     # Mencegah model terlalu menghafal (overfitting)
    random_state=42
)
model_classifier.fit(X_train, y_train)

# 4. EVALUASI MODEL
y_pred_test = model_classifier.predict(X_test)
akurasi = accuracy_score(y_test, y_pred_test)

cetak_log(f"SUKSES: Evaluasi Model pada data uji menghasilkan akurasi sebesar {akurasi * 100:.2f}%")

print("\nLaporan Detail Klasifikasi (Perhatikan baris '1' untuk Resesi):")
print(classification_report(y_test, y_pred_test))

# =========================================================================
# 4. PROSES PREDIKSI BATCH (SCORING ALL DATA)
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
# 5. MENULIS KEMBALI HASIL KE CLOUD DATABASE (LOAD TO TARGET TABLE)
# =========================================================================
try:
    cetak_log("Memindahkan hasil prediksi batch ke tabel target 'tabel_output_prediksi' di Aiven Cloud...")
    
    # Menulis langsung ke PostgreSQL menggunakan SQLAlchemy Engine
    # Jika tabel sudah ada, akan ditimpa (replace) dengan struktur dan data terbaru
    df_output_final.to_sql('tabel_output_prediksi', engine, if_exists='replace', index=False)
    
    cetak_log("SUKSES: Seluruh hasil prediksi telah disimpan kembali ke database Cloud Aiven.")
    cetak_log("Pipeline ML selesai dijalankan secara headless.")
    print("="*60)

except Exception as e:
    cetak_log(f"EROR: Gagal menulis hasil prediksi ke Aiven Cloud: {e}")
    exit(1)