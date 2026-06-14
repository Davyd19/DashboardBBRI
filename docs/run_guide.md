# Panduan Menjalankan Dashboard BI BBRI

## 1. Persiapan Environment

Jalankan perintah berikut dari folder project:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Menjalankan ETL

```powershell
.\.venv\Scripts\python.exe etl\run_etl.py
```

Output ETL akan tersimpan pada:

- `data/processed/bbri_daily_market_processed.csv`
- `data/processed/Fact_DailyMarketTrading.csv`
- `data/processed/Dim_Date.csv`
- `data/processed/Dim_Stock.csv`
- `outputs/validation/validation_report.json`
- `outputs/validation/metrics_summary.json`
- `outputs/validation/alerts.json`

## 3. Menjalankan Dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

Dashboard memiliki dua halaman utama:

- `Dashboard`: Executive Signal Dashboard berisi market status, corporate action watch, KPI sinyal, chart olahan, executive insight, alert, dan rekomendasi tindakan.
- `Proses Data`: upload CSV baru, validasi data, alur ETL, dan preview data transformasi.

Chart utama pada halaman Dashboard sudah berupa chart olahan:

- Close price vs MA20 dan MA60.
- Drawdown zone dengan batas watch -10% dan pressure -20%.
- Rolling net foreign flow 20 hari.
- Volume ratio 20 hari dibanding return harian.
- Rolling volatility 20 hari dengan threshold watch 45%.

Untuk menjaga performa, halaman Dashboard hanya merender tiga chart utama saat pertama dibuka. Chart volume spike dan volatility trend tersedia di expander `Analisis Lanjutan`. Jika rentang waktu yang dipilih lebih dari satu tahun, data chart otomatis diagregasi mingguan agar rendering lebih ringan.

## 4. Membuka Notebook ETL

Disarankan membuka file notebook langsung melalui VS Code atau Jupyter yang sudah ada di komputer. Jika ingin menjalankan notebook dari environment project, install dependency opsional terlebih dahulu:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-notebook.txt
.\.venv\Scripts\python.exe -m notebook notebooks\ETL_BBRI_Market_Intelligence.ipynb
```

Notebook ETL digunakan untuk menunjukkan proses extract, validate, transform, load, metrics, dan alert secara bertahap. Dashboard tetap menggunakan `etl/pipeline.py` sebagai engine utama agar prosesnya reusable.

## 5. Format CSV Baru

CSV baru harus mempertahankan struktur kolom utama seperti `BBRI.csv`. Kolom penting yang wajib ada antara lain:

- `Date`
- `Ticker`
- `Name`
- `Previous`
- `Open`
- `High`
- `Low`
- `Close`
- `Volume`
- `Value`
- `Frequency`
- `ForeignBuy`
- `ForeignSell`

Data akan ditolak jika ticker bukan `BBRI`, tanggal tidak valid, kolom wajib hilang, nilai numerik utama gagal dikonversi, atau terdapat duplicate date.

## 6. Catatan Environment

Folder `.venv` tidak perlu dikumpulkan. Folder tersebut hanya environment lokal untuk menjalankan dashboard dan notebook.
