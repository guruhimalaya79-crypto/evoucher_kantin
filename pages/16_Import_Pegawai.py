import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    import_employees_from_dataframe,
    get_employees_with_division,
)
from reports import build_employee_import_template


st.set_page_config(
    page_title="Import Pegawai",
    page_icon="📥",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("📥 Import Pegawai dari Excel")

st.write(
    """
    Halaman ini digunakan admin untuk import data pegawai dalam jumlah banyak
    agar tidak perlu input manual satu per satu.
    """
)

st.warning(
    """
    Gunakan template Excel yang disediakan agar format kolom sesuai.
    Jika kode pegawai sudah ada, data akan dilewati dan tidak dibuat dobel.
    """
)

st.divider()

# =========================================================
# DOWNLOAD TEMPLATE
# =========================================================
st.subheader("1. Download Template Excel")

template_file = build_employee_import_template()

st.download_button(
    label="Download Template Import Pegawai",
    data=template_file,
    file_name="template_import_pegawai.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.caption(
    """
    Isi data pegawai pada sheet `template_pegawai`.
    Jangan mengubah nama kolom.
    """
)

st.divider()

# =========================================================
# FORMAT KOLOM
# =========================================================
with st.expander("Lihat Format Kolom"):
    st.markdown(
        """
        Kolom yang dipakai:

        | Kolom | Wajib | Keterangan |
        |---|---|---|
        | employee_code | Ya | Kode pegawai unik, contoh EMP001 |
        | full_name | Ya | Nama lengkap pegawai |
        | division_name | Ya | Nama divisi |
        | phone | Tidak | Nomor HP |
        | email | Tidak | Email |
        | is_active | Tidak | 1 = aktif, 0 = nonaktif |
        """
    )

st.divider()

# =========================================================
# UPLOAD FILE
# =========================================================
st.subheader("2. Upload File Excel Pegawai")

uploaded_file = st.file_uploader(
    "Upload file Excel",
    type=["xlsx"]
)

if uploaded_file is not None:
    try:
        df_upload = pd.read_excel(uploaded_file, sheet_name="template_pegawai")
    except Exception:
        try:
            df_upload = pd.read_excel(uploaded_file)
        except Exception as error:
            st.error(f"Gagal membaca file Excel: {error}")
            st.stop()

    st.write("Preview data yang akan diimport:")

    st.dataframe(df_upload.head(20), use_container_width=True)

    st.caption(f"Total baris terbaca: {len(df_upload)}")

    st.divider()

    confirm_import = st.checkbox(
        "Saya sudah mengecek preview data dan ingin import pegawai."
    )

    if st.button("Import Pegawai", type="primary"):
        if not confirm_import:
            st.error("Centang konfirmasi terlebih dahulu.")
        else:
            result = import_employees_from_dataframe(
                df=df_upload,
                imported_by=st.session_state.user_id,
            )

            if result["success"]:
                st.success(result["message"])

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Berhasil Ditambahkan", result["created"])

                with col2:
                    st.metric("Dilewati / Sudah Ada", result["skipped"])

                with col3:
                    st.metric("Error", len(result["errors"]))

                if result["errors"]:
                    with st.expander("Lihat Detail Error"):
                        for error in result["errors"]:
                            st.error(error)

                st.info("Jika import berhasil, cek daftar pegawai di bagian bawah halaman.")
            else:
                st.error(result["message"])

st.divider()

# =========================================================
# DAFTAR PEGAWAI
# =========================================================
st.subheader("Daftar Pegawai Saat Ini")

employees = get_employees_with_division(include_inactive=True)
df_employees = pd.DataFrame(employees)

if df_employees.empty:
    st.info("Belum ada data pegawai.")
else:
    df_employees["Status"] = df_employees["is_active"].apply(
        lambda value: "Aktif" if value == 1 else "Nonaktif"
    )

    df_display = df_employees[
        [
            "employee_code",
            "full_name",
            "division_name",
            "phone",
            "email",
            "Status",
            "created_at",
        ]
    ].rename(
        columns={
            "employee_code": "Kode Pegawai",
            "full_name": "Nama Pegawai",
            "division_name": "Divisi",
            "phone": "No. HP",
            "email": "Email",
            "created_at": "Dibuat Pada",
        }
    )

    st.dataframe(df_display, use_container_width=True)