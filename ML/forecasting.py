import streamlit as st
import pandas as pd
import sqlite3
import os
from sklearn.ensemble import RandomForestRegressor
import numpy as np

# =========================================================================
# 1. KONFIGURASI HALAMAN
# =========================================================================
st.set_page_config(
    page_title="Forecasting Sistem: Proyeksi Ekonomi Global",
    page_icon="📈",
    layout="wide"
)

DB_PATH = 'stabilitas_ekonomi_politik.db'

def get_db_connection():
    return sqlite3.connect(DB_PATH)

if not os.path.exists(DB_PATH):
    st.error(f"❌ Database tidak ditemukan di {DB_PATH}")
    st.stop()

# =========================================================================
# 2. MACHINE LEARNING ENGINE: TRAINING MODEL REGRESI
# =========================================================================
@st.cache_resource
def latih_model_forecasting():
    """Membaca data dari SQL dan melatih model untuk meramal nilai GDP murni"""
    conn = get_db_connection()
    # Mengambil data dari Feature Store ML
    query = "SELECT * FROM tabel_features_ml"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Drop data yang memiliki nilai kosong pada fitur utama
    fitur_cols = ['Democracy Index', 'Inflation_Value', 'GDP_Growth_Lag1', 'Inflation_Lag1', 'Democracy_Index_Lag1']
    df_clean = df.dropna(subset=fitur_cols + ['GDP_Growth_Value'])
    
    X = df_clean[fitur_cols]
    y = df_clean['GDP_Growth_Value']
    
    # Menggunakan Random Forest Regressor untuk prediksi angka kontinu (persentase)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return model

# Latih model di background saat aplikasi dibuka
model_regresi = latih_model_forecasting()

# =========================================================================
# 3. FUNGSI RECURSIVE FORECASTING (PROYEKSI MASA DEPAN)
# =========================================================================
def ramal_masa_depan(nama_negara, jumlah_tahun_ke_depan=5):
    conn = get_db_connection()
    # Ambil data historis asli dari database untuk negara tersebut, urutkan dari tahun terlama ke terbaru
    query = 'SELECT * FROM tabel_features_ml WHERE "Country Name" = ? ORDER BY "Year" ASC'
    df_negara = pd.read_sql_query(query, conn, params=[nama_negara])
    conn.close()
    
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
        
        # Susun array fitur sesuai format training data
        # Catatan: Kita asumsikan tingkat inflasi dan indeks demokrasi stabil/konstan di tahun depan 
        # untuk mengisolasi peramalan pada tren pertumbuhan ekonomi.
        fitur_input = [[demokrasi_sekarang, inflasi_sekarang, gdp_lag1_baru, inflasi_lag1_baru, demokrasi_lag1_baru]]
        
        # Prediksi nilai GDP tahun depan menggunakan model ML
        gdp_prediksi = model_regresi.predict(fitur_input)[0]
        
        # Simpan hasil ramalan
        list_tahun_prediksi.append(tahun_berjalan)
        list_gdp_prediksi.append(gdp_prediksi)
        
        # Update nilai variabel sekarang dengan hasil prediksi tadi agar bisa dipakai di iterasi loop berikutnya
        gdp_sekarang = gdp_prediksi
        gdp_lag1 = gdp_lag1_baru
        
    return (riwayat_tahun, riwayat_gdp), (list_tahun_prediksi, list_gdp_prediksi)

# =========================================================================
# 4. INTERFACE STRALMIT (FRONTEND)
# =========================================================================
st.title("📈 Proyeksi & Peramalan Multi-Tahun Pertumbuhan Ekonomi")
st.markdown("""
Aplikasi ini menggunakan teknik **Recursive Autoregressive Forecasting** dengan algoritma *Random Forest Regressor*.
Sistem akan membaca data historis dari tabel database SQL, lalu memproyeksikan laju pertumbuhan ekonomi beberapa tahun ke depan.
""")
st.write("---")

# Mengambil daftar negara dari database untuk dropdown
conn = get_db_connection()
daftar_negara = pd.read_sql_query('SELECT DISTINCT "Country Name" FROM tabel_features_ml ORDER BY "Country Name" ASC', conn)['Country Name'].tolist()
conn.close()

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
        df_grafik_hist = pd.DataFrame({'Tahun': tahun_historis, 'Kategori': 'Historis (Data SQL)', 'GDP Growth (%)': gdp_historis})
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