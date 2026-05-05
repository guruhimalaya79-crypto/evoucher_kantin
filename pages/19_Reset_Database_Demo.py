import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    reset_demo_database,
    get_demo_database_counts,
)


st.set_page_config(
    page_title="Reset Database Demo",
    page_icon="♻️",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("♻️ Reset Database Demo")

st.error(
    """
    Halaman ini hanya untuk DEMO ONLINE / TESTING.

    Jika tombol reset dijalankan, semua data uji coba akan dihapus dan database
    akan dikembalikan ke data demo awal.
    """
)

st.warning(
    """
    Jangan gunakan fitur ini untuk aplikasi operasional resmi.
    Untuk operasional resmi, database tidak boleh direset sembarangan.
    """
)

st.divider()

st.subheader("Isi Database Saat Ini")

counts = get_demo_database_counts()
df_counts = pd.DataFrame(counts)

st.dataframe(df_counts, use_container_width=True)

st.divider()

st.subheader("Apa yang Akan Direset?")

st.markdown(
    """
    Data berikut akan dihapus:

    - Transaksi POS
    - Detail item transaksi
    - Alokasi voucher bulanan
    - User tambahan
    - Pegawai tambahan/import
    - Divisi tambahan
    - Kategori menu tambahan
    - Menu makanan tambahan
    - Setting yang sudah diubah
    - Audit log

    Setelah itu sistem akan membuat ulang data demo awal:

    - User demo: `admin`, `kasir`, `emp001`, `emp002`
    - Divisi demo
    - Pegawai demo
    - Merchant demo
    - Kategori menu demo
    - Menu makanan demo
    - Setting default
    """
)

st.divider()

st.subheader("Konfirmasi Reset")

st.write(
    """
    Untuk menghindari salah klik, ketik teks berikut secara persis:
    """
)

st.code("RESET DEMO")

confirm_text = st.text_input(
    "Ketik RESET DEMO"
)

confirm_checkbox = st.checkbox(
    "Saya paham bahwa semua data uji coba akan dihapus."
)

final_checkbox = st.checkbox(
    "Saya yakin ingin mengembalikan database ke data demo awal."
)

if st.button("Reset Database Demo Sekarang", type="primary"):
    if confirm_text.strip() != "RESET DEMO":
        st.error("Teks konfirmasi salah. Ketik RESET DEMO secara persis.")
    elif not confirm_checkbox:
        st.error("Centang pemahaman reset terlebih dahulu.")
    elif not final_checkbox:
        st.error("Centang konfirmasi akhir terlebih dahulu.")
    else:
        result = reset_demo_database(
            reset_by=st.session_state.user_id
        )

        if result["success"]:
            st.success(result["message"])
            st.info(
                """
                Silakan logout lalu login ulang menggunakan akun demo:

                Admin:
                username `admin`
                password `admin123`

                Kasir:
                username `kasir`
                password `kasir123`

                Pegawai:
                username `emp001`
                password `emp001123`
                """
            )
            st.rerun()
        else:
            st.error(result["message"])

st.divider()

st.subheader("Catatan untuk Streamlit Cloud")

st.info(
    """
    Fitur ini dibuat karena pada demo online, banyak orang bisa mencoba input data.
    Jika data demo sudah terlalu berantakan, admin cukup membuka halaman ini dan
    melakukan reset.

    Untuk penggunaan resmi kantor, fitur ini sebaiknya dihapus atau disembunyikan.
    """
)