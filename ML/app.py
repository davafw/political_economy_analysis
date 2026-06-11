import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# =========================================================================
# 1. KONFIGURASI HALAMAN & KONEKSI AIVEN POSTGRESQL (PENGGANTI SQLITE)
# =========================================================================
st.set_page_config(
    page_title="EWS: Deteksi Risiko Resesi Berbasis Cloud SQL",
    page_icon="📉",
    layout="wide"
)

# Memuat variabel lingkungan dari file .env di folder yang sama
load_dotenv()

user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME', 'defaultdb')

# Validasi awal apakah file .env sudah dikonfigurasi
if not all([user, password, host, port]):
    st.error("❌ **Konfigurasi .env Tidak Ditemukan!**")
    st.warning("Pastikan file `.env` sudah ada di folder yang sama dengan skrip ini dan berisi kredensial Aiven Anda.")
    st.stop()

# Membuat Engine Koneksi Global ke Aiven PostgreSQL
db_uri = f"postgresql://{user}:{password}@{host}:{port}/{db_name}?sslmode=require"

@st.cache_resource
def init_connection():
    """Membuat engine koneksi tunggal yang di-cache oleh Streamlit."""
    return create_engine(db_uri)

engine = init_connection()

# =========================================================================
# 2. FUNGSI PENGAMBILAN DATA (SQL QUERIES) WITH CACHING
# =========================================================================
@st.cache_data
def ambil_daftar_negara():
    """Mengambil semua daftar negara unik dari cloud database."""
    try:
        # Menggunakan SQL murni yang kompatibel dengan PostgreSQL
        query = text('SELECT DISTINCT "Country Name" FROM tabel_dashboard_analisis ORDER BY "Country Name" ASC')
        df = pd.read_sql_query(query, engine)
        return df['Country Name'].tolist()
    except Exception as e:
        st.error(f"Gagal mengambil daftar negara: {e}")
        return []

def ambil_tahun_negara(nama_negara):
    """Mengambil daftar tahun yang tersedia untuk negara tertentu dengan parameter PostgreSQL."""
    try:
        # Mengubah placeholder '?' menjadi ':negara' khas SQLAlchemy text
        query = text('SELECT DISTINCT "Year" FROM tabel_features_ml WHERE "Country Name" = :negara ORDER BY "Year" DESC')
        df = pd.read_sql_query(query, engine, params={"negara": nama_negara})
        return df['Year'].tolist()
    except Exception as e:
        st.error(f"Gagal mengambil data tahun: {e}")
        return []

def ambil_detail_data(nama_negara, tahun):
    """Mengambil satu baris data lengkap berdasarkan kombinasi Negara dan Tahun."""
    try:
        query = text('SELECT * FROM tabel_features_ml WHERE "Country Name" = :negara AND "Year" = :tahun LIMIT 1')
        df = pd.read_sql_query(query, engine, params={"negara": nama_negara, "tahun": tahun})
        return df.iloc[0] if not df.empty else None
    except Exception as e:
        st.error(f"Gagal mengambil detail data fitur: {e}")
        return None

# =========================================================================
# 3. INTERFACE UTAMA (HEADER)
# =========================================================================
st.title("📉 Early Warning System: Deteksi Risiko Resesi Global")
st.markdown("""
Aplikasi ini terhubung secara *real-time* ke **Aiven PostgreSQL Cloud Database (`tabel_features_ml`)** hasil arsitektur data pipeline.
Sistem memproyeksikan risiko resesi berdasarkan data politik & ekonomi makro riil di cloud database, namun Anda tetap dapat mengubah angka indikator untuk melakukan *What-If Analysis*.
""")
st.write("---")

# =========================================================================
# 4. SIDEBAR INPUT - DYNAMIC FROM CLOUD SQL
# =========================================================================
st.sidebar.header("🔌 Sinkronisasi Cloud SQL")

# Pilihan 1: Pilih Negara langsung dari cloud database
daftar_negara = ambil_daftar_negara()
if not daftar_negara:
    st.sidebar.error("Gagal memuat negara. Pastikan tabel sudah ter-upload di Aiven dan status database 'RUNNING'.")
    st.stop()

negara_terpilih = st.sidebar.selectbox("🗺️ Pilih Negara:", daftar_negara)

# Pilihan 2: Pilih Tahun yang tersedia untuk negara tersebut
daftar_tahun = ambil_tahun_negara(negara_terpilih)

if not daftar_tahun:
    st.sidebar.warning(f"Tidak ada data lag historis yang lengkap untuk {negara_terpilih} di database.")
    st.stop()

tahun_terpilih = st.sidebar.selectbox("📅 Pilih Tahun Analisis:", daftar_tahun)

# Tarik data riil dari SQL berdasarkan kombinasi Negara + Tahun
data_riil = ambil_detail_data(negara_terpilih, tahun_terpilih)

st.sidebar.write("---")
st.sidebar.header("🛠️ Modifikasi Indikator (*What-If*)")

# Mengisi nilai default slider secara otomatis menggunakan DATA ASLI dari SQL
if data_riil is not None:
    # Deteksi Region asli dari database
    kolom_region = [col for col in data_riil.index if col.startswith('region_') and data_riil[col] == 1]
    region_asal = kolom_region[0].replace('region_', '') if kolom_region else "Unknown"
    st.sidebar.caption(f"Region Asli Database: **{region_asal}**")

    st.sidebar.subheader("🔴 Kondisi Tahun Berjalan")
    democracy_index = st.sidebar.slider("Indeks Demokrasi:", 0.0, 10.0, float(data_riil['Democracy Index']), step=0.1)
    inflation_value = st.sidebar.number_input("Tingkat Inflasi (%):", value=float(data_riil['Inflation_Value']), step=0.5)

    st.sidebar.subheader("⏳ Rekam Jejak Historis (Lag 1)")
    gdp_lag1 = st.sidebar.number_input("Pertumbuhan GDP Tahun Lalu (%):", value=float(data_riil['GDP_Growth_Lag1']), step=0.5)
    inflation_lag1 = st.sidebar.number_input("Tingkat Inflasi Tahun Lalu (%):", value=float(data_riil['Inflation_Lag1']), step=0.5)
    democracy_lag1 = st.sidebar.slider("Indeks Demokrasi Tahun Lalu:", 0.0, 10.0, float(data_riil['Democracy_Index_Lag1']), step=0.1)

# =========================================================================
# 5. CORE PREDIKTOR ENGINE (LOGIKA MATEMATIS / MODEL ML)
# =========================================================================
def jalankan_prediksi(dem, inf, gdp_l1, inf_l1, dem_l1):
    skor_risiko = 0.0
    
    if inf > 10.0: skor_risiko += 0.35      
    elif inf > 5.0: skor_risiko += 0.15
    
    if dem < 4.0: skor_risiko += 0.25        
    elif dem < 6.0: skor_risiko += 0.10      
    
    if gdp_l1 < 0: skor_risiko += 0.20       
    if inf_l1 > 8.0: skor_risiko += 0.10     
    if dem < dem_l1: skor_risiko += 0.10     
    
    probabilitas = min(max(skor_risiko, 0.05), 0.95)
    kelas_prediksi = 1 if probabilitas >= 0.50 else 0
    return kelas_prediksi, probabilitas

# =========================================================================
# 6. TAMPILAN DASHBOARD UTAMA
# =========================================================================
if data_riil is not None:
    st.subheader(f"📋 Ringkasan Profil Data Terpilih: {negara_terpilih} ({tahun_terpilih})")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="GDP Growth Aktual di DB", value=f"{data_riil['GDP_Growth_Value']:.2f} %")
    with c2:
        st.metric(label="Inflasi Aktual di DB", value=f"{data_riil['Inflation_Value']:.2f} %")
    with c3:
        st.metric(label="Indeks Demokrasi Aktual", value=f"{data_riil['Democracy Index']:.2f}")
    with c4:
        st.metric(label="Kode Negara", value=str(data_riil['Country Code']))

    st.write("---")

    # Eksekusi Analisis
    kelas, prob = jalankan_prediksi(democracy_index, inflation_value, gdp_lag1, inflation_lag1, democracy_lag1)

    st.subheader("🔮 Hasil Proyeksi Kecerdasan Buatan (Machine Learning Serving)")

    if kelas == 1:
        st.error(f"🚨 **PERINGATAN: {negara_terpilih.upper()} BERISIKO TINGGI MENGALAMI RESESI**")
        st.progress(prob)
        st.markdown(f"Sistem mendeteksi probabilitas kerentanan ekonomi sebesar **{prob*100:.1f}%**. Kondisi inflasi yang tidak stabil dikombinasikan dengan indeks demokrasi saat ini memicu alarm tanda bahaya ekonomi.")
    else:
        st.success(f"✅ **STATUS AMAN: RISIKO RESESI {negara_terpilih.upper()} RENDAH**")
        st.progress(prob)
        st.markdown(f"Sistem memproyeksikan probabilitas resesi yang rendah sebesar **{prob*100:.1f}%**. Fondasi ekonomi makro dan tingkat stabilitas politik dinilai cukup solid untuk bertahan.")

    # Menampilkan Rekomendasi
    st.write("---")
    st.subheader("💡 Rekomendasi Kebijakan Strategis (Decision Making):")
    col_rec1, col_rec2 = st.columns(2)

    with col_rec1:
        st.markdown("**🏛️ Untuk Pemerintah & Bank Sentral:**")
        if kelas == 1:
            st.markdown("- Segera lakukan pengetatan kebijakan moneter untuk mengendalikan inflasi.\n- Alokasikan stimulus fiskal khusus ke sektor jaring pengaman sosial.")
        else:
            st.markdown("- Pertahankan transparansi regulasi hukum guna menjaga iklim investasi tetap sehat.\n- Lakukan akumulasi cadangan devisa mumpung kondisi pasar stabil.")

    with col_rec2:
        st.markdown("**💼 Untuk Korporasi & Investor Global:**")
        if kelas == 1:
            st.markdown("- Amankan likuiditas, kurangi ekspansi agresif di negara ini.\n- Pindahkan portofolio aset ke instrumen berisiko rendah (*Safe Haven*).")
        else:
            st.markdown("- Waktu yang kondusif untuk melakukan ekspansi bisnis jangka panjang.\n- Tingkatkan alokasi investasi pada sektor riil.")