"""DVF data ingestion script.

Downloads DVF data from data.gouv.fr, filters for large warehouses,
and inserts into Supabase.
"""

import csv
import gzip
import tempfile
from pathlib import Path
from urllib.request import urlretrieve

from app.db import get_service_client

DVF_URL_TEMPLATE = (
    "https://files.data.gouv.fr/geo-dvf/latest/csv/2024/departements/{dept}.csv.gz"
)

MAX_WAREHOUSES = 100
MIN_SURFACE_M2 = 10000
WAREHOUSE_TYPE = "Local industriel. commercial ou assimilé"


def download_dvf(department: str) -> Path:
    """Downloads gzipped CSV to temp file, returns path to decompressed CSV.

    Args:
        department: French department code (e.g., "77")

    Returns:
        Path to the decompressed CSV file
    """
    url = DVF_URL_TEMPLATE.format(dept=department)

    # Download gzipped file
    temp_gz = tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False)
    urlretrieve(url, temp_gz.name)

    # Decompress to CSV
    temp_csv = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    with gzip.open(temp_gz.name, "rt", encoding="utf-8") as f_in:
        with open(temp_csv.name, "w", encoding="utf-8") as f_out:
            f_out.write(f_in.read())

    # Cleanup gzipped file
    Path(temp_gz.name).unlink()

    return Path(temp_csv.name)


def parse_row(row: dict) -> dict | None:
    """Extracts and transforms fields per mapping. Returns None if required fields missing.

    Args:
        row: Dictionary from CSV DictReader

    Returns:
        Transformed dictionary for database insertion, or None if id_mutation is missing
    """
    # Skip if id_mutation is missing (required field)
    if not row.get("id_mutation"):
        return None

    # Build address from components
    numero = row.get("adresse_numero") or ""
    voie = row.get("adresse_nom_voie") or ""
    address = f"{numero} {voie}".strip()

    # Parse numeric fields (allow None for optional fields)
    def parse_float(value: str | None) -> float | None:
        if not value or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    # Parse date (allow None for optional field)
    def parse_date(value: str | None) -> str | None:
        if not value or value == "":
            return None
        return value  # Already in ISO-8601 format (YYYY-MM-DD)

    return {
        "dvf_mutation_id": row.get("id_mutation"),
        "address": address,
        "postal_code": row.get("code_postal") or None,
        "commune": row.get("nom_commune") or None,
        "department": row.get("code_departement") or None,
        "surface_m2": parse_float(row.get("surface_reelle_bati")),
        "price_eur": parse_float(row.get("valeur_fonciere")),
        "transaction_date": parse_date(row.get("date_mutation")),
        "latitude": parse_float(row.get("latitude")),
        "longitude": parse_float(row.get("longitude")),
        "property_type": row.get("type_local") or None,
    }


def _is_valid_warehouse(row: dict) -> bool:
    """Returns True if row should be included. Skips if required fields missing.

    Args:
        row: Raw DVF row dictionary

    Returns:
        True if row passes all filter criteria
    """
    try:
        has_id = bool(row.get("id_mutation"))
        is_warehouse = row.get("type_local") == WAREHOUSE_TYPE
        surface = row.get("surface_reelle_bati")
        has_surface = bool(surface and surface != "")
        has_large_surface = has_surface and float(surface) >= MIN_SURFACE_M2  # type: ignore[arg-type]
        price = row.get("valeur_fonciere")
        has_price = bool(price and price != "")
        return has_id and is_warehouse and has_large_surface and has_price
    except (ValueError, TypeError):
        return False


def filter_warehouses(rows: list[dict]) -> list[dict]:
    """Applies filters, returns max 100 qualifying warehouses.

    Args:
        rows: List of raw DVF row dictionaries

    Returns:
        List of transformed warehouse dictionaries (max 100)
    """
    warehouses = []
    for row in rows:
        if _is_valid_warehouse(row):
            parsed = parse_row(row)
            if parsed:
                warehouses.append(parsed)
                if len(warehouses) >= MAX_WAREHOUSES:
                    break
    return warehouses


def insert_to_supabase(warehouses: list[dict]) -> int:
    """Inserts to DB using SERVICE_ROLE_KEY. Returns count inserted.

    Args:
        warehouses: List of warehouse dictionaries to insert

    Returns:
        Number of records inserted
    """
    if not warehouses:
        return 0

    client = get_service_client()
    result = client.table("warehouses").insert(warehouses).execute()
    return len(result.data)


def main(department: str = "77") -> None:
    """Orchestrates the pipeline.

    Args:
        department: French department code (default: "77" - Seine-et-Marne)
    """
    print(f"Downloading DVF data for department {department}...")
    csv_path = download_dvf(department)

    print("Parsing CSV...")
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    print(f"Parsed {len(rows)} rows")

    warehouses = filter_warehouses(rows)
    print(f"Filtered to {len(warehouses)} warehouses")

    count = insert_to_supabase(warehouses)
    print(f"Inserted {count} records")

    # Cleanup
    csv_path.unlink()


if __name__ == "__main__":
    main()
