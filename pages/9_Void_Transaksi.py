import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    get_voidable_transactions,
    get_transaction_by_id,
    get_transaction_items,
    void_transaction,
    get_void_transaction_summary,
)
from utils import (
    format_rupiah,
    get_current_period_month,
    is_valid_period_month,
)


st.set_page_config(
    page_title="Void Transaksi",
    page_icon="🚫",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("🚫 Void / Cancel Transaksi")

st.write(
    """
    Gunakan halaman ini jika ada transaksi yang salah input.
    Transaksi tidak dihapus dari database, tetapi diberi status void agar audit tetap aman.
    """
)

st.warning(
    """
    Hati-hati: transaksi yang sudah di-void tidak akan dihitung lagi dalam saldo pegawai
    dan laporan pembayaran pedagang.
    """
)

st.divider()

period_month = st.text_input(
    "Periode",
    value=get_current_period_month(),
    help="Format wajib YYYY-MM. Contoh: 2026-05"
)

period_month_clean = period_month.strip()

if not is_valid_period_month(period_month_clean):
    st.error("Format periode salah. Gunakan format YYYY-MM.")
    st.stop()

summary = get_void_transaction_summary(period_month_clean)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Transaksi Valid", summary["total_valid"])

with col2:
    st.metric("Transaksi Void", summary["total_void"])

with col3:
    st.metric("Voucher Valid", format_rupiah(summary["total_valid_voucher"]))

with col4:
    st.metric("Voucher Void", format_rupiah(summary["total_void_voucher"]))

st.divider()

st.subheader("Daftar Transaksi Periode")

transactions = get_voidable_transactions(period_month_clean)
df = pd.DataFrame(transactions)

if df.empty:
    st.info("Belum ada transaksi pada periode ini.")
    st.stop()

df["Total"] = df["total_amount"].apply(format_rupiah)
df["Voucher"] = df["voucher_amount"].apply(format_rupiah)
df["Tunai"] = df["cash_amount"].apply(format_rupiah)
df["Status"] = df["voided_at"].apply(
    lambda value: "Valid" if pd.isna(value) or value is None else "Void"
)

df_display = df[
    [
        "id",
        "created_at",
        "transaction_date",
        "employee_code",
        "full_name",
        "division_name",
        "merchant_name",
        "Total",
        "Voucher",
        "Tunai",
        "Status",
        "notes",
        "created_by_username",
        "voided_at",
        "voided_by_username",
        "void_reason",
    ]
].rename(
    columns={
        "id": "ID",
        "created_at": "Waktu Input",
        "transaction_date": "Tanggal",
        "employee_code": "Kode",
        "full_name": "Pegawai",
        "division_name": "Divisi",
        "merchant_name": "Pedagang",
        "notes": "Catatan",
        "created_by_username": "Diinput Oleh",
        "voided_at": "Waktu Void",
        "voided_by_username": "Divoid Oleh",
        "void_reason": "Alasan Void",
    }
)

st.dataframe(df_display, use_container_width=True)

st.divider()

st.subheader("Void Transaksi")

valid_transactions = [
    trx for trx in transactions
    if trx["voided_at"] is None
]

if len(valid_transactions) == 0:
    st.info("Tidak ada transaksi valid yang bisa di-void pada periode ini.")
    st.stop()

transaction_options = {}

for trx in valid_transactions:
    label = (
        f'ID {trx["id"]} | '
        f'{trx["created_at"]} | '
        f'{trx["employee_code"]} - {trx["full_name"]} | '
        f'{format_rupiah(trx["voucher_amount"])}'
    )
    transaction_options[label] = trx["id"]

selected_label = st.selectbox(
    "Pilih Transaksi yang Akan Divoid",
    options=list(transaction_options.keys())
)

selected_transaction_id = transaction_options[selected_label]
selected_transaction = get_transaction_by_id(selected_transaction_id)

if selected_transaction is None:
    st.error("Transaksi tidak ditemukan.")
    st.stop()

st.write("Detail transaksi yang dipilih:")

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    st.metric("ID Transaksi", selected_transaction["id"])

with col_b:
    st.metric("Pegawai", selected_transaction["full_name"])

with col_c:
    st.metric("Voucher", format_rupiah(selected_transaction["voucher_amount"]))

with col_d:
    status_text = "Valid" if selected_transaction["voided_at"] is None else "Void"
    st.metric("Status", status_text)

col_e, col_f, col_g = st.columns(3)

with col_e:
    st.write("Tanggal:", selected_transaction["transaction_date"])

with col_f:
    st.write("Periode:", selected_transaction["period_month"])

with col_g:
    st.write("Pedagang:", selected_transaction["merchant_name"])

st.write("Catatan transaksi:", selected_transaction["notes"] or "-")

st.subheader("Detail Item")

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

st.divider()

with st.form("form_void_transaksi"):
    void_reason = st.text_area(
        "Alasan Void",
        placeholder="Contoh: nominal salah input, pegawai salah pilih, transaksi dobel, dll."
    )

    confirm_void = st.checkbox(
        "Saya yakin ingin melakukan void transaksi ini."
    )

    submitted = st.form_submit_button("Void Transaksi")

    if submitted:
        if not confirm_void:
            st.error("Centang konfirmasi terlebih dahulu.")
        else:
            result = void_transaction(
                transaction_id=selected_transaction_id,
                void_reason=void_reason,
                voided_by=st.session_state.user_id,
            )

            if result["success"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])