import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# 1. Load kredensial dari file .env
load_dotenv()

user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME', 'defaultdb')

# 2. Ambil data dari SQLite Lokal
DB_PATH = 'stabilitas_ekonomi_politik.db'
if not os.path.exists(DB_PATH):
    print(f"❌ Error: File lokal {DB_PATH} tidak ditemukan!")
    exit(1)

print("📦 Membaca data dari SQLite lokal...")
conn_local = sqlite3.connect(DB_PATH)

# Tarik kedua tabel yang dibutuhkan ke DataFrame Pandas
df_features = pd.read_sql_query('SELECT * FROM tabel_features_ml', conn_local)
df_dashboard = pd.read_sql_query('SELECT * FROM tabel_dashboard_analisis', conn_local)
conn_local.close()

# 3. Koneksi ke Aiven PostgreSQL Cloud
db_uri = f"postgresql://{user}:{password}@{host}:{port}/{db_name}?sslmode=require"
engine_cloud = create_engine(db_uri)

# 4. Upload data ke Aiven Cloud
try:
    print("🚀 Menghubungkan ke Aiven Cloud dan mengupload data...")
    
    # Upload tabel_features_ml
    df_features.to_sql('tabel_features_ml', engine_cloud, if_exists='replace', index=False)
    print("✅ Tabel 'tabel_features_ml' berhasil di-upload!")
    
    # Upload tabel_dashboard_analisis
    df_dashboard.to_sql('tabel_dashboard_analisis', engine_cloud, if_exists='replace', index=False)
    print("✅ Tabel 'tabel_dashboard_analisis' berhasil di-upload!")
    
    print("\n🎉 MIGRASI SELESAI! Semua data telah berada di Cloud Aiven PostgreSQL.")

except Exception as e:
    print(f"❌ Gagal mengupload data: {e}")