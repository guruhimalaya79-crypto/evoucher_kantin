import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    get_divisions,
    get_employees_with_division,
    employee_code_exists_final,
    add_employee_final,
    update_employee_final,
)


st.set_page_config(
    page_title="Master Pegawai",
    page_icon="👥",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("👥 Master Pegawai")

st.write("Kelola data pegawai. Divisi dipilih dari master divisi, bukan diketik manual.")

active_divisions = get_divisions(include_inactive=False)

if len(active_divisions) == 0:
    st.warning("Belum ada divisi aktif. Tambahkan divisi terlebih dahulu.")
    st.stop()

st.divider()

st.subheader("Tambah Pegawai")

division_options = {
    d["division_name"]: d["id"]
    for d in active_divisions
}

with st.form("form_tambah_pegawai"):
    employee_code = st.text_input("Kode Pegawai", placeholder="Contoh: EMP007")
    full_name = st.text_input("Nama Lengkap", placeholder="Contoh: Ahmad Fauzi")
    selected_division_name = st.selectbox("Divisi", list(division_options.keys()))
    phone = st.text_input("No. HP", placeholder="Opsional")
    email = st.text_input("Email", placeholder="Opsional")
    status = st.selectbox("Status", ["Aktif", "Nonaktif"])

    submitted = st.form_submit_button("Simpan Pegawai")

    if submitted:
        employee_code_clean = employee_code.strip().upper()
        full_name_clean = full_name.strip()
        phone_clean = phone.strip()
        email_clean = email.strip()
        division_id = division_options[selected_division_name]
        is_active = 1 if status == "Aktif" else 0

        if employee_code_clean == "":
            st.error("Kode pegawai tidak boleh kosong.")
        elif full_name_clean == "":
            st.error("Nama lengkap tidak boleh kosong.")
        elif employee_code_exists_final(employee_code_clean):
            st.error("Kode pegawai sudah digunakan.")
        else:
            add_employee_final(
                employee_code=employee_code_clean,
                full_name=full_name_clean,
                division_id=division_id,
                phone=phone_clean,
                email=email_clean,
                is_active=is_active,
                created_by=st.session_state.user_id,
            )
            st.success("Pegawai berhasil ditambahkan.")
            st.rerun()

st.divider()

st.subheader("Edit Pegawai")

employees = get_employees_with_division(include_inactive=True)

if len(employees) == 0:
    st.warning("Belum ada data pegawai.")
else:
    employee_options = {
        f'{e["employee_code"]} - {e["full_name"]}': e
        for e in employees
    }

    selected_employee_label = st.selectbox("Pilih Pegawai", list(employee_options.keys()))
    selected_employee = employee_options[selected_employee_label]

    division_names = list(division_options.keys())

    current_division_name = selected_employee["division_name"]
    if current_division_name not in division_names:
        current_division_index = 0
    else:
        current_division_index = division_names.index(current_division_name)

    with st.form("form_edit_pegawai"):
        edit_employee_code = st.text_input(
            "Kode Pegawai",
            value=selected_employee["employee_code"]
        )
        edit_full_name = st.text_input(
            "Nama Lengkap",
            value=selected_employee["full_name"]
        )
        edit_division_name = st.selectbox(
            "Divisi",
            division_names,
            index=current_division_index
        )
        edit_phone = st.text_input(
            "No. HP",
            value=selected_employee["phone"] or ""
        )
        edit_email = st.text_input(
            "Email",
            value=selected_employee["email"] or ""
        )
        edit_status = st.selectbox(
            "Status",
            ["Aktif", "Nonaktif"],
            index=0 if selected_employee["is_active"] == 1 else 1
        )

        submitted_edit = st.form_submit_button("Update Pegawai")

        if submitted_edit:
            edit_employee_code_clean = edit_employee_code.strip().upper()
            edit_full_name_clean = edit_full_name.strip()
            edit_division_id = division_options[edit_division_name]
            edit_phone_clean = edit_phone.strip()
            edit_email_clean = edit_email.strip()
            edit_is_active = 1 if edit_status == "Aktif" else 0

            if edit_employee_code_clean == "":
                st.error("Kode pegawai tidak boleh kosong.")
            elif edit_full_name_clean == "":
                st.error("Nama lengkap tidak boleh kosong.")
            elif employee_code_exists_final(
                edit_employee_code_clean,
                exclude_id=selected_employee["id"]
            ):
                st.error("Kode pegawai sudah digunakan oleh pegawai lain.")
            else:
                update_employee_final(
                    employee_id=selected_employee["id"],
                    employee_code=edit_employee_code_clean,
                    full_name=edit_full_name_clean,
                    division_id=edit_division_id,
                    phone=edit_phone_clean,
                    email=edit_email_clean,
                    is_active=edit_is_active,
                    updated_by=st.session_state.user_id,
                )
                st.success("Pegawai berhasil diupdate.")
                st.rerun()

st.divider()

st.subheader("Daftar Pegawai")

df = pd.DataFrame(get_employees_with_division(include_inactive=True))

if df.empty:
    st.info("Belum ada data pegawai.")
else:
    df["Status"] = df["is_active"].apply(lambda x: "Aktif" if x == 1 else "Nonaktif")

    df_display = df[
        [
            "employee_code",
            "full_name",
            "division_name",
            "phone",
            "email",
            "Status",
            "created_at",
            "updated_at",
        ]
    ].rename(
        columns={
            "employee_code": "Kode Pegawai",
            "full_name": "Nama Lengkap",
            "division_name": "Divisi",
            "phone": "No. HP",
            "email": "Email",
            "created_at": "Dibuat Pada",
            "updated_at": "Diupdate Pada",
        }
    )

    st.dataframe(df_display, use_container_width=True)