# BBRI BI Dashboard

Dashboard ini mengimplementasikan Milestone 4 untuk studi kasus Business Intelligence
Market Intelligence & Corporate Action Support BBRI.

## Struktur Folder

- `data/raw/`: dataset asli, termasuk `BBRI.csv`.
- `data/processed/`: output ETL dan data mart CSV.
- `etl/`: validasi data, transformasi, dan script ETL.
- `dashboard/`: aplikasi Streamlit.
- `notebooks/`: dokumentasi ETL dalam format Jupyter Notebook.
- `outputs/validation/`: hasil validasi, metric summary, alert, dan test report.
- `outputs/screenshots/`: tempat menyimpan screenshot dashboard.
- `docs/`: schema SQL dan dokumentasi pendukung.

## Cara Menjalankan ETL

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe etl\run_etl.py
```

## Cara Menjalankan Dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

## Cara Membuka Notebook ETL

Disarankan buka file `.ipynb` langsung dari VS Code atau Jupyter yang sudah terpasang di komputer.
Jika ingin install notebook di environment project, jalankan dependency opsional:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-notebook.txt
.\.venv\Scripts\python.exe -m notebook notebooks\ETL_BBRI_Market_Intelligence.ipynb
```

## Fitur Utama

- Import CSV baru melalui dashboard.
- Validasi schema, ticker, tanggal, duplikasi, nilai numerik, `Open = 0`, dan OHLC.
- ETL menghasilkan indikator sinyal: `Daily_Return`, `MA20`, `MA60`, `Rolling_Net_Foreign_20D`, `Volume_Ratio_20D`, `Rolling_Volatility_20D`, `Drawdown_Zone`, dan `Corporate_Action_Watch`.
- Dashboard actionable berbentuk Executive Signal Dashboard, bukan chart raw biasa.
- Halaman `Dashboard` menampilkan market status, corporate action watch, KPI sinyal, chart olahan, executive insight, alert, dan rekomendasi tindakan.
- Halaman `Dashboard` dioptimasi agar lebih ringan: chart utama langsung tampil, chart lanjutan ada di expander, dan rentang data panjang otomatis memakai agregasi mingguan.
- Halaman `Proses Data` menampilkan upload CSV, validasi data, quality warning, alur ETL, preview data, dan output data mart.
- Notebook ETL untuk menunjukkan proses extract, validate, transform, load, insight, dan alert.

Catatan: `requirements.txt` sengaja dibuat ringan untuk menjalankan dashboard dan ETL. Dependency notebook dipisah agar instalasi dashboard tidak gagal karena path JupyterLab yang panjang di Windows.

## Catatan Import Data Baru

CSV baru harus mempertahankan struktur kolom utama seperti `BBRI.csv`.
Data akan ditolak jika kolom wajib hilang, ticker bukan `BBRI`, tanggal tidak valid,
nilai numerik utama gagal dikonversi, atau terdapat duplicate date.

## Catatan Environment

Folder `.venv` tidak perlu dikumpulkan. Jika ingin membersihkan project sebelum upload,
hapus folder `.venv` dan pastikan hanya source code, data, notebook, output, dan dokumen
pendukung yang dikumpulkan.
