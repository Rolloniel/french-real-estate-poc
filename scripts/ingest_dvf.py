"""DVF data ingestion script.

Downloads DVF data from data.gouv.fr, filters for large warehouses,
and inserts into Supabase.

Supports processing a single department, a comma-separated list,
or all French departments at once.
"""

import argparse
import csv
import gzip
import sys
import tempfile
from pathlib import Path
from urllib.request import urlretrieve

from app.db import get_service_client

DVF_URL_TEMPLATE = (
    "https://files.data.gouv.fr/geo-dvf/latest/csv/2024/departements/{dept}.csv.gz"
)

MIN_SURFACE_M2 = 10000
WAREHOUSE_TYPE = "Local industriel. commercial ou assimilé"

# All French department codes:
# - 01 to 19 (mainland)
# - 2A and 2B (Corsica, replacing the old "20")
# - 21 to 95 (mainland)
# - 971 to 976 (overseas)
ALL_DEPARTMENTS: list[str] = (
    [f"{i:02d}" for i in range(1, 20)]
    + ["2A", "2B"]
    + [f"{i:02d}" for i in range(21, 96)]
    + [str(i) for i in range(971, 977)]
)


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


def filter_warehouses(rows: list[dict], limit: int | None = None) -> list[dict]:
    """Applies filters, returns qualifying warehouses up to an optional limit.

    Args:
        rows: List of raw DVF row dictionaries
        limit: Maximum number of warehouses to return. None means no limit.

    Returns:
        List of transformed warehouse dictionaries
    """
    warehouses = []
    for row in rows:
        if _is_valid_warehouse(row):
            parsed = parse_row(row)
            if parsed:
                warehouses.append(parsed)
                if limit is not None and len(warehouses) >= limit:
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


def process_department(department: str, limit: int | None = None) -> int:
    """Downloads, filters, and inserts warehouse data for a single department.

    Args:
        department: French department code (e.g., "77")
        limit: Maximum number of warehouses to insert. None means no limit.

    Returns:
        Number of records inserted for this department.

    Raises:
        Exception: Any error encountered during download, parsing, or insertion.
    """
    print(f"  Downloading DVF data for department {department}...")
    csv_path = download_dvf(department)

    try:
        print(f"  Parsing CSV for department {department}...")
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        print(f"  Parsed {len(rows)} rows from department {department}")

        warehouses = filter_warehouses(rows, limit=limit)
        print(f"  Filtered to {len(warehouses)} warehouses in department {department}")

        count = insert_to_supabase(warehouses)
        print(f"  Inserted {count} records for department {department}")
        return count
    finally:
        # Always clean up the temp CSV
        csv_path.unlink(missing_ok=True)


def resolve_departments(args: argparse.Namespace) -> list[str]:
    """Determines which departments to process based on CLI arguments.

    Args:
        args: Parsed CLI arguments.

    Returns:
        List of department code strings.
    """
    if args.all:
        return list(ALL_DEPARTMENTS)
    if args.departments:
        return [d.strip() for d in args.departments.split(",") if d.strip()]
    return ["77"]


def main() -> None:
    """Orchestrates the pipeline with CLI argument support."""
    parser = argparse.ArgumentParser(
        description="Ingest DVF warehouse data into Supabase."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all French departments (mainland + overseas).",
    )
    parser.add_argument(
        "--departments",
        type=str,
        default=None,
        help='Comma-separated list of department codes (e.g., "75,77,78,92,93,94").',
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of warehouses per department. Default: no limit.",
    )
    args = parser.parse_args()

    if args.all and args.departments:
        print("Error: --all and --departments are mutually exclusive.", file=sys.stderr)
        sys.exit(1)

    departments = resolve_departments(args)
    total_departments = len(departments)
    limit = args.limit

    print(f"Starting ingestion for {total_departments} department(s)...")
    if limit is not None:
        print(f"Record limit per department: {limit}")
    print()

    total_inserted = 0
    succeeded: list[str] = []
    failed: list[tuple[str, str]] = []

    for i, dept in enumerate(departments, start=1):
        print(f"[{i}/{total_departments}] Processing department {dept}...")
        try:
            count = process_department(dept, limit=limit)
            total_inserted += count
            succeeded.append(dept)
        except Exception as exc:
            error_msg = str(exc)
            print(f"  ERROR processing department {dept}: {error_msg}", file=sys.stderr)
            failed.append((dept, error_msg))
        print()

    # Summary
    print("=" * 60)
    print("INGESTION SUMMARY")
    print("=" * 60)
    print(f"Total departments processed: {len(succeeded)}/{total_departments}")
    print(f"Total records inserted:      {total_inserted}")
    if failed:
        print(f"Failed departments ({len(failed)}):")
        for dept, error in failed:
            print(f"  - {dept}: {error}")
    else:
        print("All departments processed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
