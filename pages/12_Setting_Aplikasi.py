import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    get_setting_value,
    get_setting_bool,
    get_setting_int,
    get_all_settings,
    update_setting,
)
from utils import format_rupiah


st.set_page_config(
    page_title="Setting Aplikasi",
    page_icon="⚙️",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("⚙️ Setting Aplikasi")

st.write(
    """
    Halaman ini digunakan admin untuk mengatur konfigurasi dasar aplikasi.
    """
)

st.warning(
    """
    Hati-hati mengubah nominal voucher bulanan.
    Perubahan nominal hanya berlaku untuk generate voucher berikutnya.
    Alokasi yang sudah dibuat tidak otomatis berubah.
    """
)

st.divider()

current_company_name = get_setting_value("company_name", "Kantor Demo")
current_monthly_amount = get_setting_int("monthly_voucher_amount", 75000)
current_allow_split = get_setting_bool("allow_split_payment", False)
current_allow_free = get_setting_bool("allow_free_amount", True)

st.subheader("Setting Umum")

with st.form("form_setting_umum"):
    company_name = st.text_input(
        "Nama Kantor / Instansi",
        value=current_company_name
    )

    monthly_voucher_amount = st.number_input(
        "Nominal Voucher Bulanan per Pegawai",
        min_value=0,
        step=5000,
        value=int(current_monthly_amount)
    )

    allow_free_amount = st.selectbox(
        "Nominal Transaksi Bebas",
        options=["Ya", "Tidak"],
        index=0 if current_allow_free else 1,
        help="Untuk sistem final ini disarankan Ya, karena transaksi berasal dari total item makanan."
    )

    allow_split_payment = st.selectbox(
        "Izinkan Split Payment Voucher + Tunai",
        options=["Tidak", "Ya"],
        index=1 if current_allow_split else 0,
        help="Untuk versi awal disarankan Tidak. Jika Ya, belanja melebihi saldo dapat dibagi voucher dan tunai."
    )

    submitted = st.form_submit_button("Simpan Setting")

    if submitted:
        company_name_clean = company_name.strip()

        if company_name_clean == "":
            st.error("Nama kantor tidak boleh kosong.")
        elif monthly_voucher_amount <= 0:
            st.error("Nominal voucher bulanan harus lebih dari 0.")
        else:
            update_setting(
                key="company_name",
                value=company_name_clean,
                updated_by=st.session_state.user_id,
            )

            update_setting(
                key="monthly_voucher_amount",
                value=int(monthly_voucher_amount),
                updated_by=st.session_state.user_id,
            )

            update_setting(
                key="allow_free_amount",
                value="true" if allow_free_amount == "Ya" else "false",
                updated_by=st.session_state.user_id,
            )

            update_setting(
                key="allow_split_payment",
                value="true" if allow_split_payment == "Ya" else "false",
                updated_by=st.session_state.user_id,
            )

            st.success("Setting aplikasi berhasil disimpan.")
            st.rerun()

st.divider()

st.subheader("Ringkasan Setting Aktif")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Nama Kantor", get_setting_value("company_name", "-"))

with col2:
    st.metric(
        "Voucher Bulanan",
        format_rupiah(get_setting_int("monthly_voucher_amount", 75000))
    )

with col3:
    free_text = "Ya" if get_setting_bool("allow_free_amount", True) else "Tidak"
    st.metric("Nominal Bebas", free_text)

with col4:
    split_text = "Ya" if get_setting_bool("allow_split_payment", False) else "Tidak"
    st.metric("Split Payment", split_text)

st.divider()

st.subheader("Semua Setting")

settings = get_all_settings()
df = pd.DataFrame(settings)

if df.empty:
    st.info("Belum ada setting.")
else:
    df_display = df.rename(
        columns={
            "key": "Key",
            "value": "Value",
            "updated_at": "Diupdate Pada",
        }
    )

    st.dataframe(df_display, use_container_width=True)