from datetime import date, datetime


def format_rupiah(amount):
    """
    Mengubah angka menjadi format rupiah.
    Contoh: 75000 -> Rp75.000
    """
    try:
        return "Rp" + f"{int(amount):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp0"


def get_current_period_month():
    """
    Mengambil periode bulan berjalan dalam format YYYY-MM.
    """
    return date.today().strftime("%Y-%m")


def is_valid_period_month(period_month):
    """
    Validasi format periode bulan.
    Format benar: YYYY-MM
    Contoh: 2026-05
    """
    if not isinstance(period_month, str):
        return False

    period_month = period_month.strip()

    if len(period_month) != 7:
        return False

    if period_month[4] != "-":
        return False

    year_part = period_month[:4]
    month_part = period_month[5:7]

    if not year_part.isdigit():
        return False

    if not month_part.isdigit():
        return False

    month_number = int(month_part)

    if month_number < 1 or month_number > 12:
        return False

    return True


def get_now_text():
    """
    Waktu sekarang untuk disimpan ke SQLite.
    """
    return datetime.now().isoformat(timespec="seconds")


def get_today_text():
    """
    Tanggal hari ini format YYYY-MM-DD.
    """
    return date.today().isoformat()