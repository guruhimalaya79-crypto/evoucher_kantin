from io import BytesIO

import pandas as pd

from database import (
    get_merchant_payment_report,
    get_transactions_by_period,
    get_employee_balance_report,
    get_menu_usage_report,
    get_daily_usage_report,
    get_division_usage_report,
)
from utils import get_now_text


def build_merchant_payment_dataframe(period_month):
    data = get_merchant_payment_report(period_month)
    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "Pedagang",
                "Jumlah Transaksi",
                "Jumlah Pegawai",
                "Total Belanja",
                "Total Dibayar Kantor",
                "Total Tunai",
            ]
        )

    df = df.rename(
        columns={
            "merchant_name": "Pedagang",
            "total_transactions": "Jumlah Transaksi",
            "total_employees": "Jumlah Pegawai",
            "total_sales": "Total Belanja",
            "total_voucher_payment": "Total Dibayar Kantor",
            "total_cash": "Total Tunai",
        }
    )

    return df[
        [
            "Pedagang",
            "Jumlah Transaksi",
            "Jumlah Pegawai",
            "Total Belanja",
            "Total Dibayar Kantor",
            "Total Tunai",
        ]
    ]


def build_transactions_dataframe(period_month):
    data = get_transactions_by_period(period_month)
    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "ID",
                "Waktu Input",
                "Tanggal",
                "Periode",
                "Kode Pegawai",
                "Nama Pegawai",
                "Divisi",
                "Pedagang",
                "Total Belanja",
                "Voucher",
                "Tunai",
                "Status",
                "Catatan",
                "Diinput Oleh",
                "Waktu Void",
                "Alasan Void",
            ]
        )

    df["Status"] = df["voided_at"].apply(
        lambda value: "Valid" if pd.isna(value) or value is None else "Void"
    )

    df = df.rename(
        columns={
            "id": "ID",
            "created_at": "Waktu Input",
            "transaction_date": "Tanggal",
            "period_month": "Periode",
            "employee_code": "Kode Pegawai",
            "full_name": "Nama Pegawai",
            "division_name": "Divisi",
            "merchant_name": "Pedagang",
            "total_amount": "Total Belanja",
            "voucher_amount": "Voucher",
            "cash_amount": "Tunai",
            "notes": "Catatan",
            "created_by_username": "Diinput Oleh",
            "voided_at": "Waktu Void",
            "void_reason": "Alasan Void",
        }
    )

    return df[
        [
            "ID",
            "Waktu Input",
            "Tanggal",
            "Periode",
            "Kode Pegawai",
            "Nama Pegawai",
            "Divisi",
            "Pedagang",
            "Total Belanja",
            "Voucher",
            "Tunai",
            "Status",
            "Catatan",
            "Diinput Oleh",
            "Waktu Void",
            "Alasan Void",
        ]
    ]


def build_employee_balance_dataframe(period_month):
    data = get_employee_balance_report(period_month)
    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "Kode Pegawai",
                "Nama Pegawai",
                "Divisi",
                "Alokasi",
                "Terpakai",
                "Sisa",
            ]
        )

    df = df.rename(
        columns={
            "employee_code": "Kode Pegawai",
            "full_name": "Nama Pegawai",
            "division_name": "Divisi",
            "amount_allocated": "Alokasi",
            "used_amount": "Terpakai",
            "remaining_balance": "Sisa",
        }
    )

    return df[
        [
            "Kode Pegawai",
            "Nama Pegawai",
            "Divisi",
            "Alokasi",
            "Terpakai",
            "Sisa",
        ]
    ]


def build_menu_usage_dataframe(period_month):
    data = get_menu_usage_report(period_month)
    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "Menu",
                "Total Qty",
                "Total Nilai",
            ]
        )

    df = df.rename(
        columns={
            "item_name_snapshot": "Menu",
            "total_quantity": "Total Qty",
            "total_subtotal": "Total Nilai",
        }
    )

    return df[
        [
            "Menu",
            "Total Qty",
            "Total Nilai",
        ]
    ]


def build_daily_usage_dataframe(period_month):
    data = get_daily_usage_report(period_month)
    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "Tanggal",
                "Jumlah Transaksi",
                "Jumlah Pegawai",
                "Total Voucher",
            ]
        )

    df = df.rename(
        columns={
            "transaction_date": "Tanggal",
            "total_transactions": "Jumlah Transaksi",
            "total_employees": "Jumlah Pegawai",
            "total_voucher": "Total Voucher",
        }
    )

    return df[
        [
            "Tanggal",
            "Jumlah Transaksi",
            "Jumlah Pegawai",
            "Total Voucher",
        ]
    ]


def build_division_usage_dataframe(period_month):
    data = get_division_usage_report(period_month)
    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "Divisi",
                "Jumlah Transaksi",
                "Jumlah Pegawai",
                "Total Voucher",
            ]
        )

    df = df.rename(
        columns={
            "division_name": "Divisi",
            "total_transactions": "Jumlah Transaksi",
            "total_employees": "Jumlah Pegawai",
            "total_voucher": "Total Voucher",
        }
    )

    return df[
        [
            "Divisi",
            "Jumlah Transaksi",
            "Jumlah Pegawai",
            "Total Voucher",
        ]
    ]


def autosize_excel_columns(writer, sheet_name, dataframe):
    worksheet = writer.sheets[sheet_name]

    for idx, column in enumerate(dataframe.columns, start=1):
        max_length = len(str(column))

        for value in dataframe[column]:
            if value is not None:
                max_length = max(max_length, len(str(value)))

        adjusted_width = min(max_length + 2, 45)
        column_letter = worksheet.cell(row=1, column=idx).column_letter
        worksheet.column_dimensions[column_letter].width = adjusted_width


def build_excel_report(period_month):
    """
    Membuat file Excel multi-sheet dalam bentuk BytesIO.
    Nanti dipakai oleh st.download_button().
    """
    output = BytesIO()

    merchant_df = build_merchant_payment_dataframe(period_month)
    transactions_df = build_transactions_dataframe(period_month)
    balance_df = build_employee_balance_dataframe(period_month)
    menu_df = build_menu_usage_dataframe(period_month)
    daily_df = build_daily_usage_dataframe(period_month)
    division_df = build_division_usage_dataframe(period_month)

    metadata_df = pd.DataFrame(
        [
            {"Keterangan": "Periode", "Nilai": period_month},
            {"Keterangan": "Dibuat Pada", "Nilai": get_now_text()},
            {"Keterangan": "Aplikasi", "Nilai": "Sistem E-Voucher Kantin"},
        ]
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        metadata_df.to_excel(writer, index=False, sheet_name="Info")
        merchant_df.to_excel(writer, index=False, sheet_name="Pembayaran Pedagang")
        transactions_df.to_excel(writer, index=False, sheet_name="Transaksi")
        balance_df.to_excel(writer, index=False, sheet_name="Saldo Pegawai")
        menu_df.to_excel(writer, index=False, sheet_name="Rekap Menu")
        daily_df.to_excel(writer, index=False, sheet_name="Rekap Harian")
        division_df.to_excel(writer, index=False, sheet_name="Rekap Divisi")

        for sheet_name, df in {
            "Info": metadata_df,
            "Pembayaran Pedagang": merchant_df,
            "Transaksi": transactions_df,
            "Saldo Pegawai": balance_df,
            "Rekap Menu": menu_df,
            "Rekap Harian": daily_df,
            "Rekap Divisi": division_df,
        }.items():
            autosize_excel_columns(writer, sheet_name, df)

    output.seek(0)
    return output

def build_employee_import_template():
    """
    Membuat template Excel untuk import pegawai.
    """
    output = BytesIO()

    template_df = pd.DataFrame(
        [
            {
                "employee_code": "EMP001",
                "full_name": "Budi Santoso",
                "division_name": "IT",
                "phone": "081111111001",
                "email": "budi@example.com",
                "is_active": 1,
            },
            {
                "employee_code": "EMP002",
                "full_name": "Siti Aminah",
                "division_name": "SDM",
                "phone": "081111111002",
                "email": "siti@example.com",
                "is_active": 1,
            },
            {
                "employee_code": "EMP003",
                "full_name": "Joko Permana",
                "division_name": "Umum",
                "phone": "081111111003",
                "email": "joko@example.com",
                "is_active": 0,
            },
        ]
    )

    instruction_df = pd.DataFrame(
        [
            {
                "Kolom": "employee_code",
                "Wajib": "Ya",
                "Keterangan": "Kode pegawai unik. Contoh: EMP001",
            },
            {
                "Kolom": "full_name",
                "Wajib": "Ya",
                "Keterangan": "Nama lengkap pegawai.",
            },
            {
                "Kolom": "division_name",
                "Wajib": "Ya",
                "Keterangan": "Nama divisi. Jika belum ada, sistem akan membuat otomatis.",
            },
            {
                "Kolom": "phone",
                "Wajib": "Tidak",
                "Keterangan": "Nomor HP pegawai.",
            },
            {
                "Kolom": "email",
                "Wajib": "Tidak",
                "Keterangan": "Email pegawai.",
            },
            {
                "Kolom": "is_active",
                "Wajib": "Tidak",
                "Keterangan": "1 = Aktif, 0 = Nonaktif. Jika kosong dianggap aktif.",
            },
        ]
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="template_pegawai")
        instruction_df.to_excel(writer, index=False, sheet_name="petunjuk")

        autosize_excel_columns(writer, "template_pegawai", template_df)
        autosize_excel_columns(writer, "petunjuk", instruction_df)

    output.seek(0)
    return output

def build_generated_credentials_excel(credentials):
    """
    Membuat Excel berisi username dan password awal hasil generate.
    File ini sebaiknya hanya dipegang admin.
    """
    output = BytesIO()

    df_credentials = pd.DataFrame(credentials)

    if df_credentials.empty:
        df_credentials = pd.DataFrame(
            columns=[
                "employee_code",
                "full_name",
                "division_name",
                "username",
                "initial_password",
                "role",
            ]
        )

    df_credentials = df_credentials.rename(
        columns={
            "employee_code": "Kode Pegawai",
            "full_name": "Nama Pegawai",
            "division_name": "Divisi",
            "username": "Username",
            "initial_password": "Password Awal",
            "role": "Role",
        }
    )

    instruction_df = pd.DataFrame(
        [
            {
                "Catatan": "File ini berisi password awal. Simpan dengan aman dan jangan dibagikan sembarangan."
            },
            {
                "Catatan": "Pegawai disarankan mengganti password setelah login pertama."
            },
            {
                "Catatan": "Jika password lupa, admin dapat reset password dari halaman Manajemen User."
            },
        ]
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_credentials.to_excel(writer, index=False, sheet_name="akun_pegawai")
        instruction_df.to_excel(writer, index=False, sheet_name="catatan")

        autosize_excel_columns(writer, "akun_pegawai", df_credentials)
        autosize_excel_columns(writer, "catatan", instruction_df)

    output.seek(0)
    return output

