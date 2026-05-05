import streamlit as st
import pandas as pd

from auth import init_session, require_login, show_user_sidebar
from database import (
    setup_database,
    get_pos_active_employees,
    get_employee_detail_with_division,
    get_employee_voucher_summary_final,
    get_employee_transaction_history,
    get_transaction_items,
)
from utils import (
    format_rupiah,
    get_current_period_month,
    is_valid_period_month,
)


st.set_page_config(
    page_title="Saldo Pegawai",
    page_icon="👤",
    layout="wide",
)

setup_database()
init_session()
require_login()
show_user_sidebar()

st.title("👤 Saldo Pegawai dan Riwayat Voucher")

role = st.session_state.role

period_month = st.text_input(
    "Periode",
    value=get_current_period_month(),
    help="Format wajib YYYY-MM. Contoh: 2026-05"
)

period_month_clean = period_month.strip()

if not is_valid_period_month(period_month_clean):
    st.error("Format periode salah. Gunakan format YYYY-MM.")
    st.stop()

if role == "pegawai":
    selected_employee_id = st.session_state.employee_id

    if selected_employee_id is None:
        st.error("Akun pegawai ini belum terhubung dengan data pegawai.")
        st.stop()

else:
    employees = get_pos_active_employees()

    if len(employees) == 0:
        st.warning("Belum ada pegawai aktif.")
        st.stop()

    employee_options = {}

    for employee in employees:
        label = (
            f'{employee["employee_code"]} - '
            f'{employee["full_name"]} - '
            f'{employee["division_name"] or "-"}'
        )
        employee_options[label] = employee["id"]

    selected_employee_label = st.selectbox(
        "Pilih Pegawai",
        options=list(employee_options.keys())
    )

    selected_employee_id = employee_options[selected_employee_label]

summary = get_employee_voucher_summary_final(
    employee_id=selected_employee_id,
    period_month=period_month_clean,
)

employee = summary["employee"]

if employee is None:
    st.error("Data pegawai tidak ditemukan.")
    st.stop()

st.divider()

st.subheader("Informasi Pegawai")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Kode Pegawai", employee["employee_code"])

with col2:
    st.metric("Nama", employee["full_name"])

with col3:
    st.metric("Divisi", employee["division_name"] or "-")

with col4:
    status_text = "Aktif" if employee["is_active"] == 1 else "Nonaktif"
    st.metric("Status", status_text)

if employee["is_active"] != 1:
    st.warning("Pegawai ini nonaktif.")

if not summary["has_allocation"]:
    st.warning("Pegawai belum memiliki alokasi voucher pada periode ini.")

st.divider()

st.subheader("Ringkasan Saldo")

col_s1, col_s2, col_s3, col_s4 = st.columns(4)

with col_s1:
    st.metric("Alokasi", format_rupiah(summary["allocation"]))

with col_s2:
    st.metric("Terpakai", format_rupiah(summary["used"]))

with col_s3:
    st.metric("Sisa Saldo", format_rupiah(summary["balance"]))

with col_s4:
    st.metric("Transaksi Valid", summary["valid_transaction_count"])

allocation = summary["allocation"]
used = summary["used"]

if allocation > 0:
    usage_percent = used / allocation
    st.progress(min(usage_percent, 1.0))
    st.caption(f"Persentase pemakaian: {usage_percent * 100:.1f}%")
else:
    st.progress(0)
    st.caption("Belum ada alokasi voucher.")

st.divider()

st.subheader("Riwayat Transaksi Pegawai")

transactions = get_employee_transaction_history(
    employee_id=selected_employee_id,
    period_month=period_month_clean,
)

df = pd.DataFrame(transactions)

if df.empty:
    st.info("Belum ada transaksi pada periode ini.")
else:
    df["Total"] = df["total_amount"].apply(format_rupiah)
    df["Voucher"] = df["voucher_amount"].apply(format_rupiah)
    df["Tunai"] = df["cash_amount"].apply(format_rupiah)
    df["Status"] = df["voided_at"].apply(
        lambda value: "Valid" if pd.isna(value) or value is None else "Void"
    )

    df_display = df[
        [
            "id",
            "transaction_date",
            "period_month",
            "merchant_name",
            "Total",
            "Voucher",
            "Tunai",
            "Status",
            "notes",
            "created_at",
        ]
    ].rename(
        columns={
            "id": "ID",
            "transaction_date": "Tanggal",
            "period_month": "Periode",
            "merchant_name": "Pedagang",
            "notes": "Catatan",
            "created_at": "Waktu Input",
        }
    )

    st.dataframe(df_display, use_container_width=True)

    st.divider()

    st.subheader("Detail Item Transaksi")

    transaction_ids = [trx["id"] for trx in transactions]

    selected_transaction_id = st.selectbox(
        "Pilih ID Transaksi",
        options=transaction_ids
    )

    items = get_transaction_items(selected_transaction_id)
    df_items = pd.DataFrame(items)

    if df_items.empty:
        st.info("Tidak ada detail item.")
    else:
        df_items["Harga"] = df_items["price_snapshot"].apply(format_rupiah)
        df_items["Subtotal"] = df_items["subtotal"].apply(format_rupiah)

        df_items_display = df_items[
            [
                "item_name_snapshot",
                "Harga",
                "quantity",
                "Subtotal",
            ]
        ].rename(
            columns={
                "item_name_snapshot": "Nama Item",
                "quantity": "Qty",
            }
        )

        st.dataframe(df_items_display, use_container_width=True)