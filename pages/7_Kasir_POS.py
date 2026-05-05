import streamlit as st
import pandas as pd

from auth import init_session, require_roles, show_user_sidebar
from database import (
    setup_database,
    get_pos_active_employees,
    get_active_merchant,
    get_pos_food_categories,
    get_pos_food_items,
    get_employee_voucher_balance,
    create_pos_voucher_transaction,
    get_today_pos_transactions,
    get_setting_bool,
)
from utils import (
    format_rupiah,
    get_current_period_month,
    is_valid_period_month,
)


st.set_page_config(
    page_title="Kasir POS",
    page_icon="🧾",
    layout="wide",
)


setup_database()
init_session()
require_roles(["admin", "kasir"])
show_user_sidebar()


def init_cart():
    """
    Menyiapkan keranjang POS di session_state.
    """
    if "pos_cart" not in st.session_state:
        st.session_state.pos_cart = []


def clear_cart():
    """
    Mengosongkan keranjang POS.
    """
    st.session_state.pos_cart = []


def add_to_cart(food_item_id, item_name, price, quantity):
    """
    Menambahkan item ke keranjang.
    Jika item yang sama sudah ada, quantity akan ditambah.
    """
    quantity = int(quantity)
    price = int(price)

    if quantity <= 0:
        return

    for item in st.session_state.pos_cart:
        if item["food_item_id"] == food_item_id and item["price"] == price:
            item["quantity"] += quantity
            item["subtotal"] = item["quantity"] * item["price"]
            return

    st.session_state.pos_cart.append(
        {
            "food_item_id": food_item_id,
            "item_name": item_name,
            "price": price,
            "quantity": quantity,
            "subtotal": price * quantity,
        }
    )


def remove_cart_item(index):
    """
    Menghapus item dari keranjang berdasarkan index.
    """
    if 0 <= index < len(st.session_state.pos_cart):
        st.session_state.pos_cart.pop(index)


def calculate_cart_total():
    """
    Menghitung total belanja dari keranjang.
    """
    total = 0

    for item in st.session_state.pos_cart:
        total += int(item["subtotal"])

    return total


init_cart()


st.title("🧾 Kasir Mini POS")

st.write(
    """
    Halaman ini digunakan kasir untuk mencatat transaksi penggunaan voucher.
    Kasir memilih pegawai, memilih item makanan/minuman, lalu sistem menghitung total otomatis.
    """
)

st.divider()


# =========================================================
# PERIODE DAN SETTING
# =========================================================
period_month = st.text_input(
    "Periode Voucher",
    value=get_current_period_month(),
    help="Format wajib YYYY-MM. Contoh: 2026-05",
)

period_month_clean = period_month.strip()
allow_split_payment = get_setting_bool("allow_split_payment", False)

if not is_valid_period_month(period_month_clean):
    st.error("Format periode salah. Gunakan format YYYY-MM.")
    st.stop()


# =========================================================
# MERCHANT
# =========================================================
merchant = get_active_merchant()

if merchant is None:
    st.error("Belum ada merchant aktif.")
    st.stop()


# =========================================================
# PILIH PEGAWAI
# =========================================================
employees = get_pos_active_employees()

if len(employees) == 0:
    st.error("Belum ada pegawai aktif.")
    st.stop()

employee_options = {}

for employee in employees:
    label = (
        f'{employee["employee_code"]} - '
        f'{employee["full_name"]} - '
        f'{employee["division_name"] or "-"}'
    )
    employee_options[label] = employee

selected_employee_label = st.selectbox(
    "Pilih Pegawai",
    options=list(employee_options.keys()),
)

selected_employee = employee_options[selected_employee_label]
selected_employee_id = selected_employee["id"]

balance_info = get_employee_voucher_balance(
    employee_id=selected_employee_id,
    period_month=period_month_clean,
)


# =========================================================
# INFORMASI SALDO
# =========================================================
st.subheader("Informasi Pegawai dan Saldo")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Pegawai", selected_employee["full_name"])

with col2:
    st.metric("Alokasi", format_rupiah(balance_info["allocation"]))

with col3:
    st.metric("Terpakai", format_rupiah(balance_info["used"]))

with col4:
    st.metric("Sisa Saldo", format_rupiah(balance_info["balance"]))

if not balance_info["has_allocation"]:
    st.warning(
        "Pegawai ini belum memiliki alokasi voucher untuk periode ini. "
        "Silakan admin melakukan generate voucher dari halaman 6_Generate_Voucher."
    )

if allow_split_payment:
    st.info(
        """
        Split payment aktif.
        Jika total belanja melebihi saldo voucher, kekurangannya akan dicatat sebagai tunai.
        """
    )
else:
    st.info(
        """
        Split payment nonaktif.
        Total belanja harus lebih kecil atau sama dengan sisa saldo voucher.
        """
    )

st.divider()


# =========================================================
# LAYOUT POS
# =========================================================
left_col, right_col = st.columns([2, 1])


# =========================================================
# PILIH MENU
# =========================================================
with left_col:
    st.subheader("Pilih Menu")

    categories = get_pos_food_categories()

    if len(categories) == 0:
        st.warning("Belum ada kategori menu aktif.")
    else:
        category_options = {
            category["category_name"]: category["id"]
            for category in categories
        }

        selected_category_name = st.selectbox(
            "Filter Kategori",
            options=list(category_options.keys()),
        )

        selected_category_id = category_options[selected_category_name]

        food_items = get_pos_food_items(category_id=selected_category_id)

        if len(food_items) == 0:
            st.info("Belum ada menu aktif pada kategori ini.")
        else:
            for food in food_items:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])

                    with c1:
                        st.write(f"**{food['item_name']}**")
                        st.caption(food["category_name"])

                    with c2:
                        st.write(format_rupiah(food["price"]))

                    with c3:
                        qty = st.number_input(
                            "Qty",
                            min_value=1,
                            max_value=99,
                            value=1,
                            step=1,
                            key=f"qty_{food['id']}",
                        )

                    with c4:
                        if st.button("Tambah", key=f"add_{food['id']}"):
                            add_to_cart(
                                food_item_id=food["id"],
                                item_name=food["item_name"],
                                price=food["price"],
                                quantity=qty,
                            )
                            st.rerun()

    st.divider()

    # =====================================================
    # ITEM MANUAL
    # =====================================================
    st.subheader("Item Manual / Lain-lain")

    st.caption(
        "Gunakan hanya jika ada item yang belum terdaftar di master menu."
    )

    with st.form("form_item_manual"):
        manual_name = st.text_input(
            "Nama Item Manual",
            value="Item Manual",
            placeholder="Contoh: Tambahan lauk",
        )

        manual_price = st.number_input(
            "Harga Manual",
            min_value=0,
            step=500,
            value=0,
        )

        manual_qty = st.number_input(
            "Qty Manual",
            min_value=1,
            max_value=99,
            step=1,
            value=1,
        )

        submitted_manual = st.form_submit_button("Tambah Item Manual")

        if submitted_manual:
            manual_name_clean = manual_name.strip()

            if manual_name_clean == "":
                st.error("Nama item manual tidak boleh kosong.")
            elif manual_price <= 0:
                st.error("Harga manual harus lebih dari 0.")
            else:
                add_to_cart(
                    food_item_id=None,
                    item_name=manual_name_clean,
                    price=int(manual_price),
                    quantity=int(manual_qty),
                )
                st.success("Item manual ditambahkan ke keranjang.")
                st.rerun()


# =========================================================
# KERANJANG
# =========================================================
with right_col:
    st.subheader("Keranjang")

    if len(st.session_state.pos_cart) == 0:
        st.info("Keranjang masih kosong.")
    else:
        for index, item in enumerate(st.session_state.pos_cart):
            with st.container(border=True):
                st.write(f"**{item['item_name']}**")
                st.caption(
                    f"{item['quantity']} x {format_rupiah(item['price'])}"
                )
                st.write(f"Subtotal: **{format_rupiah(item['subtotal'])}**")

                if st.button("Hapus", key=f"remove_{index}"):
                    remove_cart_item(index)
                    st.rerun()

        cart_total = calculate_cart_total()
        current_balance = int(balance_info["balance"])

        if allow_split_payment:
            voucher_amount_preview = min(cart_total, current_balance)
            cash_amount_preview = max(cart_total - current_balance, 0)
        else:
            voucher_amount_preview = cart_total
            cash_amount_preview = 0

        remaining_after_transaction = current_balance - voucher_amount_preview

        st.divider()

        st.metric("Total Belanja", format_rupiah(cart_total))
        st.metric("Dibayar Voucher", format_rupiah(voucher_amount_preview))
        st.metric("Dibayar Tunai", format_rupiah(cash_amount_preview))
        st.metric(
            "Sisa Saldo Setelah Transaksi",
            format_rupiah(remaining_after_transaction),
        )

        if not balance_info["has_allocation"]:
            st.warning("Pegawai belum memiliki alokasi voucher.")
        elif current_balance <= 0:
            st.error("Saldo voucher pegawai sudah habis.")
        elif not allow_split_payment and cart_total > current_balance:
            st.error(
                "Saldo voucher tidak cukup. "
                "Kurangi item atau aktifkan split payment di Setting Aplikasi."
            )
        elif allow_split_payment and cash_amount_preview > 0:
            st.warning(
                f"Total belanja melebihi saldo. "
                f"{format_rupiah(cash_amount_preview)} akan dicatat sebagai pembayaran tunai."
            )
        else:
            st.success("Saldo cukup untuk transaksi ini.")

        notes = st.text_area(
            "Catatan Transaksi",
            placeholder="Contoh: makan siang",
        )

        col_save, col_clear = st.columns(2)

        with col_save:
            if st.button("Simpan Transaksi", type="primary"):
                result = create_pos_voucher_transaction(
                    employee_id=selected_employee_id,
                    merchant_id=merchant["id"],
                    period_month=period_month_clean,
                    cart_items=st.session_state.pos_cart,
                    notes=notes.strip(),
                    created_by=st.session_state.user_id,
                )

                if result["success"]:
                    st.success(result["message"])

                    if result.get("cash_amount", 0) > 0:
                        st.warning(
                            f"Ada pembayaran tunai sebesar "
                            f"{format_rupiah(result['cash_amount'])}."
                        )

                    clear_cart()
                    st.rerun()
                else:
                    st.error(result["message"])

        with col_clear:
            if st.button("Kosongkan"):
                clear_cart()
                st.rerun()


st.divider()


# =========================================================
# TRANSAKSI HARI INI
# =========================================================
with st.expander("Transaksi Hari Ini"):
    transactions = get_today_pos_transactions()

    df = pd.DataFrame(transactions)

    if df.empty:
        st.info("Belum ada transaksi hari ini.")
    else:
        df["Total"] = df["total_amount"].apply(format_rupiah)
        df["Voucher"] = df["voucher_amount"].apply(format_rupiah)
        df["Tunai"] = df["cash_amount"].apply(format_rupiah)
        df["Status"] = df["voided_at"].apply(
            lambda value: "Valid" if pd.isna(value) or value is None else "Void"
        )

        df_display = df[
            [
                "created_at",
                "period_month",
                "employee_code",
                "full_name",
                "merchant_name",
                "Total",
                "Voucher",
                "Tunai",
                "Status",
                "notes",
            ]
        ].rename(
            columns={
                "created_at": "Waktu",
                "period_month": "Periode",
                "employee_code": "Kode",
                "full_name": "Pegawai",
                "merchant_name": "Merchant",
                "notes": "Catatan",
            }
        )

        st.dataframe(df_display, use_container_width=True)