import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    DB_PATH,
    create_database_backup,
    get_backup_files,
)


st.set_page_config(
    page_title="Backup Database",
    page_icon="💾",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("💾 Backup Database")

st.write(
    """
    Halaman ini digunakan admin untuk membuat backup file database SQLite.
    Backup sangat penting karena semua data voucher, transaksi, pegawai, dan laporan
    tersimpan di file database lokal.
    """
)

st.warning(
    """
    Rekomendasi:
    - Backup setiap akhir hari.
    - Backup sebelum update kode aplikasi.
    - Backup setelah closing laporan akhir bulan.
    - Simpan salinan backup di flashdisk, Google Drive, OneDrive, atau server kantor.
    """
)

st.divider()

st.subheader("Informasi Database")

st.code(str(DB_PATH))

if DB_PATH.exists():
    size_kb = round(DB_PATH.stat().st_size / 1024, 2)
    st.metric("Ukuran Database", f"{size_kb} KB")
else:
    st.error("File database belum ditemukan.")

st.divider()

st.subheader("Buat Backup Baru")

if st.button("Buat Backup Database Sekarang", type="primary"):
    result = create_database_backup()

    if result["success"]:
        st.success(result["message"])
        st.code(str(result["backup_path"]))
        st.rerun()
    else:
        st.error(result["message"])

st.divider()

st.subheader("Daftar File Backup")

backup_files = get_backup_files()
df = pd.DataFrame(backup_files)

if df.empty:
    st.info("Belum ada file backup.")
else:
    df_display = df[
        [
            "filename",
            "path",
            "size_kb",
        ]
    ].rename(
        columns={
            "filename": "Nama File",
            "path": "Lokasi",
            "size_kb": "Ukuran KB",
        }
    )

    st.dataframe(df_display, use_container_width=True)

st.divider()

st.subheader("Cara Restore Manual")

st.markdown(
    """
    Jika suatu hari database rusak dan ingin mengembalikan dari backup:

    1. Tutup aplikasi Streamlit.
    2. Buka folder project.
    3. Masuk ke folder `data/backups`.
    4. Pilih file backup yang ingin dipakai.
    5. Copy file backup tersebut.
    6. Rename menjadi `evoucher.db`.
    7. Letakkan di folder `data/`.
    8. Jalankan ulang aplikasi.

    Contoh struktur:

    ```text
    evoucher-kantin/
    └── data/
        ├── evoucher.db
        └── backups/
            ├── evoucher_backup_2026-05-05T09-30-00.db
            └── evoucher_backup_2026-05-06T17-00-00.db
    ```
    """
)