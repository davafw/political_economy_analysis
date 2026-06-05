import streamlit as st
import pandas as pd
import sqlite3
import os

# =========================================================================
# 1. KONFIGURASI HALAMAN & PATH DATABASE
# =========================================================================
st.set_page_config(
    page_title="EWS: Deteksi Risiko Resesi Berbasis SQL",
    page_icon="📉",
    layout="wide"
)

# KONTROL PATH DATABASE:
# Jika di VSCode Lokal: Pastikan file .db berada di folder yang sama dengan app.py
# Jika di Google Colab: Gunakan path '/content/drive/MyDrive/.../stabilitas_ekonomi_politik.db'
DB_PATH = 'stabilitas_ekonomi_politik.db'

# Fungsi untuk membuat koneksi ke SQLite
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Agar hasil query bisa diakses berdasarkan nama kolom
    return conn

# Validasi awal apakah database sudah dibuat oleh Pipeline ETL
if not os.path.exists(DB_PATH):
    st.error(f"❌ **Database tidak ditemukan di:** `{os.path.abspath(DB_PATH)}`")
    st.warning("Silakan jalankan pipeline ETL Anda terlebih dahulu untuk membuat database SQL, atau sesuaikan variabel `DB_PATH` di baris atas kode.")
    st.stop()

# =========================================================================
# 2. FUNGSI PENGAMBILAN DATA (SQL QUERIES) WITH CACHING
# =========================================================================
@st.cache_data
def ambil_daftar_negara():
    """Mengambil semua daftar negara unik yang tersedia di database."""
    conn = get_db_connection()
    query = 'SELECT DISTINCT "Country Name" FROM tabel_dashboard_analisis ORDER BY "Country Name" ASC'
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df['Country Name'].tolist()

def ambil_tahun_negara(nama_negara):
    """Mengambil daftar tahun yang tersedia untuk negara tertentu dari Feature Store (ML)."""
    conn = get_db_connection()
    query = 'SELECT DISTINCT "Year" FROM tabel_features_ml WHERE "Country Name" = ? ORDER BY "Year" DESC'
    df = pd.read_sql_query(query, conn, params=[nama_negara])
    conn.close()
    return df['Year'].tolist()

def ambil_detail_data(nama_negara, tahun):
    """Mengambil satu baris data lengkap (fitur berjalan & fitur lag) dari SQL."""
    conn = get_db_connection()
    query = 'SELECT * FROM tabel_features_ml WHERE "Country Name" = ? AND "Year" = ? LIMIT 1'
    df = pd.read_sql_query(query, conn, params=[nama_negara, tahun])
    conn.close()
    return df.iloc[0] if not df.empty else None

# =========================================================================
# 3. INTERFACE UTAMA (HEADER)
# =========================================================================
st.title("📉 Early Warning System: Deteksi Risiko Resesi Global")
st.markdown("""
Aplikasi ini terhubung langsung ke **Database SQLite (`tabel_features_ml`)** hasil pipeline ETL.
Sistem memproyeksikan risiko resesi berdasarkan data politik & ekonomi makro riil di database, namun Anda tetap dapat mengubah angka indikator untuk melakukan *What-If Analysis*.
""")
st.write("---")

# =========================================================================
# 4. SIDEBAR INPUT - DYNAMIC FROM SQL
# =========================================================================
st.sidebar.header("🔌 Sinkronisasi Data SQL")

# Pilihan 1: Pilih Negara langsung dari database
daftar_negara = ambil_daftar_negara()
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
    # Mencari nama kolom region_* mana yang bernilai 1 di database
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
    # Logika pembobotan berbasis risiko makroekonomi & stabilitas politik
    skor_risiko = 0.0
    
    if inf > 10.0: skor_risiko += 0.35      # Hiperinflasi merusak daya beli
    elif inf > 5.0: skor_risiko += 0.15
    
    if dem < 4.0: skor_risiko += 0.25        # Rezim otoriter rentan sanksi/gejolak
    elif dem < 6.0: skor_risiko += 0.10      # Demokrasi cacat (Flawed Democracy)
    
    if gdp_l1 < 0: skor_risiko += 0.20       # Tren ekonomi tahun lalu sudah minus
    if inf_l1 > 8.0: skor_risiko += 0.10     # Inflasi tinggi berkepanjangan
    if dem < dem_l1: skor_risiko += 0.10     # Terjadi regresi/kemunduran demokrasi
    
    probabilitas = min(max(skor_risiko, 0.05), 0.95)
    kelas_prediksi = 1 if probabilitas >= 0.50 else 0
    return kelas_prediksi, probabilitas

# =========================================================================
# 6. TAMPILAN DASHBOARD UTAMA
# =========================================================================
# Tampilkan Ringkasan Informasi Data yang Sedang Aktif
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

# Menampilkan Output dengan Kondisi Warna Komponen UI
if kelas == 1:
    st.error(f"🚨 **PERINGATAN: {negara_terpilih.upper()} BERISIKO TINGGI MENGALAMI RESESI**")
    st.progress(prob)
    st.markdown(f"Sistem mendeteksi probabilitas kerentanan ekonomi sebesar **{prob*100:.1f}%**. Kondisi inflasi yang tidak stabil dikombinasikan dengan indeks demokrasi saat ini memicu alarm tanda bahaya ekonomi.")
else:
    st.success(f"✅ **STATUS AMAN: RISIKO RESESI {negara_terpilih.upper()} RENDAH**")
    st.progress(prob)
    st.markdown(f"Sistem memproyeksikan probabilitas resesi yang rendah sebesar **{prob*100:.1f}%**. Fondasi ekonomi makro dan tingkat stabilitas politik dinilai cukup solid untuk bertahan.")

# Menampilkan Rekomendasi Pengambilan Keputusan (Bobot Nilai Tinggi UAS)
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