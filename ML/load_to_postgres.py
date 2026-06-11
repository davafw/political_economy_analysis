import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# =========================================================================
# 1. LOAD ENVIRONMENT VARIABLES (PENGGANTI GOOGLE USERDATA)
# =========================================================================
# Fungsi ini akan otomatis membaca file .env yang ada di folder yang sama
load_dotenv()

def cetak_log(pesan):
    print(f"[INFO] [POSTGRES-LOAD] {pesan}")

# Mengambil kredensial dari file .env
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME', 'defaultdb')

# Validasi apakah kredensial berhasil terbaca
if not all([user, password, host, port]):
    print("❌ ERROR: Kredensial di file .env belum diisi atau tidak terbaca!")
    exit(1)

cetak_log("Kredensial database dari file .env berhasil dimuat.")

# =========================================================================
# 2. BUAT CONNECTION STRING & ENGINE
# =========================================================================
db_uri = f"postgresql://{user}:{password}@{host}:{port}/{db_name}?sslmode=require"
engine = create_engine(db_uri)

# =========================================================================
# 3. CONTOH DATA (SIMULASI DATA FRAME)
# =========================================================================
# Catatan: Jika kode ini ditempel di akhir skrip ETL Anda, 
# hapus/komentari baris simulasi di bawah ini karena Anda sudah punya 'df_master' asli.
if 'df_master' not in locals() and 'df_master' not in globals():
    cetak_log("Membuat data simulasi df_master untuk uji coba koneksi...")
    data_simulasi = {
        'Country Name': ['Indonesia', 'Malaysia'],
        'GDP_Growth_Value': [5.05, 4.2],
        'Inflation_Value': [2.8, 3.1]
    }
    df_master = pd.DataFrame(data_simulasi)

# =========================================================================
# 4. PROSES LOAD: KIRIM KE AIVEN POSTGRESQL
# =========================================================================
try:
    cetak_log("Menghubungkan ke Aiven PostgreSQL Cloud...")
    
    # Mengirim data ke tabel 'ekonomi_politik_global'
    df_master.to_sql('ekonomi_politik_global', engine, if_exists='replace', index=False)
    
    print("✅ SUKSES: Data berhasil dikirim dan disimpan ke Aiven PostgreSQL!")
    print("="*60)
except Exception as e:
    print(f"❌ Gagal mengirim data ke cloud database: {e}")