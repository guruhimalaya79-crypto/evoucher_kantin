import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    get_users_with_employee,
    get_employees_with_division,
    create_user,
    update_user_basic,
    reset_user_password,
)


st.set_page_config(
    page_title="Manajemen User",
    page_icon="👤",
    layout="wide",
)

setup_database()
init_session()
require_roles(["admin"])
show_user_sidebar()

st.title("👤 Manajemen User")

st.write(
    """
    Halaman ini digunakan admin untuk membuat user, mengatur role,
    menghubungkan akun pegawai, reset password, dan aktif/nonaktif user.
    """
)

st.warning(
    """
    Catatan:
    Untuk keamanan, password tidak pernah ditampilkan.
    Admin hanya bisa reset password, bukan melihat password lama.
    """
)

st.divider()

# =========================================================
# TAMBAH USER
# =========================================================
st.subheader("Tambah User Baru")

employees = get_employees_with_division(include_inactive=False)

employee_options = {
    f'{e["employee_code"]} - {e["full_name"]} - {e["division_name"] or "-"}': e["id"]
    for e in employees
}

with st.form("form_tambah_user"):
    username = st.text_input(
        "Username",
        placeholder="Contoh: emp007 atau kasir2"
    )

    password = st.text_input(
        "Password Awal",
        type="password",
        placeholder="Minimal 6 karakter"
    )

    role = st.selectbox(
        "Role",
        options=["admin", "kasir", "pegawai"]
    )

    selected_employee_id = None

    if role == "pegawai":
        if len(employee_options) == 0:
            st.warning("Belum ada pegawai aktif untuk dihubungkan.")
        else:
            selected_employee_label = st.selectbox(
                "Hubungkan ke Pegawai",
                options=list(employee_options.keys())
            )
            selected_employee_id = employee_options[selected_employee_label]

    status = st.selectbox(
        "Status User",
        options=["Aktif", "Nonaktif"]
    )

    submitted = st.form_submit_button("Buat User")

    if submitted:
        is_active = 1 if status == "Aktif" else 0

        result = create_user(
            username=username,
            password=password,
            role=role,
            employee_id=selected_employee_id,
            is_active=is_active,
            created_by=st.session_state.user_id,
        )

        if result["success"]:
            st.success(result["message"])
            st.rerun()
        else:
            st.error(result["message"])

st.divider()

# =========================================================
# EDIT USER
# =========================================================
st.subheader("Edit User")

users = get_users_with_employee()

if len(users) == 0:
    st.info("Belum ada user.")
else:
    user_options = {
        f'{u["username"]} - {u["role"]} - {"Aktif" if u["is_active"] == 1 else "Nonaktif"}': u
        for u in users
    }

    selected_user_label = st.selectbox(
        "Pilih User",
        options=list(user_options.keys())
    )

    selected_user = user_options[selected_user_label]

    with st.form("form_edit_user"):
        edit_username = st.text_input(
            "Username",
            value=selected_user["username"]
        )

        edit_role = st.selectbox(
            "Role",
            options=["admin", "kasir", "pegawai"],
            index=["admin", "kasir", "pegawai"].index(selected_user["role"])
        )

        edit_employee_id = selected_user["employee_id"]

        if edit_role == "pegawai":
            if len(employee_options) == 0:
                st.warning("Belum ada pegawai aktif.")
            else:
                employee_labels = list(employee_options.keys())

                current_label = None
                for label, emp_id in employee_options.items():
                    if emp_id == selected_user["employee_id"]:
                        current_label = label
                        break

                if current_label is None:
                    employee_index = 0
                else:
                    employee_index = employee_labels.index(current_label)

                edit_employee_label = st.selectbox(
                    "Hubungkan ke Pegawai",
                    options=employee_labels,
                    index=employee_index
                )
                edit_employee_id = employee_options[edit_employee_label]

        else:
            edit_employee_id = None
            st.info("Role admin/kasir tidak perlu dihubungkan ke data pegawai.")

        edit_status = st.selectbox(
            "Status",
            options=["Aktif", "Nonaktif"],
            index=0 if selected_user["is_active"] == 1 else 1
        )

        submitted_edit = st.form_submit_button("Update User")

        if submitted_edit:
            edit_is_active = 1 if edit_status == "Aktif" else 0

            result = update_user_basic(
                user_id=selected_user["id"],
                username=edit_username,
                role=edit_role,
                employee_id=edit_employee_id,
                is_active=edit_is_active,
                updated_by=st.session_state.user_id,
            )

            if result["success"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])

st.divider()

# =========================================================
# RESET PASSWORD
# =========================================================
st.subheader("Reset Password User")

if len(users) == 0:
    st.info("Belum ada user untuk reset password.")
else:
    reset_user_options = {
        f'{u["username"]} - {u["role"]}': u
        for u in users
    }

    selected_reset_label = st.selectbox(
        "Pilih User untuk Reset Password",
        options=list(reset_user_options.keys())
    )

    selected_reset_user = reset_user_options[selected_reset_label]

    with st.form("form_reset_password"):
        new_password = st.text_input(
            "Password Baru",
            type="password",
            placeholder="Minimal 6 karakter"
        )

        confirm_reset = st.checkbox(
            "Saya yakin ingin reset password user ini."
        )

        submitted_reset = st.form_submit_button("Reset Password")

        if submitted_reset:
            if not confirm_reset:
                st.error("Centang konfirmasi terlebih dahulu.")
            else:
                result = reset_user_password(
                    user_id=selected_reset_user["id"],
                    new_password=new_password,
                    updated_by=st.session_state.user_id,
                )

                if result["success"]:
                    st.success(result["message"])
                else:
                    st.error(result["message"])

st.divider()

# =========================================================
# DAFTAR USER
# =========================================================
st.subheader("Daftar User")

df = pd.DataFrame(get_users_with_employee())

if df.empty:
    st.info("Belum ada user.")
else:
    df["Status"] = df["is_active"].apply(
        lambda value: "Aktif" if value == 1 else "Nonaktif"
    )

    df_display = df[
        [
            "username",
            "role",
            "employee_code",
            "full_name",
            "division_name",
            "Status",
            "created_at",
            "updated_at",
            "last_login_at",
        ]
    ].rename(
        columns={
            "username": "Username",
            "role": "Role",
            "employee_code": "Kode Pegawai",
            "full_name": "Nama Pegawai",
            "division_name": "Divisi",
            "created_at": "Dibuat Pada",
            "updated_at": "Diupdate Pada",
            "last_login_at": "Login Terakhir",
        }
    )

    st.dataframe(df_display, use_container_width=True)