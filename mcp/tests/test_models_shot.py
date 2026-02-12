"""Tests for shot Pydantic models."""

import pytest
from datetime import datetime
from pydantic import ValidationError
from gaggimate_mcp.models.shot import (
    ShotMetadata,
    TemperatureStats,
    PressureStats,
    FlowStats,
    ExtractionStats,
    ShotSummary,
    ShotPhaseData,
    TransformedShot,
    ShotListItem,
)


class TestShotMetadata:
    """Test ShotMetadata model."""

    def test_shot_metadata_minimal(self):
        """Test shot metadata with minimal fields."""
        metadata = ShotMetadata(
            shot_id="000123",
            profile_name="Agent-Test",
            profile_id="profile-123",
            timestamp=datetime(2025, 1, 26, 10, 30),
            duration_seconds=28.5,
            final_weight_grams=None,
            sample_count=285,
            sample_interval_ms=100
        )
        assert metadata.shot_id == "000123"
        assert metadata.duration_seconds == 28.5
        assert metadata.final_weight_grams is None

    def test_shot_metadata_with_weight(self):
        """Test shot metadata with weight."""
        metadata = ShotMetadata(
            shot_id="000124",
            profile_name="Test",
            profile_id="profile-123",
            timestamp=datetime.now(),
            duration_seconds=30.0,
            final_weight_grams=36.5,
            sample_count=300,
            sample_interval_ms=100
        )
        assert metadata.final_weight_grams == 36.5


class TestStats:
    """Test statistics models."""

    def test_temperature_stats(self):
        """Test temperature statistics."""
        stats = TemperatureStats(
            min_celsius=90.5,
            max_celsius=93.2,
            average_celsius=92.1,
            target_average=93.0
        )
        assert stats.min_celsius == 90.5
        assert stats.average_celsius == 92.1

    def test_pressure_stats(self):
        """Test pressure statistics."""
        stats = PressureStats(
            min_bar=0.0,
            max_bar=9.2,
            average_bar=8.5,
            peak_time_seconds=15.3
        )
        assert stats.max_bar == 9.2
        assert stats.peak_time_seconds == 15.3

    def test_flow_stats(self):
        """Test flow statistics."""
        stats = FlowStats(
            total_volume_ml=45.2,
            average_flow_rate_ml_s=1.8,
            peak_flow_ml_s=2.5,
            time_to_first_drip_seconds=8.2
        )
        assert stats.total_volume_ml == 45.2
        assert stats.time_to_first_drip_seconds == 8.2

    def test_flow_stats_no_drip_time(self):
        """Test flow stats without drip time."""
        stats = FlowStats(
            total_volume_ml=40.0,
            average_flow_rate_ml_s=1.5,
            peak_flow_ml_s=2.0,
            time_to_first_drip_seconds=None
        )
        assert stats.time_to_first_drip_seconds is None

    def test_extraction_stats(self):
        """Test extraction statistics."""
        stats = ExtractionStats(
            extraction_time_seconds=28.5,
            preinfusion_time_seconds=8.0,
            main_extraction_seconds=20.5
        )
        assert stats.extraction_time_seconds == 28.5
        assert stats.preinfusion_time_seconds == 8.0


class TestShotSummary:
    """Test ShotSummary model."""

    def test_shot_summary(self):
        """Test complete shot summary."""
        summary = ShotSummary(
            temperature=TemperatureStats(
                min_celsius=90.0,
                max_celsius=93.0,
                average_celsius=92.0,
                target_average=93.0
            ),
            pressure=PressureStats(
                min_bar=0.0,
                max_bar=9.0,
                average_bar=8.5,
                peak_time_seconds=15.0
            ),
            flow=FlowStats(
                total_volume_ml=42.0,
                average_flow_rate_ml_s=1.7,
                peak_flow_ml_s=2.3,
                time_to_first_drip_seconds=8.5
            ),
            extraction=ExtractionStats(
                extraction_time_seconds=28.0,
                preinfusion_time_seconds=8.0,
                main_extraction_seconds=20.0
            )
        )
        assert summary.temperature.average_celsius == 92.0
        assert summary.pressure.max_bar == 9.0


class TestShotPhaseData:
    """Test ShotPhaseData model."""

    def test_shot_phase_data(self):
        """Test shot phase data."""
        phase = ShotPhaseData(
            name="Extraction",
            phase_number=1,
            start_time_seconds=8.0,
            duration_seconds=20.0,
            sample_count=200,
            avg_temperature_c=92.5,
            avg_pressure_bar=9.0,
            total_flow_ml=35.0
        )
        assert phase.name == "Extraction"
        assert phase.duration_seconds == 20.0
        assert phase.avg_pressure_bar == 9.0


class TestTransformedShot:
    """Test TransformedShot model."""

    def test_transformed_shot(self):
        """Test complete transformed shot."""
        shot = TransformedShot(
            metadata=ShotMetadata(
                shot_id="000125",
                profile_name="Agent-Test",
                profile_id="profile-123",
                timestamp=datetime(2025, 1, 26, 10, 30),
                duration_seconds=28.5,
                final_weight_grams=36.0,
                sample_count=285,
                sample_interval_ms=100,
                bluetooth_scale_connected=True,
                volumetric_mode=False
            ),
            summary=ShotSummary(
                temperature=TemperatureStats(
                    min_celsius=90.0,
                    max_celsius=93.0,
                    average_celsius=92.0,
                    target_average=93.0
                ),
                pressure=PressureStats(
                    min_bar=0.0,
                    max_bar=9.0,
                    average_bar=8.5,
                    peak_time_seconds=15.0
                ),
                flow=FlowStats(
                    total_volume_ml=42.0,
                    average_flow_rate_ml_s=1.7,
                    peak_flow_ml_s=2.3,
                    time_to_first_drip_seconds=8.5
                ),
                extraction=ExtractionStats(
                    extraction_time_seconds=28.5,
                    preinfusion_time_seconds=8.0,
                    main_extraction_seconds=20.5
                )
            ),
            phases=[
                ShotPhaseData(
                    name="Preinfusion",
                    phase_number=0,
                    start_time_seconds=0.0,
                    duration_seconds=8.0,
                    sample_count=80,
                    avg_temperature_c=92.0,
                    avg_pressure_bar=2.0,
                    total_flow_ml=5.0
                ),
                ShotPhaseData(
                    name="Extraction",
                    phase_number=1,
                    start_time_seconds=8.0,
                    duration_seconds=20.5,
                    sample_count=205,
                    avg_temperature_c=92.5,
                    avg_pressure_bar=9.0,
                    total_flow_ml=37.0
                )
            ]
        )
        assert shot.metadata.shot_id == "000125"
        assert len(shot.phases) == 2
        assert shot.phases[0].name == "Preinfusion"


class TestShotListItem:
    """Test ShotListItem model."""

    def test_shot_list_item_minimal(self):
        """Test shot list item with minimal fields."""
        item = ShotListItem(
            id="000126",
            timestamp=datetime(2025, 1, 26, 11, 0),
            profile_id="profile-123",
            profile_name="Agent-Test",
            duration_seconds=28.0,
            final_weight_grams=None,
            rating=None,
            has_notes=False
        )
        assert item.id == "000126"
        assert item.rating is None
        assert item.has_notes is False

    def test_shot_list_item_with_rating(self):
        """Test shot list item with rating."""
        item = ShotListItem(
            id="000127",
            timestamp=datetime.now(),
            profile_id="profile-123",
            profile_name="Test",
            duration_seconds=30.0,
            final_weight_grams=36.5,
            rating=4,
            has_notes=True
        )
        assert item.rating == 4
        assert item.has_notes is True

    def test_shot_list_item_rating_validation(self):
        """Test rating must be 0-5."""
        with pytest.raises(ValidationError):
            ShotListItem(
                id="000128",
                timestamp=datetime.now(),
                profile_id="profile-123",
                profile_name="Test",
                duration_seconds=30.0,
                final_weight_grams=36.0,
                rating=6,
                has_notes=False
            )

    def test_shot_list_item_json_serialization(self):
        """Test shot list item can be serialized."""
        item = ShotListItem(
            id="000129",
            timestamp=datetime(2025, 1, 26, 12, 0),
            profile_id="profile-123",
            profile_name="Test",
            duration_seconds=28.5,
            final_weight_grams=35.0,
            rating=5,
            has_notes=True
        )
        data = item.model_dump()
        assert data["id"] == "000129"
        assert data["rating"] == 5
