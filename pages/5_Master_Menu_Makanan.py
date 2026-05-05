import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    get_food_categories,
    get_food_items_with_category,
    food_item_exists,
    add_food_item,
    update_food_item,
)
from utils import format_rupiah


st.set_page_config(
    page_title="Master Menu Makanan",
    page_icon="🍛",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("🍛 Master Menu Makanan")

st.write("Kelola daftar menu makanan/minuman yang nanti dipilih kasir di halaman POS.")

active_categories = get_food_categories(include_inactive=False)

if len(active_categories) == 0:
    st.warning("Belum ada kategori aktif. Tambahkan kategori menu terlebih dahulu.")
    st.stop()

category_options = {
    c["category_name"]: c["id"]
    for c in active_categories
}

st.divider()

st.subheader("Tambah Menu Makanan")

with st.form("form_tambah_menu"):
    selected_category_name = st.selectbox("Kategori", list(category_options.keys()))
    item_name = st.text_input("Nama Menu", placeholder="Contoh: Nasi Campur")
    price = st.number_input("Harga", min_value=0, step=500, value=10000)
    status = st.selectbox("Status", ["Aktif", "Nonaktif"])

    submitted = st.form_submit_button("Simpan Menu")

    if submitted:
        category_id = category_options[selected_category_name]
        item_name_clean = item_name.strip()
        is_active = 1 if status == "Aktif" else 0

        if item_name_clean == "":
            st.error("Nama menu tidak boleh kosong.")
        elif price < 0:
            st.error("Harga tidak boleh negatif.")
        elif food_item_exists(category_id, item_name_clean):
            st.error("Menu dengan nama tersebut sudah ada di kategori yang sama.")
        else:
            add_food_item(
                category_id=category_id,
                item_name=item_name_clean,
                price=int(price),
                is_active=is_active,
                created_by=st.session_state.user_id,
            )
            st.success("Menu berhasil ditambahkan.")
            st.rerun()

st.divider()

st.subheader("Edit Menu Makanan")

items = get_food_items_with_category(include_inactive=True)

if len(items) == 0:
    st.warning("Belum ada data menu makanan.")
else:
    item_options = {
        f'{i["category_name"]} - {i["item_name"]} - {format_rupiah(i["price"])}': i
        for i in items
    }

    selected_item_label = st.selectbox("Pilih Menu", list(item_options.keys()))
    selected_item = item_options[selected_item_label]

    category_names = list(category_options.keys())

    current_category_name = selected_item["category_name"]
    if current_category_name not in category_names:
        current_category_index = 0
    else:
        current_category_index = category_names.index(current_category_name)

    with st.form("form_edit_menu"):
        edit_category_name = st.selectbox(
            "Kategori",
            category_names,
            index=current_category_index
        )

        edit_item_name = st.text_input(
            "Nama Menu",
            value=selected_item["item_name"]
        )

        edit_price = st.number_input(
            "Harga",
            min_value=0,
            step=500,
            value=int(selected_item["price"])
        )

        edit_status = st.selectbox(
            "Status",
            ["Aktif", "Nonaktif"],
            index=0 if selected_item["is_active"] == 1 else 1
        )

        submitted_edit = st.form_submit_button("Update Menu")

        if submitted_edit:
            edit_category_id = category_options[edit_category_name]
            edit_item_name_clean = edit_item_name.strip()
            edit_is_active = 1 if edit_status == "Aktif" else 0

            if edit_item_name_clean == "":
                st.error("Nama menu tidak boleh kosong.")
            elif food_item_exists(
                edit_category_id,
                edit_item_name_clean,
                exclude_id=selected_item["id"]
            ):
                st.error("Menu dengan nama tersebut sudah ada di kategori yang sama.")
            else:
                update_food_item(
                    item_id=selected_item["id"],
                    category_id=edit_category_id,
                    item_name=edit_item_name_clean,
                    price=int(edit_price),
                    is_active=edit_is_active,
                    updated_by=st.session_state.user_id,
                )
                st.success("Menu berhasil diupdate.")
                st.rerun()

st.divider()

st.subheader("Daftar Menu Makanan")

df = pd.DataFrame(get_food_items_with_category(include_inactive=True))

if df.empty:
    st.info("Belum ada data menu makanan.")
else:
    df["Harga"] = df["price"].apply(format_rupiah)
    df["Status"] = df["is_active"].apply(lambda x: "Aktif" if x == 1 else "Nonaktif")

    df_display = df[
        [
            "category_name",
            "item_name",
            "Harga",
            "Status",
            "created_at",
            "updated_at",
        ]
    ].rename(
        columns={
            "category_name": "Kategori",
            "item_name": "Nama Menu",
            "created_at": "Dibuat Pada",
            "updated_at": "Diupdate Pada",
        }
    )

    st.dataframe(df_display, use_container_width=True)