import streamlit as st

from auth import init_session, require_login, show_user_sidebar
from database import setup_database


st.set_page_config(
    page_title="Panduan Penggunaan",
    page_icon="📘",
    layout="wide",
)

setup_database()
init_session()
require_login()
show_user_sidebar()

st.title("📘 Panduan Penggunaan Aplikasi")

st.info(
    """
    Halaman ini berisi panduan singkat penggunaan aplikasi e-voucher kantin.
    Untuk demo online, data yang dimasukkan hanya data uji coba dan bukan transaksi resmi.
    """
)

st.divider()

tab_admin, tab_kasir, tab_pegawai, tab_demo, tab_faq = st.tabs(
    [
        "Admin",
        "Kasir",
        "Pegawai",
        "Demo Online",
        "FAQ",
    ]
)

with tab_admin:
    st.header("Panduan Admin")

    st.subheader("1. Login Admin")

    st.write(
        """
        Admin login menggunakan akun admin yang sudah disediakan.
        Setelah login, admin dapat mengelola data master, generate voucher,
        melihat laporan, export Excel, dan melakukan void transaksi.
        """
    )

    st.subheader("2. Urutan Kerja Admin")

    st.markdown(
        """
        1. Buka **Master Divisi** dan pastikan daftar divisi sudah benar.
        2. Buka **Master Pegawai** dan pastikan pegawai aktif/nonaktif sudah benar.
        3. Buka **Master Kategori Menu** dan cek kategori makanan/minuman.
        4. Buka **Master Menu Makanan** dan cek harga menu.
        5. Buka **Setting Aplikasi** untuk memastikan nominal voucher bulanan.
        6. Buka **Generate Voucher** untuk membuat alokasi voucher bulan berjalan.
        7. Pantau transaksi dari halaman **Laporan**.
        8. Jika ada transaksi salah, buka **Void Transaksi**.
        9. Export laporan akhir bulan dari halaman **Laporan**.
        10. Backup database dari halaman **Backup Database** jika berjalan lokal/LAN.
        """
    )

    st.subheader("3. Generate Voucher Bulanan")

    st.write(
        """
        Generate voucher dilakukan satu kali setiap bulan.
        Sistem hanya memberikan voucher kepada pegawai aktif.
        Jika tombol generate ditekan ulang pada bulan yang sama,
        sistem akan melewati pegawai yang sudah punya alokasi.
        """
    )

    st.warning(
        """
        Sebelum generate voucher, pastikan data pegawai aktif sudah benar.
        Pegawai nonaktif tidak akan mendapat voucher.
        """
    )

    st.subheader("4. Void Transaksi")

    st.write(
        """
        Jika kasir salah input transaksi, transaksi tidak boleh dihapus.
        Admin harus melakukan void transaksi dan mengisi alasan.
        Transaksi void tidak dihitung dalam saldo dan laporan pembayaran pedagang.
        """
    )

with tab_kasir:
    st.header("Panduan Kasir")

    st.subheader("1. Login Kasir")

    st.write(
        """
        Kasir login menggunakan akun kasir.
        Kasir hanya fokus pada halaman **Kasir POS** dan pengecekan saldo pegawai.
        """
    )

    st.subheader("2. Input Transaksi di Kasir POS")

    st.markdown(
        """
        1. Buka halaman **Kasir POS**.
        2. Pilih periode voucher yang benar.
        3. Pilih pegawai.
        4. Cek sisa saldo voucher pegawai.
        5. Pilih kategori makanan.
        6. Klik **Tambah** pada item makanan/minuman.
        7. Cek isi keranjang.
        8. Pastikan total belanja benar.
        9. Klik **Simpan Transaksi**.
        """
    )

    st.subheader("3. Jika Salah Input")

    st.warning(
        """
        Jika salah memilih pegawai, salah memilih item, atau salah transaksi,
        jangan menghapus data manual. Catat ID transaksi dan hubungi admin
        agar transaksi di-void.
        """
    )

    st.subheader("4. Split Payment")

    st.write(
        """
        Jika split payment aktif, belanja yang melebihi saldo voucher
        dapat dicatat sebagian sebagai voucher dan sisanya sebagai tunai.
        Jika split payment nonaktif, transaksi akan ditolak jika total belanja
        melebihi saldo voucher.
        """
    )

with tab_pegawai:
    st.header("Panduan Pegawai")

    st.subheader("1. Login Pegawai")

    st.write(
        """
        Pegawai login menggunakan akun pegawai masing-masing.
        Pegawai hanya dapat melihat saldo dan riwayat transaksi miliknya sendiri.
        """
    )

    st.subheader("2. Cek Saldo Voucher")

    st.markdown(
        """
        1. Buka halaman **Saldo Pegawai**.
        2. Pilih periode bulan.
        3. Lihat alokasi voucher.
        4. Lihat total terpakai.
        5. Lihat sisa saldo.
        6. Cek riwayat transaksi dan detail item makanan.
        """
    )

    st.subheader("3. Jika Saldo Tidak Sesuai")

    st.write(
        """
        Jika saldo terasa tidak sesuai, pegawai dapat melihat riwayat transaksi.
        Jika ada transaksi yang tidak dikenali, hubungi admin atau kasir.
        """
    )

with tab_demo:
    st.header("Panduan Demo Online")

    st.warning(
        """
        Aplikasi yang berjalan di Streamlit Cloud ini hanya untuk demo online.
        Data yang diinput bukan data resmi dan tidak boleh dijadikan dasar pembayaran asli.
        """
    )

    st.subheader("Akun Demo")

    st.markdown(
        """
        **Admin**

        - Username: `admin`
        - Password: `admin123`

        **Kasir**

        - Username: `kasir`
        - Password: `kasir123`

        **Pegawai**

        - Username: `emp001`
        - Password: `emp001123`

        **Pegawai**

        - Username: `emp002`
        - Password: `emp002123`
        """
    )

    st.subheader("Urutan Demo yang Disarankan")

    st.markdown(
        """
        1. Login sebagai **admin**.
        2. Cek Master Divisi, Pegawai, Kategori Menu, dan Menu Makanan.
        3. Buka Setting Aplikasi dan cek nominal voucher.
        4. Buka Generate Voucher dan buat voucher bulan berjalan.
        5. Logout, login sebagai **kasir**.
        6. Buka Kasir POS dan buat transaksi.
        7. Logout, login sebagai **pegawai**.
        8. Buka Saldo Pegawai dan cek saldo.
        9. Login kembali sebagai admin.
        10. Buka Laporan dan lihat pembayaran pedagang.
        11. Coba export Excel.
        """
    )

    st.info(
        """
        Untuk pemakaian resmi, aplikasi disarankan berjalan di jaringan lokal kantor
        atau memakai database server seperti PostgreSQL/Supabase.
        """
    )

with tab_faq:
    st.header("FAQ")

    st.subheader("Apakah sisa saldo bulan lalu masuk ke bulan berikutnya?")

    st.write(
        """
        Tidak. Voucher hanya berlaku untuk bulan berjalan.
        Sisa saldo bulan sebelumnya hangus dan tidak diakumulasikan.
        """
    )

    st.subheader("Apakah transaksi salah boleh dihapus?")

    st.write(
        """
        Tidak disarankan. Transaksi salah harus di-void agar jejak audit tetap ada.
        """
    )

    st.subheader("Apa dasar pembayaran kantor ke pedagang?")

    st.write(
        """
        Dasar pembayaran adalah total voucher valid yang dipakai pegawai,
        yaitu total `voucher_amount` dari transaksi yang tidak void.
        """
    )

    st.subheader("Apakah total belanja sama dengan pembayaran kantor?")

    st.write(
        """
        Belum tentu. Jika split payment aktif, total belanja bisa lebih besar
        daripada voucher yang dibayar kantor. Selisihnya dicatat sebagai tunai.
        """
    )

    st.subheader("Apakah demo online ini aman untuk transaksi resmi?")

    st.write(
        """
        Tidak. Demo online hanya untuk uji coba tampilan dan alur.
        Untuk transaksi resmi, gunakan jaringan lokal kantor atau database server.
        """
    )