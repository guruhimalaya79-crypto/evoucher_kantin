import streamlit as st
import pandas as pd

from auth import (
    init_session,
    login_user,
    show_user_sidebar,
)
from database import (
    setup_database,
    get_database_summary,
    get_setting_int,
    DB_PATH,
)
from utils import (
    format_rupiah,
    get_current_period_month,
)


st.set_page_config(
    page_title="Sistem E-Voucher Kantin",
    page_icon="🍽️",
    layout="wide",
)


setup_database()
init_session()


def show_login_page():
    st.title("🍽️ Sistem E-Voucher Kantin")

    st.subheader("Login Aplikasi")

    st.write(
        """
        Aplikasi internal untuk mengelola e-voucher kantin kantor
        dengan fitur mini POS sederhana.
        """
    )

    monthly_amount = get_setting_int("monthly_voucher_amount", 75000)
    
    col_info1, col_info2, col_info3 = st.columns(3)

    with col_info1:
        st.metric("Voucher Bulanan", format_rupiah(monthly_amount))

    with col_info2:
        st.metric("Periode Saat Ini", get_current_period_month())

    with col_info3:
        st.metric("Mode Transaksi", "Mini POS")

    st.divider()

    with st.form("form_login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        submitted = st.form_submit_button("Login")

        if submitted:
            result = login_user(username, password)

            if result["success"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])

    st.divider()

    with st.expander("Akun Demo"):
        st.write(
            """
            **Admin**
            - Username: `admin`
            - Password: `admin123`

            **Kasir**
            - Username: `kasir`
            - Password: `kasir123`

            **Pegawai**
            - Username: `emp001`
            - Password: `emp001123`

            **Pegawai**
            - Username: `emp002`
            - Password: `emp002123`
            """
        )


def show_admin_home():
    st.subheader("Beranda Admin")

    st.write(
        """
        Admin bertugas mengelola data master, membuat voucher bulanan,
        memantau transaksi, melakukan void jika ada kesalahan, dan membuat laporan.
        """
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            """
            **1. Siapkan Master Data**

            - Master Divisi
            - Master Pegawai
            - Master Kategori Menu
            - Master Menu Makanan
            """
        )

    with col2:
        st.info(
            """
            **2. Operasional Voucher**

            - Generate voucher bulanan
            - Kasir input transaksi POS
            - Cek saldo pegawai
            - Void transaksi jika salah
            """
        )

    with col3:
        st.info(
            """
            **3. Laporan dan Kontrol**

            - Dashboard admin
            - Laporan pembayaran pedagang
            - Export Excel/CSV
            - Backup database
            """
        )

    st.divider()

    st.subheader("Urutan Kerja Admin yang Disarankan")

    st.markdown(
        """
        1. Cek dan lengkapi **Master Divisi**.
        2. Cek dan lengkapi **Master Pegawai**.
        3. Cek **Master Kategori Menu**.
        4. Cek **Master Menu Makanan**.
        5. Generate voucher bulanan.
        6. Pantau transaksi dari halaman laporan.
        7. Lakukan export laporan akhir bulan.
        8. Backup database secara rutin.
        """
    )


def show_kasir_home():
    st.subheader("Beranda Kasir")

    st.write(
        """
        Kasir bertugas mencatat transaksi penggunaan voucher pegawai
        melalui halaman Mini POS.
        """
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.success(
            """
            **Alur Kerja Kasir**

            1. Buka halaman **Kasir POS**.
            2. Pilih pegawai.
            3. Cek saldo voucher.
            4. Pilih item makanan/minuman.
            5. Pastikan total belanja benar.
            6. Klik **Simpan Transaksi**.
            """
        )

    with col2:
        st.warning(
            """
            **Catatan Penting**

            - Jangan simpan transaksi jika pegawai salah.
            - Jangan simpan transaksi jika item salah.
            - Jika terjadi salah input, hubungi admin untuk void.
            - Transaksi yang sudah void tidak dihitung dalam laporan pembayaran.
            """
        )


def show_pegawai_home():
    st.subheader("Beranda Pegawai")

    st.write(
        """
        Pegawai dapat melihat saldo voucher bulan berjalan dan riwayat pemakaian voucher.
        """
    )

    st.divider()

    st.info(
        """
        Buka halaman **Saldo Pegawai** untuk melihat:

        - Alokasi voucher bulan ini
        - Total voucher yang sudah dipakai
        - Sisa saldo voucher
        - Riwayat transaksi
        - Detail item makanan yang dibeli
        """
    )


def show_home_after_login():
    role = st.session_state.role

    st.title("🍽️ Sistem E-Voucher Kantin")

    st.success(f"Login berhasil sebagai `{role}`.")

    st.divider()

    monthly_amount = get_setting_int("monthly_voucher_amount", 75000)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Voucher Bulanan Default", format_rupiah(monthly_amount))

    with col2:
        st.metric("Periode Bulan Ini", get_current_period_month())

    with col3:
        st.metric("Database", "SQLite Lokal")

    st.divider()

    if role == "admin":
        show_admin_home()

    elif role == "kasir":
        show_kasir_home()

    elif role == "pegawai":
        show_pegawai_home()

    st.divider()

    with st.expander("Ringkasan Tabel Database"):
        summary = get_database_summary()
        df_summary = pd.DataFrame(summary)
        st.dataframe(df_summary, use_container_width=True)

    st.caption(f"Lokasi database: `{DB_PATH}`")


show_user_sidebar()

if not st.session_state.is_logged_in:
    show_login_page()
else:
    show_home_after_login()