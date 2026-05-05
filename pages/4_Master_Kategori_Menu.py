import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    get_food_categories,
    food_category_name_exists,
    add_food_category,
    update_food_category,
)


st.set_page_config(
    page_title="Master Kategori Menu",
    page_icon="🍱",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("🍱 Master Kategori Menu")

st.write("Kelola kategori makanan/minuman untuk mini POS kasir.")

st.divider()

st.subheader("Tambah Kategori Menu")

with st.form("form_tambah_kategori"):
    category_name = st.text_input("Nama Kategori", placeholder="Contoh: Paket Sarapan")

    submitted = st.form_submit_button("Simpan Kategori")

    if submitted:
        category_name_clean = category_name.strip()

        if category_name_clean == "":
            st.error("Nama kategori tidak boleh kosong.")
        elif food_category_name_exists(category_name_clean):
            st.error("Nama kategori sudah ada.")
        else:
            add_food_category(
                category_name=category_name_clean,
                created_by=st.session_state.user_id
            )
            st.success("Kategori berhasil ditambahkan.")
            st.rerun()

st.divider()

st.subheader("Edit Kategori Menu")

categories = get_food_categories(include_inactive=True)

if len(categories) == 0:
    st.warning("Belum ada data kategori.")
else:
    category_options = {
        f'{c["category_name"]} - {"Aktif" if c["is_active"] == 1 else "Nonaktif"}': c
        for c in categories
    }

    selected_label = st.selectbox("Pilih Kategori", list(category_options.keys()))
    selected_category = category_options[selected_label]

    with st.form("form_edit_kategori"):
        edit_name = st.text_input(
            "Nama Kategori",
            value=selected_category["category_name"]
        )

        edit_status = st.selectbox(
            "Status",
            ["Aktif", "Nonaktif"],
            index=0 if selected_category["is_active"] == 1 else 1
        )

        submitted_edit = st.form_submit_button("Update Kategori")

        if submitted_edit:
            edit_name_clean = edit_name.strip()
            edit_active_value = 1 if edit_status == "Aktif" else 0

            if edit_name_clean == "":
                st.error("Nama kategori tidak boleh kosong.")
            elif food_category_name_exists(edit_name_clean, exclude_id=selected_category["id"]):
                st.error("Nama kategori sudah digunakan oleh data lain.")
            else:
                update_food_category(
                    category_id=selected_category["id"],
                    category_name=edit_name_clean,
                    is_active=edit_active_value,
                    updated_by=st.session_state.user_id
                )
                st.success("Kategori berhasil diupdate.")
                st.rerun()

st.divider()

st.subheader("Daftar Kategori Menu")

df = pd.DataFrame(get_food_categories(include_inactive=True))

if df.empty:
    st.info("Belum ada data kategori.")
else:
    df["Status"] = df["is_active"].apply(lambda x: "Aktif" if x == 1 else "Nonaktif")

    df_display = df[
        ["category_name", "Status", "created_at", "updated_at"]
    ].rename(
        columns={
            "category_name": "Nama Kategori",
            "created_at": "Dibuat Pada",
            "updated_at": "Diupdate Pada",
        }
    )

    st.dataframe(df_display, use_container_width=True)