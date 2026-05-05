import streamlit as st


def show_role_menu():
    """
    Menampilkan menu sidebar sesuai role user.
    Menu ini menggantikan sidebar otomatis bawaan Streamlit.
    """
    if not st.session_state.get("is_logged_in"):
        return

    role = st.session_state.get("role")

    st.sidebar.divider()
    st.sidebar.title("🍽️ E-Voucher")
    st.sidebar.caption("Menu Aplikasi")

    if role == "admin":
        show_admin_menu()

    elif role == "kasir":
        show_kasir_menu()

    elif role == "pegawai":
        show_pegawai_menu()

    else:
        st.sidebar.warning("Role tidak dikenali.")


def show_admin_menu():
    """
    Menu lengkap untuk admin.
    """
    with st.sidebar.expander("🏠 Utama", expanded=True):
        st.page_link("app.py", label="Beranda", icon="🏠")
        st.page_link("pages/15_Panduan_Penggunaan.py", label="Panduan Penggunaan", icon="📘")

    with st.sidebar.expander("📊 Dashboard & Laporan", expanded=True):
        st.page_link("pages/1_Admin_Dashboard.py", label="Admin Dashboard", icon="📊")
        st.page_link("pages/10_Laporan.py", label="Laporan", icon="📑")

    with st.sidebar.expander("🗂️ Master Pegawai", expanded=False):
        st.page_link("pages/2_Master_Divisi.py", label="Master Divisi", icon="🏢")
        st.page_link("pages/3_Master_Pegawai.py", label="Master Pegawai", icon="👥")
        st.page_link("pages/16_Import_Pegawai.py", label="Import Pegawai", icon="📥")
        st.page_link("pages/17_Generate_User_Pegawai.py", label="Generate User Pegawai", icon="🪪")

    with st.sidebar.expander("🍱 Master Menu Kantin", expanded=False):
        st.page_link("pages/4_Master_Kategori_Menu.py", label="Master Kategori Menu", icon="🍱")
        st.page_link("pages/5_Master_Menu_Makanan.py", label="Master Menu Makanan", icon="🍛")
        st.page_link("pages/18_Import_Menu_Makanan.py", label="Import Menu Makanan", icon="📥")

    with st.sidebar.expander("🎫 Voucher & Transaksi", expanded=False):
        st.page_link("pages/6_Generate_Voucher.py", label="Generate Voucher", icon="🎫")
        st.page_link("pages/7_Kasir_POS.py", label="Kasir POS", icon="🧾")
        st.page_link("pages/8_Saldo_Pegawai.py", label="Saldo Pegawai", icon="👤")
        st.page_link("pages/9_Void_Transaksi.py", label="Void Transaksi", icon="🚫")

    with st.sidebar.expander("⚙️ Sistem", expanded=False):
        st.page_link("pages/12_Setting_Aplikasi.py", label="Setting Aplikasi", icon="⚙️")
        st.page_link("pages/13_Manajemen_User.py", label="Manajemen User", icon="👤")
        st.page_link("pages/14_Ganti_Password.py", label="Ganti Password", icon="🔐")
        st.page_link("pages/11_Backup_Database.py", label="Backup Database", icon="💾")
        st.page_link("pages/19_Reset_Database_Demo.py", label="Reset Database Demo", icon="♻️")


def show_kasir_menu():
    """
    Menu khusus kasir.
    Kasir tidak melihat menu admin.
    """
    with st.sidebar.expander("🏠 Utama", expanded=True):
        st.page_link("app.py", label="Beranda", icon="🏠")
        st.page_link("pages/15_Panduan_Penggunaan.py", label="Panduan Penggunaan", icon="📘")

    with st.sidebar.expander("🧾 Operasional Kasir", expanded=True):
        st.page_link("pages/7_Kasir_POS.py", label="Kasir POS", icon="🧾")
        st.page_link("pages/8_Saldo_Pegawai.py", label="Cek Saldo Pegawai", icon="👤")

    with st.sidebar.expander("⚙️ Akun", expanded=True):
        st.page_link("pages/14_Ganti_Password.py", label="Ganti Password", icon="🔐")


def show_pegawai_menu():
    """
    Menu khusus pegawai.
    Pegawai hanya melihat menu yang berhubungan dengan dirinya.
    """
    with st.sidebar.expander("🏠 Utama", expanded=True):
        st.page_link("app.py", label="Beranda", icon="🏠")
        st.page_link("pages/15_Panduan_Penggunaan.py", label="Panduan Penggunaan", icon="📘")

    with st.sidebar.expander("👤 Pegawai", expanded=True):
        st.page_link("pages/8_Saldo_Pegawai.py", label="Saldo Saya", icon="👤")

    with st.sidebar.expander("⚙️ Akun", expanded=True):
        st.page_link("pages/14_Ganti_Password.py", label="Ganti Password", icon="🔐")