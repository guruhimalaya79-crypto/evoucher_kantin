import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    get_divisions,
    division_name_exists,
    add_division,
    update_division,
)


st.set_page_config(
    page_title="Master Divisi",
    page_icon="🏢",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("🏢 Master Divisi")

st.write("Kelola daftar divisi. Divisi nanti dipilih saat input pegawai.")

st.divider()

st.subheader("Tambah Divisi")

with st.form("form_tambah_divisi"):
    division_name = st.text_input("Nama Divisi", placeholder="Contoh: Humas")

    submitted = st.form_submit_button("Simpan Divisi")

    if submitted:
        division_name_clean = division_name.strip()

        if division_name_clean == "":
            st.error("Nama divisi tidak boleh kosong.")
        elif division_name_exists(division_name_clean):
            st.error("Nama divisi sudah ada.")
        else:
            add_division(
                division_name=division_name_clean,
                created_by=st.session_state.user_id
            )
            st.success("Divisi berhasil ditambahkan.")
            st.rerun()

st.divider()

st.subheader("Edit Divisi")

divisions = get_divisions(include_inactive=True)

if len(divisions) == 0:
    st.warning("Belum ada data divisi.")
else:
    division_options = {
        f'{d["division_name"]} - {"Aktif" if d["is_active"] == 1 else "Nonaktif"}': d
        for d in divisions
    }

    selected_label = st.selectbox("Pilih Divisi", list(division_options.keys()))
    selected_division = division_options[selected_label]

    with st.form("form_edit_divisi"):
        edit_name = st.text_input(
            "Nama Divisi",
            value=selected_division["division_name"]
        )

        edit_status = st.selectbox(
            "Status",
            options=["Aktif", "Nonaktif"],
            index=0 if selected_division["is_active"] == 1 else 1
        )

        submitted_edit = st.form_submit_button("Update Divisi")

        if submitted_edit:
            edit_name_clean = edit_name.strip()
            edit_active_value = 1 if edit_status == "Aktif" else 0

            if edit_name_clean == "":
                st.error("Nama divisi tidak boleh kosong.")
            elif division_name_exists(edit_name_clean, exclude_id=selected_division["id"]):
                st.error("Nama divisi sudah digunakan oleh data lain.")
            else:
                update_division(
                    division_id=selected_division["id"],
                    division_name=edit_name_clean,
                    is_active=edit_active_value,
                    updated_by=st.session_state.user_id
                )
                st.success("Divisi berhasil diupdate.")
                st.rerun()

st.divider()

st.subheader("Daftar Divisi")

df = pd.DataFrame(get_divisions(include_inactive=True))

if df.empty:
    st.info("Belum ada data divisi.")
else:
    df["Status"] = df["is_active"].apply(lambda x: "Aktif" if x == 1 else "Nonaktif")

    df_display = df[
        ["division_name", "Status", "created_at", "updated_at"]
    ].rename(
        columns={
            "division_name": "Nama Divisi",
            "created_at": "Dibuat Pada",
            "updated_at": "Diupdate Pada",
        }
    )

    st.dataframe(df_display, use_container_width=True)