# Knowledge File — Sistem E-Voucher Kantin Kantor

## Ringkasan Masalah
Kantor saat ini memberikan voucher fisik Rp75.000 per bulan kepada setiap pegawai. Voucher dicetak di kertas A4 menjadi 15 voucher dengan nilai Rp5.000 per voucher. Voucher dipakai untuk belanja di kantin kantor yang hanya memiliki 1 pedagang. Jika voucher tidak habis pada bulan berjalan, sisa voucher hangus dan tidak dibawa ke bulan berikutnya. Kantor membayar pedagang berdasarkan total voucher fisik yang terkumpul dari transaksi pegawai.

## Tujuan Digitalisasi
Mengubah proses voucher fisik menjadi sistem e-voucher agar:
- Paperless dan ramah lingkungan.
- Mengurangi risiko voucher hilang, rusak, dipalsukan, atau salah hitung.
- Memudahkan pencatatan transaksi.
- Memudahkan perhitungan pembayaran ke pedagang.
- Memiliki dashboard penggunaan harian, bulanan, dan periode tertentu.
- Memiliki laporan pegawai yang sudah/belum memakai voucher.

## Aturan Bisnis Utama
1. Setiap pegawai mendapatkan saldo voucher Rp75.000 per bulan.
2. Voucher hanya berlaku pada bulan berjalan.
3. Sisa saldo hangus di akhir bulan.
4. Tidak ada akumulasi saldo ke bulan berikutnya.
5. Penggunaan voucher dicatat sebagai transaksi.
6. Transaksi tidak boleh melebihi saldo bulan berjalan.
7. Untuk tahap awal hanya ada satu merchant/pedagang.
8. Nilai transaksi sebaiknya kelipatan Rp5.000 agar mirip voucher fisik lama, tetapi sistem boleh dibuat fleksibel.
9. Admin dapat generate alokasi voucher bulanan otomatis.
10. Laporan akhir bulan menunjukkan total yang harus dibayar kantor ke pedagang.

## Peran Pengguna
### Admin
- Kelola data pegawai.
- Generate e-voucher bulanan.
- Lihat dashboard.
- Lihat dan ekspor laporan.
- Koreksi transaksi jika dibutuhkan, dengan catatan audit.

### Kasir/Pedagang
- Mencatat transaksi penggunaan voucher.
- Melihat total transaksi harian/bulanan miliknya.
- Tidak boleh mengubah alokasi bulanan.

### Pegawai
- Melihat saldo voucher bulan berjalan.
- Melihat riwayat pemakaian voucher sendiri.

## Modul Aplikasi
1. Login dan role access.
2. Master pegawai.
3. Generate voucher bulanan.
4. Transaksi penggunaan voucher.
5. Dashboard penggunaan.
6. Laporan pembayaran pedagang.
7. Ekspor CSV/Excel.
8. Pengaturan nominal voucher bulanan.

## Rekomendasi Teknologi Tahap Awal
- Python 3.11+
- Streamlit
- SQLite untuk database lokal
- Pandas untuk laporan
- OpenPyXL untuk ekspor Excel
- Git/GitHub untuk backup kode

## Rekomendasi Teknologi Tahap Lanjut
- Supabase/PostgreSQL untuk database online.
- Streamlit Community Cloud atau VPS internal untuk deployment.
- Authentication yang lebih aman.
- QR code pegawai untuk mempercepat transaksi di kasir.

## Struktur Database Awal
### users
Menyimpan akun login.
Kolom: id, username, password_hash, role, employee_id, is_active, created_at.

### employees
Menyimpan data pegawai.
Kolom: id, employee_code, full_name, department, is_active, created_at.

### merchants
Menyimpan data pedagang.
Kolom: id, merchant_name, is_active, created_at.

### monthly_allocations
Menyimpan alokasi voucher per pegawai per bulan.
Kolom: id, employee_id, period_month, amount_allocated, generated_by, generated_at, status.
period_month format YYYY-MM.

### voucher_transactions
Menyimpan semua penggunaan voucher.
Kolom: id, employee_id, merchant_id, period_month, transaction_date, amount, notes, created_by, created_at, voided_at, void_reason.

### settings
Menyimpan konfigurasi.
Kolom: key, value.

## Rumus Saldo
Saldo pegawai bulan berjalan:
alokasi bulan berjalan - total transaksi valid bulan berjalan.

## Dashboard Minimum
- Total pegawai aktif.
- Jumlah pegawai yang sudah memakai voucher hari ini.
- Total nominal voucher terpakai hari ini.
- Total nominal voucher terpakai bulan ini.
- Total yang harus dibayar ke pedagang.
- Sisa saldo total seluruh pegawai.
- Grafik penggunaan harian.
- Tabel top pengguna voucher.
- Filter tanggal/periode.

## Prinsip Audit
Semua transaksi harus tersimpan. Jika ada kesalahan, jangan hapus transaksi langsung; gunakan void/cancel dengan alasan. Ini penting agar laporan bisa dipercaya.

## Tahapan Pengembangan
1. Instal Python, VS Code, Git.
2. Buat folder project dan virtual environment.
3. Instal Streamlit, Pandas, OpenPyXL.
4. Buat aplikasi Streamlit Hello World.
5. Buat database SQLite dan tabel awal.
6. Buat seed data admin, pegawai contoh, dan merchant.
7. Buat login sederhana.
8. Buat dashboard admin.
9. Buat modul generate voucher.
10. Buat modul transaksi kasir.
11. Buat modul saldo pegawai.
12. Buat laporan dan ekspor.
13. Uji skenario bisnis.
14. Backup ke GitHub.
15. Deployment awal.

## Catatan Penting
Untuk pemula, jangan mengejar fitur terlalu banyak di awal. Bangun versi kecil yang berjalan dulu:
- Data pegawai manual.
- Generate voucher bulanan.
- Input transaksi.
- Laporan pembayaran pedagang.
Setelah itu baru tambah QR code, import Excel, multi-merchant, dan deployment online.
