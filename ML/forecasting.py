import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor
import numpy as np

# =========================================================================
# 1. KONFIGURASI HALAMAN & KONEKSI AIVEN POSTGRESQL (PENGGANTI SQLITE)
# =========================================================================
st.set_page_config(
    page_title="Forecasting Sistem: Proyeksi Ekonomi Global",
    page_icon="📈",
    layout="wide"
)

# Memuat variabel lingkungan dari file .env di folder yang sama
load_dotenv()

user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME', 'defaultdb')

# Validasi awal konfigurasi .env
if not all([user, password, host, port]):
    st.error("❌ **Konfigurasi .env Tidak Ditemukan!**")
    st.warning("Pastikan file `.env` sudah dikonfigurasi dengan benar di folder proyek Anda.")
    st.stop()

# Membuat Engine Koneksi Global ke Aiven PostgreSQL
db_uri = f"postgresql://{user}:{password}@{host}:{port}/{db_name}?sslmode=require"

@st.cache_resource
def init_connection():
    """Membuat engine koneksi tunggal yang di-cache oleh Streamlit."""
    return create_engine(db_uri)

engine = init_connection()

# =========================================================================
# 2. MACHINE LEARNING ENGINE: TRAINING MODEL REGRESI
# =========================================================================
@st.cache_resource
def latih_model_forecasting():
    """Membaca data dari Cloud PostgreSQL dan melatih model untuk meramal nilai GDP murni"""
    try:
        # Menggunakan SQL murni SQLAlchemy text untuk menarik Feature Store ML
        query = text("SELECT * FROM tabel_features_ml")
        df = pd.read_sql_query(query, engine)
        
        # Drop data yang memiliki nilai kosong pada fitur utama
        fitur_cols = ['Democracy Index', 'Inflation_Value', 'GDP_Growth_Lag1', 'Inflation_Lag1', 'Democracy_Index_Lag1']
        df_clean = df.dropna(subset=fitur_cols + ['GDP_Growth_Value'])
        
        X = df_clean[fitur_cols]
        y = df_clean['GDP_Growth_Value']
        
        # Menggunakan Random Forest Regressor untuk prediksi angka kontinu (persentase)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        return model, fitur_cols
    except Exception as e:
        st.error(f"❌ Gagal melatih model ML dari database: {e}")
        st.stop()

# Latih model di background saat aplikasi dibuka
model_regresi, nama_fitur = latih_model_forecasting()

# =========================================================================
# 3. FUNGSI RECURSIVE FORECASTING (PROYEKSI MASA DEPAN)
# =========================================================================
def ramal_masa_depan(nama_negara, jumlah_tahun_ke_depan=5):
    try:
        # Mengubah placeholder ke gaya PostgreSQL (:negara)
        query = text('SELECT * FROM tabel_features_ml WHERE "Country Name" = :negara ORDER BY "Year" ASC')
        df_negara = pd.read_sql_query(query, engine, params={"negara": nama_negara})
        
        if df_negara.empty:
            return None, None
        
        # Ambil data tahun terakhir yang tersedia di database sebagai titik awal (baseline)
        data_terakhir = df_negara.iloc[-1]
        tahun_terakhir = int(data_terakhir['Year'])
        
        # Ambil riwayat pertumbuhan GDP asli untuk grafik
        riwayat_tahun = df_negara['Year'].tolist()
        riwayat_gdp = df_negara['GDP_Growth_Value'].tolist()
        
        # Siapkan variabel penampung untuk proses rekursif peramalan
        gdp_sekarang = data_terakhir['GDP_Growth_Value']
        inflasi_sekarang = data_terakhir['Inflation_Value']
        demokrasi_sekarang = data_terakhir['Democracy Index']
        
        gdp_lag1 = data_terakhir['GDP_Growth_Lag1']
        inflasi_lag1 = data_terakhir['Inflation_Lag1']
        demokrasi_lag1 = data_terakhir['Democracy_Index_Lag1']
        
        list_tahun_prediksi = []
        list_gdp_prediksi = []
        
        tahun_berjalan = tahun_terakhir
        
        # Loop Rekursif: Hasil prediksi tahun T akan menjadi nilai LAG untuk tahun T+1
        for i in range(1, jumlah_tahun_ke_depan + 1):
            tahun_berjalan += 1
            
            # Geser nilai lag (Kondisi sekarang berubah menjadi kondisi masa lalu/lag untuk tahun depan)
            gdp_lag1_baru = gdp_sekarang
            inflasi_lag1_baru = inflasi_sekarang
            demokrasi_lag1_baru = demokrasi_sekarang
            
            # Susun DataFrame kecil agar model tidak memunculkan UserWarning mengenai nama kolom
            fitur_input = pd.DataFrame([[
                demokrasi_sekarang, inflasi_sekarang, gdp_lag1_baru, inflasi_lag1_baru, demokrasi_lag1_baru
            ]], columns=nama_fitur)
            
            # Prediksi nilai GDP tahun depan menggunakan model ML
            gdp_prediksi = model_regresi.predict(fitur_input)[0]
            
            # Simpan hasil ramalan
            list_tahun_prediksi.append(tahun_berjalan)
            list_gdp_prediksi.append(gdp_prediksi)
            
            # Update nilai variabel sekarang dengan hasil prediksi tadi agar bisa dipakai di iterasi berikutnya
            gdp_sekarang = gdp_prediksi
            gdp_lag1 = gdp_lag1_baru
            
        return (riwayat_tahun, riwayat_gdp), (list_tahun_prediksi, list_gdp_prediksi)
    except Exception as e:
        st.error(f"Gagal memproses peramalan rekursif: {e}")
        return None, None

# =========================================================================
# 4. INTERFACE STREAMLIT (FRONTEND)
# =========================================================================
st.title("📈 Proyeksi & Peramalan Multi-Tahun Pertumbuhan Ekonomi")
st.markdown("""
Aplikasi ini menggunakan teknik **Recursive Autoregressive Forecasting** dengan algoritma *Random Forest Regressor*.
Sistem akan membaca data historis dari tabel **Aiven PostgreSQL Cloud Database**, lalu memproyeksikan laju pertumbuhan ekonomi beberapa tahun ke depan.
""")
st.write("---")

# Mengambil daftar negara dari PostgreSQL cloud untuk dropdown
try:
    query_negara = text('SELECT DISTINCT "Country Name" FROM tabel_features_ml ORDER BY "Country Name" ASC')
    daftar_negara = pd.read_sql_query(query_negara, engine)['Country Name'].tolist()
except Exception as e:
    st.error(f"Gagal memuat daftar negara dari Cloud SQL: {e}")
    st.stop()

# Komponen Input di Area Utama
col_input1, col_input2 = st.columns(2)
with col_input1:
    negara_terpilih = st.selectbox("🗺️ Pilih Negara yang Ingin Diramal:", daftar_negara)
with col_input2:
    durasi_ramalan = st.slider("⏳ Jangka Waktu Peramalan (Tahun ke Depan):", 1, 7, 5)

if st.button("🚀 Jalankan Peramalan Masa Depan"):
    
    # Eksekusi fungsi peramalan
    riwayat, prediksi = ramal_masa_depan(negara_terpilih, durasi_ramalan)
    
    if riwayat is not None:
        tahun_historis, gdp_historis = riwayat
        tahun_depan, gdp_depan = prediksi
        
        # =========================================================================
        # 5. VISUALISASI HASIL PERAMALAN (LINE CHART TREN)
        # =========================================================================
        st.subheader(f"📊 Grafik Tren & Proyeksi Pertumbuhan GDP: {negara_terpilih}")
        
        # Gabungkan data historis dan data prediksi ke dalam satu DataFrame untuk grafik Streamlit
        df_grafik_hist = pd.DataFrame({'Tahun': tahun_historis, 'Kategori': 'Historis (Data SQL Cloud)', 'GDP Growth (%)': gdp_historis})
        df_grafik_pred = pd.DataFrame({'Tahun': [tahun_historis[-1]] + tahun_depan, 'Kategori': 'Proyeksi (Machine Learning)', 'GDP Growth (%)': [gdp_historis[-1]] + gdp_depan})
        
        df_total_grafik = pd.concat([df_grafik_hist, df_grafik_pred]).reset_index(drop=True)
        
        # Pivot agar formatnya dikenali oleh st.line_chart
        df_pivot = df_total_grafik.pivot(index='Tahun', columns='Kategori', values='GDP Growth (%)')
        
        # Tampilkan grafik garis interaktif
        st.line_chart(df_pivot)
        
        # =========================================================================
        # 6. TABEL DETAIL DATA HASIL RAMALAN
        # =========================================================================
        st.subheader("📋 Detail Angka Hasil Proyeksi")
        df_hasil_tabel = pd.DataFrame({
            'Tahun Masa Depan': tahun_depan,
            'Estimasi Pertumbuhan GDP (%)': [f"{val:.3f} %" for val in gdp_depan]
        })
        
        # Menampilkan indikator performa tren akhir
        tren_akhir = gdp_depan[-1] - gdp_historis[-1]
        if tren_akhir > 0:
            st.info(f"📈 **Analisis Tren:** Secara umum, model memproyeksikan ekonomi {negara_terpilih} akan mengalami **percepatan/tren positif** sebesar +{abs(tren_akhir):.2f}% dibandingkan tahun terakhir data riil.")
        else:
            st.warning(f"📉 **Analisis Tren:** Model memproyeksikan ekonomi {negara_terpilih} rentan mengalami **perlambatan/tren negatif** sebesar -{abs(tren_akhir):.2f}% dalam {durasi_ramalan} tahun ke depan.")
            
        st.dataframe(df_hasil_tabel, use_container_width=True)