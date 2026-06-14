# BBRI BI Dashboard

Dashboard Business Intelligence untuk studi kasus Market Intelligence & Corporate Action Support BBRI.

Project ini dibuat sederhana: ETL menggunakan Python, hasil data mart dimuat ke MySQL/MariaDB, dashboard menggunakan Streamlit, dan dataset utama berada di `data/raw/BBRI.csv`.

## Struktur Folder

- `dashboard/`: aplikasi Streamlit.
- `dashboard/assets/`: logo dan aset dashboard.
- `data/raw/`: dataset sumber.
- `etl/`: validasi, transformasi, pipeline ETL Python, dan loader MySQL.
- `docs/`: panduan menjalankan project dan skema data.
- `tests/`: skenario validasi sederhana.

## Instalasi

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Menjalankan ETL

```powershell
.\.venv\Scripts\python.exe etl\run_etl.py
```

ETL membaca CSV, memvalidasi data, melakukan preprocessing, membentuk data mart, lalu memuatnya ke database MySQL/MariaDB `dashboard_bbri`.

Konfigurasi default database:

- `DB_HOST=localhost`
- `DB_PORT=3306`
- `DB_USER=root`
- `DB_PASSWORD=`
- `DB_NAME=dashboard_bbri`

Jika hanya ingin menjalankan ETL tanpa load database:

```powershell
.\.venv\Scripts\python.exe etl\run_etl.py --no-db
```

## Menjalankan Dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

Dashboard memiliki dua halaman:

- `Dashboard`: KPI, visual signal, dan visualisasi pasar BBRI. Dashboard membaca MySQL terlebih dahulu dan fallback ke CSV jika database belum siap.
- `Proses Data`: upload CSV, validasi data, quality check, alur ETL, dan preview data hasil transformasi.

## Catatan Data

CSV baru harus mempertahankan struktur kolom utama seperti `BBRI.csv`. Data ditolak jika kolom wajib hilang, ticker bukan `BBRI`, tanggal tidak valid, nilai numerik utama gagal dikonversi, atau terdapat duplicate date.

Nilai `Open = 0` tidak dihapus. Pipeline menyimpan nilai asli, menandai baris yang diimputasi, lalu mengisi `Open_Clean` dari `Previous` atau `Close` hari sebelumnya.
