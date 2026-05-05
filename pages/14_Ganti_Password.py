import streamlit as st

from auth import init_session, require_login, show_user_sidebar
from database import (
    setup_database,
    change_own_password,
)


st.set_page_config(
    page_title="Ganti Password",
    page_icon="🔐",
    layout="wide",
)

setup_database()
init_session()
require_login()
show_user_sidebar()

st.title("🔐 Ganti Password")

st.write(
    """
    Gunakan halaman ini untuk mengganti password akun kamu sendiri.
    """
)

st.warning(
    """
    Setelah password diganti, gunakan password baru saat login berikutnya.
    Jangan bagikan password kepada orang lain.
    """
)

st.divider()

st.write(f"Username: **{st.session_state.username}**")
st.write(f"Role: `{st.session_state.role}`")

st.divider()

with st.form("form_ganti_password"):
    old_password = st.text_input(
        "Password Lama",
        type="password"
    )

    new_password = st.text_input(
        "Password Baru",
        type="password",
        help="Minimal 6 karakter"
    )

    confirm_password = st.text_input(
        "Konfirmasi Password Baru",
        type="password"
    )

    submitted = st.form_submit_button("Ganti Password")

    if submitted:
        result = change_own_password(
            user_id=st.session_state.user_id,
            old_password=old_password,
            new_password=new_password,
            confirm_password=confirm_password,
        )

        if result["success"]:
            st.success(result["message"])
        else:
            st.error(result["message"])