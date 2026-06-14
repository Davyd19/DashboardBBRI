# Panduan Menjalankan Dashboard BI BBRI

## 1. Persiapan Environment

Jalankan dari folder project:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Menjalankan ETL

```powershell
.\.venv\Scripts\python.exe etl\run_etl.py
```

Script ETL akan:

- membaca `data/raw/BBRI.csv`,
- memvalidasi schema, ticker, tanggal, numerik, duplicate date, dan OHLC,
- memproses nilai `Open = 0` menjadi `Open_Clean`,
- menghitung return, moving average, volatility, drawdown, foreign flow, dan volume ratio,
- membentuk data mart di memory untuk kebutuhan dashboard.

## 3. Menjalankan Dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

Halaman dashboard:

- `Dashboard`: KPI, visual signal board, trend harga, drawdown, foreign flow, komposisi status, monthly return heatmap, volume ratio, dan volatility.
- `Proses Data`: upload CSV, validasi, quality check, ETL flow, output data mart, dan preview data transformasi.

## 4. Format CSV Baru

CSV baru harus mempertahankan struktur kolom utama seperti `BBRI.csv`, terutama:

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

## 5. Catatan

Folder `.venv` tidak perlu dikumpulkan atau diunggah ke GitHub. Project ini tidak membutuhkan notebook dan tidak menyimpan output ETL ke folder terpisah.
