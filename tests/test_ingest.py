"""Tests for DVF ingestion script."""

import pytest
from scripts.ingest_dvf import parse_row, filter_warehouses


class TestParseRow:
    """Tests for parse_row function."""

    def test_parse_dvf_row_extracts_correct_fields(self):
        """Verify row parsing extracts correct fields per mapping table."""
        dvf_row = {
            "id_mutation": "2024-12345",
            "adresse_numero": "42",
            "adresse_nom_voie": "Rue de la Paix",
            "code_postal": "77000",
            "nom_commune": "Melun",
            "code_departement": "77",
            "surface_reelle_bati": "15000.5",
            "valeur_fonciere": "2500000.00",
            "date_mutation": "2024-03-15",
            "latitude": "48.5423",
            "longitude": "2.6553",
            "type_local": "Local industriel. commercial ou assimilé",
        }

        result = parse_row(dvf_row)

        assert result is not None
        assert result["dvf_mutation_id"] == "2024-12345"
        assert result["address"] == "42 Rue de la Paix"
        assert result["postal_code"] == "77000"
        assert result["commune"] == "Melun"
        assert result["department"] == "77"
        assert result["surface_m2"] == 15000.5
        assert result["price_eur"] == 2500000.00
        assert result["transaction_date"] == "2024-03-15"
        assert result["latitude"] == 48.5423
        assert result["longitude"] == 2.6553
        assert result["property_type"] == "Local industriel. commercial ou assimilé"

    def test_parse_row_handles_missing_address_number(self):
        """Verify address is constructed correctly when number is missing."""
        dvf_row = {
            "id_mutation": "2024-12345",
            "adresse_numero": "",
            "adresse_nom_voie": "Rue de la Paix",
            "code_postal": "77000",
            "nom_commune": "Melun",
            "code_departement": "77",
            "surface_reelle_bati": "15000",
            "valeur_fonciere": "2500000",
            "date_mutation": "2024-03-15",
            "latitude": "48.5423",
            "longitude": "2.6553",
            "type_local": "Local industriel. commercial ou assimilé",
        }

        result = parse_row(dvf_row)

        assert result is not None
        assert result["address"] == "Rue de la Paix"

    def test_parse_row_returns_none_when_id_mutation_missing(self):
        """Verify row is skipped when id_mutation is missing."""
        dvf_row = {
            "id_mutation": "",
            "adresse_numero": "42",
            "adresse_nom_voie": "Rue de la Paix",
            "code_postal": "77000",
            "nom_commune": "Melun",
            "code_departement": "77",
            "surface_reelle_bati": "15000",
            "valeur_fonciere": "2500000",
            "date_mutation": "2024-03-15",
            "latitude": "48.5423",
            "longitude": "2.6553",
            "type_local": "Local industriel. commercial ou assimilé",
        }

        result = parse_row(dvf_row)

        assert result is None


class TestFilterWarehouses:
    """Tests for filter_warehouses function."""

    def test_filter_warehouses_applies_surface_filter(self):
        """Verify filter logic requires surface >= 10000."""
        rows = [
            {
                "id_mutation": "1",
                "type_local": "Local industriel. commercial ou assimilé",
                "surface_reelle_bati": "15000",
                "valeur_fonciere": "1000000",
            },
            {
                "id_mutation": "2",
                "type_local": "Local industriel. commercial ou assimilé",
                "surface_reelle_bati": "5000",  # Too small
                "valeur_fonciere": "500000",
            },
            {
                "id_mutation": "3",
                "type_local": "Local industriel. commercial ou assimilé",
                "surface_reelle_bati": "10000",  # Exactly 10000 - should pass
                "valeur_fonciere": "800000",
            },
        ]

        result = filter_warehouses(rows)

        assert len(result) == 2
        mutation_ids = [r["dvf_mutation_id"] for r in result]
        assert "1" in mutation_ids
        assert "3" in mutation_ids
        assert "2" not in mutation_ids

    def test_filter_warehouses_applies_type_local_filter(self):
        """Verify filter requires exact type_local value."""
        rows = [
            {
                "id_mutation": "1",
                "type_local": "Local industriel. commercial ou assimilé",  # Correct
                "surface_reelle_bati": "15000",
                "valeur_fonciere": "1000000",
            },
            {
                "id_mutation": "2",
                "type_local": "Maison",  # Wrong type
                "surface_reelle_bati": "15000",
                "valeur_fonciere": "1000000",
            },
            {
                "id_mutation": "3",
                "type_local": "Appartement",  # Wrong type
                "surface_reelle_bati": "15000",
                "valeur_fonciere": "1000000",
            },
        ]

        result = filter_warehouses(rows)

        assert len(result) == 1
        assert result[0]["dvf_mutation_id"] == "1"

    def test_filter_warehouses_limits_to_100(self):
        """Verify filter returns max 100 qualifying warehouses."""
        rows = [
            {
                "id_mutation": str(i),
                "type_local": "Local industriel. commercial ou assimilé",
                "surface_reelle_bati": "15000",
                "valeur_fonciere": "1000000",
            }
            for i in range(150)
        ]

        result = filter_warehouses(rows)

        assert len(result) == 100


class TestSkipNullValues:
    """Tests for skipping rows with NULL/empty required values."""

    def test_skip_null_surface(self):
        """Verify rows with NULL surface are skipped."""
        rows = [
            {
                "id_mutation": "1",
                "type_local": "Local industriel. commercial ou assimilé",
                "surface_reelle_bati": "",  # Empty
                "valeur_fonciere": "1000000",
            },
            {
                "id_mutation": "2",
                "type_local": "Local industriel. commercial ou assimilé",
                "surface_reelle_bati": "15000",
                "valeur_fonciere": "1000000",
            },
        ]

        result = filter_warehouses(rows)

        assert len(result) == 1
        assert result[0]["dvf_mutation_id"] == "2"

    def test_skip_null_price(self):
        """Verify rows with NULL price are skipped."""
        rows = [
            {
                "id_mutation": "1",
                "type_local": "Local industriel. commercial ou assimilé",
                "surface_reelle_bati": "15000",
                "valeur_fonciere": "",  # Empty
            },
            {
                "id_mutation": "2",
                "type_local": "Local industriel. commercial ou assimilé",
                "surface_reelle_bati": "15000",
                "valeur_fonciere": "1000000",
            },
        ]

        result = filter_warehouses(rows)

        assert len(result) == 1
        assert result[0]["dvf_mutation_id"] == "2"

    def test_skip_missing_id_mutation(self):
        """Verify rows with missing id_mutation are skipped."""
        rows = [
            {
                "id_mutation": "",  # Empty
                "type_local": "Local industriel. commercial ou assimilé",
                "surface_reelle_bati": "15000",
                "valeur_fonciere": "1000000",
            },
            {
                "id_mutation": "2",
                "type_local": "Local industriel. commercial ou assimilé",
                "surface_reelle_bati": "15000",
                "valeur_fonciere": "1000000",
            },
        ]

        result = filter_warehouses(rows)

        assert len(result) == 1
        assert result[0]["dvf_mutation_id"] == "2"


class TestTransformDate:
    """Tests for date transformation."""

    def test_transform_date_iso_format(self):
        """Verify date parsing from DVF format (YYYY-MM-DD)."""
        dvf_row = {
            "id_mutation": "2024-12345",
            "adresse_numero": "42",
            "adresse_nom_voie": "Rue de la Paix",
            "code_postal": "77000",
            "nom_commune": "Melun",
            "code_departement": "77",
            "surface_reelle_bati": "15000",
            "valeur_fonciere": "2500000",
            "date_mutation": "2024-03-15",
            "latitude": "48.5423",
            "longitude": "2.6553",
            "type_local": "Local industriel. commercial ou assimilé",
        }

        result = parse_row(dvf_row)

        assert result is not None
        assert result["transaction_date"] == "2024-03-15"

    def test_transform_date_handles_empty(self):
        """Verify empty date is handled gracefully."""
        dvf_row = {
            "id_mutation": "2024-12345",
            "adresse_numero": "42",
            "adresse_nom_voie": "Rue de la Paix",
            "code_postal": "77000",
            "nom_commune": "Melun",
            "code_departement": "77",
            "surface_reelle_bati": "15000",
            "valeur_fonciere": "2500000",
            "date_mutation": "",  # Empty
            "latitude": "48.5423",
            "longitude": "2.6553",
            "type_local": "Local industriel. commercial ou assimilé",
        }

        result = parse_row(dvf_row)

        assert result is not None
        assert result["transaction_date"] is None
