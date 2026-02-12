"""Tests for rating/feedback Pydantic models."""

import pytest
from pydantic import ValidationError
from gaggimate_mcp.models.rating import BalanceTaste, ShotRating, RatingUpdate


class TestBalanceTaste:
    """Test BalanceTaste enum."""

    def test_balance_taste_values(self):
        """Test balance/taste enum values."""
        assert BalanceTaste.BITTER.value == "bitter"
        assert BalanceTaste.BALANCED.value == "balanced"
        assert BalanceTaste.SOUR.value == "sour"


class TestShotRating:
    """Test ShotRating model."""

    def test_shot_rating_minimal(self):
        """Test shot rating with minimal fields."""
        rating = ShotRating(shot_id="000123")
        assert rating.shot_id == "000123"
        assert rating.rating is None
        assert rating.notes is None

    def test_shot_rating_full(self):
        """Test shot rating with all fields."""
        rating = ShotRating(
            shot_id="000124",
            rating=4,
            dose_in=18.0,
            dose_out=36.0,
            grind_setting="15",
            balance_taste=BalanceTaste.BALANCED,
            bean_type="Ethiopian Yirgacheffe",
            notes="Bright acidity, floral notes, clean finish"
        )
        assert rating.shot_id == "000124"
        assert rating.rating == 4
        assert rating.dose_in == 18.0
        assert rating.dose_out == 36.0
        assert rating.ratio == 2.0  # Calculated
        assert rating.balance_taste == BalanceTaste.BALANCED
        assert rating.bean_type == "Ethiopian Yirgacheffe"

    def test_rating_validation_min(self):
        """Test rating min value (0)."""
        rating = ShotRating(shot_id="000125", rating=0)
        assert rating.rating == 0

    def test_rating_validation_max(self):
        """Test rating max value (5)."""
        rating = ShotRating(shot_id="000126", rating=5)
        assert rating.rating == 5

    def test_rating_validation_too_high(self):
        """Test rating cannot exceed 5."""
        with pytest.raises(ValidationError):
            ShotRating(shot_id="000127", rating=6)

    def test_rating_validation_negative(self):
        """Test rating cannot be negative."""
        with pytest.raises(ValidationError):
            ShotRating(shot_id="000128", rating=-1)

    def test_ratio_calculation(self):
        """Test ratio is calculated from dose in/out."""
        rating = ShotRating(
            shot_id="000129",
            dose_in=18.0,
            dose_out=36.0
        )
        assert rating.ratio == 2.0

    def test_ratio_calculation_decimal(self):
        """Test ratio calculation with decimals."""
        rating = ShotRating(
            shot_id="000130",
            dose_in=18.0,
            dose_out=35.0
        )
        assert abs(rating.ratio - 1.944) < 0.001

    def test_ratio_only_dose_in(self):
        """Test ratio when only dose_in provided."""
        rating = ShotRating(
            shot_id="000131",
            dose_in=18.0
        )
        assert rating.ratio is None

    def test_ratio_only_dose_out(self):
        """Test ratio when only dose_out provided."""
        rating = ShotRating(
            shot_id="000132",
            dose_out=36.0
        )
        assert rating.ratio is None

    def test_dose_validation(self):
        """Test dose values must be positive."""
        with pytest.raises(ValidationError):
            ShotRating(shot_id="000133", dose_in=-1.0)

        with pytest.raises(ValidationError):
            ShotRating(shot_id="000134", dose_out=-1.0)


class TestRatingUpdate:
    """Test RatingUpdate model."""

    def test_rating_update_partial(self):
        """Test rating update with partial fields."""
        update = RatingUpdate(
            shot_id="000135",
            rating=4
        )
        assert update.shot_id == "000135"
        assert update.rating == 4
        assert update.notes is None

    def test_rating_update_full(self):
        """Test rating update with all fields."""
        update = RatingUpdate(
            shot_id="000136",
            rating=5,
            dose_in=18.0,
            dose_out=36.0,
            grind_setting="14",
            balance_taste=BalanceTaste.BALANCED,
            bean_type="Colombian Supremo",
            notes="Perfect extraction, sweet and balanced"
        )
        assert update.rating == 5
        assert update.bean_type == "Colombian Supremo"
        assert update.balance_taste == BalanceTaste.BALANCED

    def test_rating_update_to_shot_rating(self):
        """Test converting RatingUpdate to ShotRating."""
        update = RatingUpdate(
            shot_id="000137",
            rating=4,
            notes="Good shot"
        )
        # Can create ShotRating from update data
        rating = ShotRating(**update.model_dump())
        assert rating.shot_id == "000137"
        assert rating.rating == 4
        assert rating.notes == "Good shot"

    def test_rating_merge(self):
        """Test merging rating updates."""
        existing = ShotRating(
            shot_id="000138",
            rating=3,
            dose_in=18.0,
            notes="Initial notes"
        )

        update = RatingUpdate(
            shot_id="000138",
            rating=4,
            balance_taste=BalanceTaste.BALANCED
        )

        # Merge logic (simulated)
        merged_data = existing.model_dump()
        update_data = update.model_dump(exclude_none=True)
        merged_data.update(update_data)

        merged = ShotRating(**merged_data)
        assert merged.rating == 4  # Updated
        assert merged.dose_in == 18.0  # Kept
        assert merged.balance_taste == BalanceTaste.BALANCED  # Added
        assert merged.notes == "Initial notes"  # Kept


class TestRatingJsonSerialization:
    """Test JSON serialization of rating models."""

    def test_shot_rating_json(self):
        """Test ShotRating JSON serialization."""
        rating = ShotRating(
            shot_id="000139",
            rating=4,
            dose_in=18.0,
            dose_out=36.0,
            balance_taste=BalanceTaste.BALANCED,
            notes="Test notes"
        )
        data = rating.model_dump()
        assert data["shot_id"] == "000139"
        assert data["rating"] == 4
        assert data["balance_taste"] == "balanced"

    def test_rating_update_json(self):
        """Test RatingUpdate JSON serialization."""
        update = RatingUpdate(
            shot_id="000140",
            rating=5
        )
        data = update.model_dump(exclude_none=True)
        assert data["shot_id"] == "000140"
        assert data["rating"] == 5
        assert "notes" not in data  # None values excluded
