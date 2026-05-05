import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    import_food_items_from_dataframe,
    get_food_items_with_category,
)
from reports import build_food_item_import_template
from utils import format_rupiah


st.set_page_config(
    page_title="Import Menu Makanan",
    page_icon="📥",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("📥 Import Menu Makanan dari Excel")

st.write(
    """
    Halaman ini digunakan admin untuk import daftar menu makanan/minuman
    dalam jumlah banyak agar tidak perlu input manual satu per satu.
    """
)

st.warning(
    """
    Gunakan template Excel yang disediakan agar format kolom sesuai.
    Jika menu dengan nama yang sama sudah ada pada kategori yang sama,
    data akan dilewati dan tidak dibuat dobel.
    """
)

st.divider()

# =========================================================
# DOWNLOAD TEMPLATE
# =========================================================
st.subheader("1. Download Template Excel")

template_file = build_food_item_import_template()

st.download_button(
    label="Download Template Import Menu Makanan",
    data=template_file,
    file_name="template_import_menu_makanan.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.caption(
    """
    Isi data menu pada sheet `template_menu`.
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
        | category_name | Ya | Nama kategori menu |
        | item_name | Ya | Nama makanan/minuman |
        | price | Ya | Harga menu dalam angka |
        | is_active | Tidak | 1 = aktif, 0 = nonaktif |

        Contoh:

        | category_name | item_name | price | is_active |
        |---|---|---:|---:|
        | Makanan Berat | Nasi Ayam | 15000 | 1 |
        | Minuman | Es Teh | 5000 | 1 |
        | Snack | Gorengan | 3000 | 1 |
        """
    )

st.divider()

# =========================================================
# UPLOAD FILE
# =========================================================
st.subheader("2. Upload File Excel Menu")

uploaded_file = st.file_uploader(
    "Upload file Excel",
    type=["xlsx"]
)

if uploaded_file is not None:
    try:
        df_upload = pd.read_excel(uploaded_file, sheet_name="template_menu")
    except Exception:
        try:
            df_upload = pd.read_excel(uploaded_file)
        except Exception as error:
            st.error(f"Gagal membaca file Excel: {error}")
            st.stop()

    st.write("Preview data yang akan diimport:")

    st.dataframe(df_upload.head(30), use_container_width=True)

    st.caption(f"Total baris terbaca: {len(df_upload)}")

    st.divider()

    confirm_import = st.checkbox(
        "Saya sudah mengecek preview data dan ingin import menu makanan."
    )

    if st.button("Import Menu Makanan", type="primary"):
        if not confirm_import:
            st.error("Centang konfirmasi terlebih dahulu.")
        else:
            result = import_food_items_from_dataframe(
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

                st.info("Jika import berhasil, cek daftar menu di bagian bawah halaman.")
            else:
                st.error(result["message"])

st.divider()

# =========================================================
# DAFTAR MENU
# =========================================================
st.subheader("Daftar Menu Saat Ini")

items = get_food_items_with_category(include_inactive=True)
df_items = pd.DataFrame(items)

if df_items.empty:
    st.info("Belum ada data menu makanan.")
else:
    df_items["Harga"] = df_items["price"].apply(format_rupiah)
    df_items["Status"] = df_items["is_active"].apply(
        lambda value: "Aktif" if value == 1 else "Nonaktif"
    )

    df_display = df_items[
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