import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    get_employee_user_generation_summary,
    get_employees_for_user_generation,
    generate_employee_users,
    get_users_with_employee,
)
from reports import build_generated_credentials_excel


st.set_page_config(
    page_title="Generate User Pegawai",
    page_icon="🪪",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("🪪 Generate User Pegawai Otomatis")

st.write(
    """
    Halaman ini digunakan admin untuk membuat akun login pegawai secara otomatis
    berdasarkan data pegawai yang sudah ada.
    """
)

st.warning(
    """
    Password awal akan tampil hanya setelah proses generate.
    Download file Excel credential dan simpan dengan aman.
    Setelah itu pegawai disarankan mengganti password sendiri.
    """
)

st.divider()

# =========================================================
# RINGKASAN
# =========================================================
st.subheader("Ringkasan Akun Pegawai")

summary = get_employee_user_generation_summary()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Pegawai Aktif", summary["active_employees"])

with col2:
    st.metric("User Pegawai Terhubung", summary["employee_users"])

with col3:
    st.metric("Pegawai Aktif Belum Punya User", summary["active_without_user"])

st.divider()

# =========================================================
# PREVIEW PEGAWAI BELUM PUNYA USER
# =========================================================
st.subheader("Preview Pegawai yang Belum Punya User")

only_active = st.checkbox(
    "Hanya pegawai aktif",
    value=True
)

employees_without_user = get_employees_for_user_generation(
    only_active=only_active
)

df_preview = pd.DataFrame(employees_without_user)

if df_preview.empty:
    st.success("Semua pegawai pada filter ini sudah memiliki user.")
else:
    df_preview_display = df_preview[
        [
            "employee_code",
            "full_name",
            "division_name",
            "is_active",
        ]
    ].copy()

    df_preview_display["Status"] = df_preview_display["is_active"].apply(
        lambda value: "Aktif" if value == 1 else "Nonaktif"
    )

    df_preview_display = df_preview_display[
        [
            "employee_code",
            "full_name",
            "division_name",
            "Status",
        ]
    ].rename(
        columns={
            "employee_code": "Kode Pegawai",
            "full_name": "Nama Pegawai",
            "division_name": "Divisi",
        }
    )

    st.dataframe(df_preview_display, use_container_width=True)

st.divider()

# =========================================================
# GENERATE USER
# =========================================================
st.subheader("Generate User Pegawai")

st.write(
    """
    Pola username:
    - dibuat dari kode pegawai
    - huruf kecil
    - hanya huruf dan angka

    Contoh:
    - EMP001 → emp001
    - NIP-2024-001 → nip2024001
    """
)

password_suffix = st.text_input(
    "Suffix Password Awal",
    value="123",
    help="Contoh: username emp001 + suffix 123 = emp001123"
)

st.caption(
    """
    Rekomendasi demo: gunakan suffix `123`.
    Untuk operasional nyata, gunakan password awal yang lebih aman,
    lalu minta pegawai mengganti password.
    """
)

confirm_generate = st.checkbox(
    "Saya yakin ingin membuat user pegawai otomatis."
)

if "generated_employee_credentials" not in st.session_state:
    st.session_state.generated_employee_credentials = []

if st.button("Generate User Pegawai", type="primary"):
    if not confirm_generate:
        st.error("Centang konfirmasi terlebih dahulu.")
    elif password_suffix.strip() == "":
        st.error("Suffix password tidak boleh kosong.")
    elif len(employees_without_user) == 0:
        st.info("Tidak ada pegawai yang perlu dibuatkan user.")
    else:
        result = generate_employee_users(
            only_active=only_active,
            password_suffix=password_suffix.strip(),
            created_by=st.session_state.user_id,
        )

        if result["success"]:
            st.success(result["message"])

            col_r1, col_r2, col_r3 = st.columns(3)

            with col_r1:
                st.metric("User Dibuat", result["created"])

            with col_r2:
                st.metric("Dilewati", result["skipped"])

            with col_r3:
                st.metric("Error", len(result["errors"]))

            st.session_state.generated_employee_credentials = result["credentials"]

            if result["errors"]:
                with st.expander("Lihat Error / Dilewati"):
                    for error in result["errors"]:
                        st.warning(error)

        else:
            st.error(result["message"])

# =========================================================
# DOWNLOAD CREDENTIAL HASIL GENERATE
# =========================================================
if st.session_state.generated_employee_credentials:
    st.divider()
    st.subheader("Download Akun Hasil Generate")

    df_credentials = pd.DataFrame(st.session_state.generated_employee_credentials)

    df_credentials_display = df_credentials.rename(
        columns={
            "employee_code": "Kode Pegawai",
            "full_name": "Nama Pegawai",
            "division_name": "Divisi",
            "username": "Username",
            "initial_password": "Password Awal",
            "role": "Role",
        }
    )

    st.dataframe(df_credentials_display, use_container_width=True)

    excel_file = build_generated_credentials_excel(
        st.session_state.generated_employee_credentials
    )

    st.download_button(
        label="Download Excel Akun Pegawai",
        data=excel_file,
        file_name="akun_pegawai_hasil_generate.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.warning(
        """
        Simpan file akun ini dengan aman. File ini berisi password awal pegawai.
        """
    )

st.divider()

# =========================================================
# DAFTAR USER
# =========================================================
st.subheader("Daftar User Saat Ini")

users = get_users_with_employee()
df_users = pd.DataFrame(users)

if df_users.empty:
    st.info("Belum ada user.")
else:
    df_users["Status"] = df_users["is_active"].apply(
        lambda value: "Aktif" if value == 1 else "Nonaktif"
    )

    df_users_display = df_users[
        [
            "username",
            "role",
            "employee_code",
            "full_name",
            "division_name",
            "Status",
            "last_login_at",
        ]
    ].rename(
        columns={
            "username": "Username",
            "role": "Role",
            "employee_code": "Kode Pegawai",
            "full_name": "Nama Pegawai",
            "division_name": "Divisi",
            "last_login_at": "Login Terakhir",
        }
    )

    st.dataframe(df_users_display, use_container_width=True)