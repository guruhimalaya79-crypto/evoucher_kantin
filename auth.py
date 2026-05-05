import bcrypt
import streamlit as st

from database import (
    get_user_by_username,
    get_user_by_id,
    update_last_login,
    insert_audit_log,
)


def verify_password(plain_password, password_hash):
    """
    Mengecek password input dengan password hash.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except Exception:
        return False


def init_session():
    """
    Menyiapkan session state Streamlit.
    """
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False

    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    if "username" not in st.session_state:
        st.session_state.username = None

    if "role" not in st.session_state:
        st.session_state.role = None

    if "employee_id" not in st.session_state:
        st.session_state.employee_id = None


def login_user(username, password):
    """
    Proses login user.
    """
    username_clean = username.strip()

    if username_clean == "" or password == "":
        return {
            "success": False,
            "message": "Username dan password wajib diisi."
        }

    user = get_user_by_username(username_clean)

    if user is None:
        return {
            "success": False,
            "message": "Username atau password salah."
        }

    if user["is_active"] != 1:
        return {
            "success": False,
            "message": "User tidak aktif. Hubungi admin."
        }

    password_valid = verify_password(password, user["password_hash"])

    if not password_valid:
        return {
            "success": False,
            "message": "Username atau password salah."
        }

    st.session_state.is_logged_in = True
    st.session_state.user_id = user["id"]
    st.session_state.username = user["username"]
    st.session_state.role = user["role"]
    st.session_state.employee_id = user["employee_id"]

    update_last_login(user["id"])
    insert_audit_log(
        user_id=user["id"],
        action="LOGIN",
        table_name="users",
        record_id=user["id"],
        description=f"User {user['username']} login sebagai {user['role']}"
    )

    return {
        "success": True,
        "message": "Login berhasil."
    }


def logout_user():
    """
    Logout user.
    """
    user_id = st.session_state.get("user_id")
    username = st.session_state.get("username")

    if user_id is not None:
        insert_audit_log(
            user_id=user_id,
            action="LOGOUT",
            table_name="users",
            record_id=user_id,
            description=f"User {username} logout"
        )

    st.session_state.is_logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.employee_id = None


def get_current_user():
    """
    Mengambil user yang sedang login.
    """
    if not st.session_state.get("is_logged_in"):
        return None

    user_id = st.session_state.get("user_id")

    if user_id is None:
        return None

    return get_user_by_id(user_id)


def require_login():
    """
    Mengecek apakah user sudah login.
    """
    if not st.session_state.get("is_logged_in"):
        st.warning("Silakan login terlebih dahulu.")
        st.stop()


def require_roles(allowed_roles):
    """
    Membatasi halaman berdasarkan role.
    Contoh:
    require_roles(["admin"])
    require_roles(["admin", "kasir"])
    """
    require_login()

    current_role = st.session_state.get("role")

    if current_role not in allowed_roles:
        st.error("Anda tidak memiliki akses ke halaman ini.")
        st.stop()


def show_user_sidebar():
    """
    Menampilkan informasi user dan panduan menu di sidebar.
    """
    if not st.session_state.get("is_logged_in"):
        return

    role = st.session_state.get("role")

    st.sidebar.divider()
    st.sidebar.write("Login sebagai:")
    st.sidebar.write(f"**{st.session_state.username}**")
    st.sidebar.write(f"Role: `{role}`")

    st.sidebar.divider()
    st.sidebar.write("Menu yang disarankan:")

    if role == "admin":
        st.sidebar.markdown(
            """
            - 📊 Admin Dashboard
            - 🏢 Master Divisi
            - 👥 Master Pegawai
            - 📥 Import Pegawai
            - 🍱 Master Kategori Menu
            - 🍛 Master Menu Makanan
            - 🎫 Generate Voucher
            - 🧾 Kasir POS
            - 👤 Saldo Pegawai
            - 🚫 Void Transaksi
            - 📑 Laporan
            - 💾 Backup Database
            - ⚙️ Setting Aplikasi
            - 👤 Manajemen User
            - 🔐 Ganti Password
            - 📘 Panduan Penggunaan
            """
        )

    elif role == "kasir":
        st.sidebar.markdown(
            """
            - 🧾 Kasir POS
            - 👤 Saldo Pegawai
            - 🔐 Ganti Password
            - 📘 Panduan Penggunaan
            """
        )

    elif role == "pegawai":
        st.sidebar.markdown(
            """
            - 👤 Saldo Pegawai
            - 🔐 Ganti Password
            - 📘 Panduan Penggunaan
            """
        )

    st.sidebar.divider()

    if st.sidebar.button("Logout"):
        logout_user()
        st.rerun()