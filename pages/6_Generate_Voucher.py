import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    get_setting_int,
    get_active_employee_count,
    get_monthly_allocation_summary,
    generate_monthly_voucher_official,
    get_monthly_allocations_with_employee,
)
from utils import (
    format_rupiah,
    get_current_period_month,
    is_valid_period_month,
)


st.set_page_config(
    page_title="Generate Voucher",
    page_icon="🎫",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("🎫 Generate Voucher Bulanan")

st.write(
    """
    Halaman ini digunakan admin untuk membuat alokasi e-voucher bulanan
    untuk seluruh pegawai aktif.
    """
)

st.warning(
    """
    Perhatian:
    Generate voucher hanya perlu dilakukan satu kali per periode bulan.
    Sistem akan otomatis melewati pegawai yang sudah memiliki alokasi pada periode tersebut.
    """
)

st.divider()

period_month = st.text_input(
    "Periode Voucher",
    value=get_current_period_month(),
    help="Format wajib YYYY-MM. Contoh: 2026-05"
)

period_month_clean = period_month.strip()

if not is_valid_period_month(period_month_clean):
    st.error("Format periode salah. Gunakan format YYYY-MM.")
    st.stop()

monthly_amount = get_setting_int("monthly_voucher_amount", 75000)
active_employee_count = get_active_employee_count()
allocation_summary = get_monthly_allocation_summary(period_month_clean)

st.subheader("Ringkasan Sebelum Generate")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Pegawai Aktif", active_employee_count)

with col2:
    st.metric("Voucher per Pegawai", format_rupiah(monthly_amount))

with col3:
    st.metric("Sudah Dialokasikan", allocation_summary["total_allocations"])

with col4:
    st.metric("Belum Dialokasikan", allocation_summary["not_allocated_count"])

col5, col6 = st.columns(2)

with col5:
    st.metric("Total Alokasi Saat Ini", format_rupiah(allocation_summary["total_amount"]))

with col6:
    estimated_total = active_employee_count * monthly_amount
    st.metric("Estimasi Jika Semua Aktif Dialokasikan", format_rupiah(estimated_total))

st.divider()

st.subheader("Proses Generate")

with st.form("form_generate_voucher"):
    st.write(f"Periode yang akan digenerate: **{period_month_clean}**")
    st.write(f"Nominal voucher per pegawai: **{format_rupiah(monthly_amount)}**")
    st.write(f"Jumlah pegawai aktif: **{active_employee_count}**")

    confirm = st.checkbox(
        "Saya yakin ingin generate voucher untuk periode ini."
    )

    submitted = st.form_submit_button("Generate Voucher Bulanan")

    if submitted:
        if not confirm:
            st.error("Centang konfirmasi terlebih dahulu.")
        elif monthly_amount <= 0:
            st.error("Nominal voucher bulanan tidak valid. Cek halaman Setting Aplikasi.")
        elif active_employee_count == 0:
            st.error("Tidak ada pegawai aktif.")
        else:
            result = generate_monthly_voucher_official(
                period_month=period_month_clean,
                generated_by=st.session_state.user_id,
            )

            if result["success"]:
                st.success(result["message"])

                col_r1, col_r2, col_r3, col_r4 = st.columns(4)

                with col_r1:
                    st.metric("Pegawai Aktif", result["active_employees"])

                with col_r2:
                    st.metric("Alokasi Baru", result["created"])

                with col_r3:
                    st.metric("Dilewati", result["skipped"])

                with col_r4:
                    st.metric("Nominal", format_rupiah(result["amount"]))

                st.rerun()
            else:
                st.error(result["message"])

st.divider()

st.subheader("Daftar Alokasi Voucher Periode Ini")

allocations = get_monthly_allocations_with_employee(period_month_clean)
df = pd.DataFrame(allocations)

if df.empty:
    st.info("Belum ada alokasi voucher pada periode ini.")
else:
    df["Nominal"] = df["amount_allocated"].apply(format_rupiah)

    df_display = df[
        [
            "period_month",
            "employee_code",
            "full_name",
            "division_name",
            "Nominal",
            "status",
            "generated_at",
            "generated_by_username",
        ]
    ].rename(
        columns={
            "period_month": "Periode",
            "employee_code": "Kode Pegawai",
            "full_name": "Nama Pegawai",
            "division_name": "Divisi",
            "status": "Status",
            "generated_at": "Dibuat Pada",
            "generated_by_username": "Dibuat Oleh",
        }
    )

    st.dataframe(df_display, use_container_width=True)