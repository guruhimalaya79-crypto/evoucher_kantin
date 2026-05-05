import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    get_period_transaction_dashboard,
    get_transactions_by_period,
    get_daily_usage_report,
    get_division_usage_report,
    get_menu_usage_report,
    get_merchant_payment_report,
    get_employee_balance_report,
    get_transaction_items,
)
from reports import (
    build_excel_report,
    build_merchant_payment_dataframe,
    build_transactions_dataframe,
    build_employee_balance_dataframe,
    build_menu_usage_dataframe,
)
from utils import (
    format_rupiah,
    get_current_period_month,
    is_valid_period_month,
)


st.set_page_config(
    page_title="Laporan",
    page_icon="📑",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("📑 Laporan dan Dashboard Transaksi")

period_month = st.text_input(
    "Periode Laporan",
    value=get_current_period_month(),
    help="Format wajib YYYY-MM. Contoh: 2026-05"
)

period_month_clean = period_month.strip()

if not is_valid_period_month(period_month_clean):
    st.error("Format periode salah. Gunakan format YYYY-MM.")
    st.stop()

st.divider()

# =========================================================
# EXPORT EXCEL
# =========================================================
st.subheader("Export Laporan Excel")

excel_file = build_excel_report(period_month_clean)

st.download_button(
    label="Download Semua Laporan Excel Multi-Sheet",
    data=excel_file,
    file_name=f"laporan_evoucher_kantin_{period_month_clean}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.caption(
    """
    File Excel berisi sheet:
    Info, Pembayaran Pedagang, Transaksi, Saldo Pegawai,
    Rekap Menu, Rekap Harian, dan Rekap Divisi.
    """
)

with st.expander("Download CSV Per Laporan"):
    merchant_csv_df = build_merchant_payment_dataframe(period_month_clean)
    transactions_csv_df = build_transactions_dataframe(period_month_clean)
    balance_csv_df = build_employee_balance_dataframe(period_month_clean)
    menu_csv_df = build_menu_usage_dataframe(period_month_clean)

    st.download_button(
        label="Download CSV Pembayaran Pedagang",
        data=merchant_csv_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"pembayaran_pedagang_{period_month_clean}.csv",
        mime="text/csv",
    )

    st.download_button(
        label="Download CSV Transaksi Periode",
        data=transactions_csv_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"transaksi_{period_month_clean}.csv",
        mime="text/csv",
    )

    st.download_button(
        label="Download CSV Saldo Pegawai",
        data=balance_csv_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"saldo_pegawai_{period_month_clean}.csv",
        mime="text/csv",
    )

    st.download_button(
        label="Download CSV Rekap Menu",
        data=menu_csv_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"rekap_menu_{period_month_clean}.csv",
        mime="text/csv",
    )

# =========================================================
# DASHBOARD TRANSAKSI
# =========================================================
st.subheader("Dashboard Transaksi Periode")

summary = get_period_transaction_dashboard(period_month_clean)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Jumlah Transaksi Valid", summary["total_transactions"])

with col2:
    st.metric("Total Voucher Terpakai", format_rupiah(summary["total_voucher"]))

with col3:
    st.metric("Pegawai Memakai Voucher", summary["employees_used"])

with col4:
    st.metric("Transaksi Void", summary["void_transactions"])

col5, col6, col7, col8 = st.columns(4)

with col5:
    st.metric("Total Alokasi", format_rupiah(summary["total_allocation"]))

with col6:
    st.metric("Sisa Saldo Total", format_rupiah(summary["remaining_total"]))

with col7:
    st.metric("Total Belanja", format_rupiah(summary["total_sales"]))

with col8:
    st.metric("Tunai", format_rupiah(summary["total_cash"]))

st.divider()

# =========================================================
# LAPORAN PEMBAYARAN PEDAGANG
# =========================================================
st.subheader("Laporan Pembayaran Pedagang")

merchant_report = get_merchant_payment_report(period_month_clean)
df_merchant = pd.DataFrame(merchant_report)

if df_merchant.empty:
    st.info("Belum ada data pembayaran pedagang.")
else:
    df_merchant["Total Belanja"] = df_merchant["total_sales"].apply(format_rupiah)
    df_merchant["Total Dibayar Kantor"] = df_merchant["total_voucher_payment"].apply(format_rupiah)
    df_merchant["Total Tunai"] = df_merchant["total_cash"].apply(format_rupiah)

    df_merchant_display = df_merchant[
        [
            "merchant_name",
            "total_transactions",
            "total_employees",
            "Total Belanja",
            "Total Dibayar Kantor",
            "Total Tunai",
        ]
    ].rename(
        columns={
            "merchant_name": "Pedagang",
            "total_transactions": "Jumlah Transaksi",
            "total_employees": "Jumlah Pegawai",
        }
    )

    st.dataframe(df_merchant_display, use_container_width=True)

    total_payment = df_merchant["total_voucher_payment"].sum()
    st.success(
        f"Total yang harus dibayar kantor ke pedagang untuk periode "
        f"{period_month_clean}: {format_rupiah(total_payment)}"
    )

st.divider()

# =========================================================
# LAPORAN HARIAN
# =========================================================
with st.expander("Rekap Penggunaan Harian"):
    daily_report = get_daily_usage_report(period_month_clean)
    df_daily = pd.DataFrame(daily_report)

    if df_daily.empty:
        st.info("Belum ada transaksi harian.")
    else:
        df_daily["Total Voucher"] = df_daily["total_voucher"].apply(format_rupiah)

        df_daily_display = df_daily[
            [
                "transaction_date",
                "total_transactions",
                "total_employees",
                "Total Voucher",
            ]
        ].rename(
            columns={
                "transaction_date": "Tanggal",
                "total_transactions": "Jumlah Transaksi",
                "total_employees": "Jumlah Pegawai",
            }
        )

        st.dataframe(df_daily_display, use_container_width=True)

# =========================================================
# LAPORAN DIVISI
# =========================================================
with st.expander("Rekap Penggunaan per Divisi"):
    division_report = get_division_usage_report(period_month_clean)
    df_division = pd.DataFrame(division_report)

    if df_division.empty:
        st.info("Belum ada penggunaan per divisi.")
    else:
        df_division["Total Voucher"] = df_division["total_voucher"].apply(format_rupiah)

        df_division_display = df_division[
            [
                "division_name",
                "total_transactions",
                "total_employees",
                "Total Voucher",
            ]
        ].rename(
            columns={
                "division_name": "Divisi",
                "total_transactions": "Jumlah Transaksi",
                "total_employees": "Jumlah Pegawai",
            }
        )

        st.dataframe(df_division_display, use_container_width=True)

# =========================================================
# LAPORAN MENU
# =========================================================
with st.expander("Rekap Menu Terjual"):
    menu_report = get_menu_usage_report(period_month_clean)
    df_menu = pd.DataFrame(menu_report)

    if df_menu.empty:
        st.info("Belum ada menu terjual.")
    else:
        df_menu["Total Nilai"] = df_menu["total_subtotal"].apply(format_rupiah)

        df_menu_display = df_menu[
            [
                "item_name_snapshot",
                "total_quantity",
                "Total Nilai",
            ]
        ].rename(
            columns={
                "item_name_snapshot": "Menu",
                "total_quantity": "Total Qty",
            }
        )

        st.dataframe(df_menu_display, use_container_width=True)

# =========================================================
# LAPORAN SALDO PEGAWAI
# =========================================================
with st.expander("Laporan Saldo Pegawai"):
    balance_report = get_employee_balance_report(period_month_clean)
    df_balance = pd.DataFrame(balance_report)

    if df_balance.empty:
        st.info("Belum ada alokasi voucher pada periode ini.")
    else:
        df_balance["Alokasi"] = df_balance["amount_allocated"].apply(format_rupiah)
        df_balance["Terpakai"] = df_balance["used_amount"].apply(format_rupiah)
        df_balance["Sisa"] = df_balance["remaining_balance"].apply(format_rupiah)

        df_balance_display = df_balance[
            [
                "employee_code",
                "full_name",
                "division_name",
                "Alokasi",
                "Terpakai",
                "Sisa",
            ]
        ].rename(
            columns={
                "employee_code": "Kode Pegawai",
                "full_name": "Nama Pegawai",
                "division_name": "Divisi",
            }
        )

        st.dataframe(df_balance_display, use_container_width=True)

# =========================================================
# DETAIL TRANSAKSI
# =========================================================
with st.expander("Detail Semua Transaksi Periode"):
    transactions = get_transactions_by_period(period_month_clean)
    df_transactions = pd.DataFrame(transactions)

    if df_transactions.empty:
        st.info("Belum ada transaksi pada periode ini.")
    else:
        df_transactions["Total"] = df_transactions["total_amount"].apply(format_rupiah)
        df_transactions["Voucher"] = df_transactions["voucher_amount"].apply(format_rupiah)
        df_transactions["Tunai"] = df_transactions["cash_amount"].apply(format_rupiah)
        df_transactions["Status"] = df_transactions["voided_at"].apply(
            lambda value: "Valid" if pd.isna(value) or value is None else "Void"
        )

        df_transactions_display = df_transactions[
            [
                "id",
                "created_at",
                "transaction_date",
                "period_month",
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
            ]
        ].rename(
            columns={
                "id": "ID",
                "created_at": "Waktu Input",
                "transaction_date": "Tanggal",
                "period_month": "Periode",
                "employee_code": "Kode",
                "full_name": "Pegawai",
                "division_name": "Divisi",
                "merchant_name": "Pedagang",
                "notes": "Catatan",
                "created_by_username": "Diinput Oleh",
            }
        )

        st.dataframe(df_transactions_display, use_container_width=True)

        st.divider()
        st.write("Detail item transaksi")

        transaction_ids = [trx["id"] for trx in transactions]

        selected_transaction_id = st.selectbox(
            "Pilih ID Transaksi untuk Lihat Item",
            options=transaction_ids
        )

        items = get_transaction_items(selected_transaction_id)
        df_items = pd.DataFrame(items)

        if df_items.empty:
            st.info("Tidak ada item pada transaksi ini.")
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