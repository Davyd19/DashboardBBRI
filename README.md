# BBRI BI Dashboard

Dashboard Business Intelligence untuk studi kasus Market Intelligence & Corporate Action Support BBRI.

Project ini dibuat sederhana: ETL menggunakan Python, dashboard menggunakan Streamlit, dan dataset utama berada di `data/raw/BBRI.csv`.

## Struktur Folder

- `dashboard/`: aplikasi Streamlit.
- `dashboard/assets/`: logo dan aset dashboard.
- `data/raw/`: dataset sumber.
- `etl/`: validasi, transformasi, dan pipeline ETL Python.
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

ETL membaca CSV, memvalidasi data, melakukan preprocessing, membentuk data mart di memory, dan menampilkan ringkasan hasil di terminal. ETL tidak membuat file output tambahan agar repo tetap bersih.

## Menjalankan Dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

Dashboard memiliki dua halaman:

- `Dashboard`: KPI, visual signal, dan visualisasi pasar BBRI.
- `Proses Data`: upload CSV, validasi data, quality check, alur ETL, dan preview data hasil transformasi.

## Catatan Data

CSV baru harus mempertahankan struktur kolom utama seperti `BBRI.csv`. Data ditolak jika kolom wajib hilang, ticker bukan `BBRI`, tanggal tidak valid, nilai numerik utama gagal dikonversi, atau terdapat duplicate date.

Nilai `Open = 0` tidak dihapus. Pipeline menyimpan nilai asli, menandai baris yang diimputasi, lalu mengisi `Open_Clean` dari `Previous` atau `Close` hari sebelumnya.
