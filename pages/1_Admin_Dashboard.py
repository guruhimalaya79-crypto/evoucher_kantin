import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    get_admin_dashboard_summary,
    get_database_summary,
)
from utils import format_rupiah, get_current_period_month


st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="📊",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("📊 Admin Dashboard")

st.write("Ringkasan awal sistem e-voucher kantin dan mini POS.")

summary = get_admin_dashboard_summary()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Divisi Aktif", summary["active_divisions"])

with col2:
    st.metric("Pegawai Aktif", summary["active_employees"])

with col3:
    st.metric("Pegawai Nonaktif", summary["inactive_employees"])

col4, col5, col6 = st.columns(3)

with col4:
    st.metric("Kategori Menu Aktif", summary["active_categories"])

with col5:
    st.metric("Menu Makanan Aktif", summary["active_food_items"])

with col6:
    st.metric("User Aktif", summary["active_users"])

st.divider()

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.metric("Voucher Default", format_rupiah(75000))

with col_b:
    st.metric("Periode Bulan Ini", get_current_period_month())

with col_c:
    st.metric("Mode Kasir", "Mini POS")

st.divider()

st.subheader("Status Database")

df_summary = pd.DataFrame(get_database_summary())
st.dataframe(df_summary, use_container_width=True)

st.info(
    """
    Paket Final B berhasil jika dashboard ini bisa dibuka oleh admin,
    tetapi tidak bisa dibuka oleh kasir atau pegawai.
    """
)