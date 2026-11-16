#!/bin/sh
# Rebuild every derived file in kujovic_family/ from the PDFs in pdfs/.
# Usage: sh scripts/run_all.sh <python with pymupdf, numpy, scipy, matplotlib>
set -e
PY=${1:-python3}
cd "$(dirname "$0")/.."
$PY -I scripts/s1_extract.py pdfs/S1_kujovic2024_AFM_21p4.pdf .
$PY -I scripts/s1_raster_check.py pdfs/S1_kujovic2024_AFM_21p4.pdf .
$PY -I scripts/s4_extract.py pdfs/S4_kujovic_PhD_thesis_2025.pdf .
$PY -I scripts/s3_crosscheck.py pdfs/S3_kujovic2026_JPhysEnergy_CeZnO.pdf .
$PY -I scripts/s1_vs_s4_check.py .
$PY -I scripts/make_params.py .
$PY -I scripts/make_tables.py .
$PY -I scripts/make_index.py .
