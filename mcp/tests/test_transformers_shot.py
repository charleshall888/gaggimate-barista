"""Tests for shot transformer."""

from gaggimate_mcp.parsers.shot import ShotData, PhaseTransition
from gaggimate_mcp.transformers.shot import (
    transform_shot_for_ai,
    calculate_summary,
    process_phases,
    calculate_total_volume,
)


class TestShotTransformer:
    """Test shot transformation for AI analysis."""

    def test_calculate_total_volume(self):
        """Test volume calculation from flow samples."""
        samples = [
            {'pf': 2.0},  # 2 ml/s
            {'pf': 3.0},  # 3 ml/s
            {'pf': 2.5},  # 2.5 ml/s
        ]
        interval_ms = 100  # 0.1 seconds

        volume = calculate_total_volume(samples, interval_ms)

        # (2.0 + 3.0 + 2.5) * 0.1 = 0.75 ml
        assert volume == 0.8  # Rounded to 1 decimal

    def test_calculate_summary_basic(self):
        """Test summary statistics calculation."""
        shot = ShotData(
            id='1',
            version=4,
            fields_mask=0xFF,
            sample_count=5,
            sample_interval=100,
            profile_id='test',
            profile_name='Test Profile',
            timestamp=1640000000,
            rating=4,
            duration=25000,
            weight=36.0,
            samples=[
                {'t': 0, 'ct': 90.0, 'tt': 93.0, 'cp': 0.0, 'tp': 9.0, 'pf': 0.0, 'v': 0.0},
                {'t': 100, 'ct': 91.0, 'tt': 93.0, 'cp': 2.0, 'tp': 9.0, 'pf': 1.0, 'v': 0.0},
                {'t': 200, 'ct': 92.0, 'tt': 93.0, 'cp': 9.0, 'tp': 9.0, 'pf': 2.5, 'v': 1.2},
                {'t': 300, 'ct': 93.0, 'tt': 93.0, 'cp': 8.5, 'tp': 9.0, 'pf': 2.0, 'v': 5.0},
                {'t': 400, 'ct': 93.0, 'tt': 93.0, 'cp': 8.0, 'tp': 9.0, 'pf': 1.5, 'v': 10.0},
            ],
            phases=[],
        )

        summary = calculate_summary(shot)

        # Temperature
        assert summary['temperature']['min_c'] == 90.0
        assert summary['temperature']['max_c'] == 93.0
        assert summary['temperature']['avg_c'] == 91.8
        assert summary['temperature']['target_avg_c'] == 93.0

        # Pressure
        assert summary['pressure']['min_bar'] == 0.0
        assert summary['pressure']['max_bar'] == 9.0
        assert summary['pressure']['avg_bar'] == 5.5
        assert summary['pressure']['peak_time_s'] == 0.2  # At sample 2

        # Flow
        assert summary['flow']['total_volume_ml'] == 0.7
        assert summary['flow']['avg_flow_ml_s'] == 1.4
        assert summary['flow']['peak_flow_ml_s'] == 2.5
        assert summary['flow']['time_to_first_drip_s'] == 0.1  # At sample 1
        assert summary['flow']['time_to_first_weight_s'] == 0.2  # At sample 2 (first v > 0)

        # Extraction timing
        # Preinfusion is 0.2s (time to reach 50% of peak pressure)
        # Total time is 25.0s (from shot.duration)
        # Main extraction is total - preinfusion
        assert summary['extraction']['preinfusion_time_s'] == 0.2
        assert summary['extraction']['main_extraction_time_s'] == 24.8
        assert summary['extraction']['total_time_s'] == 25.0

    def test_process_phases_with_transitions(self):
        """Test phase processing with defined transitions."""
        shot = ShotData(
            id='1',
            version=5,
            fields_mask=0xFF,
            sample_count=6,
            sample_interval=100,
            profile_id='test',
            profile_name='Test Profile',
            timestamp=1640000000,
            rating=4,
            duration=30000,
            weight=40.0,
            samples=[
                {'t': 0, 'ct': 90.0, 'cp': 2.0, 'pf': 0.5, 'phase': 0},
                {'t': 100, 'ct': 91.0, 'cp': 3.0, 'pf': 0.8, 'phase': 0},
                {'t': 200, 'ct': 92.0, 'cp': 4.0, 'pf': 1.0, 'phase': 0},
                {'t': 300, 'ct': 93.0, 'cp': 9.0, 'pf': 2.5, 'phase': 1},
                {'t': 400, 'ct': 93.0, 'cp': 8.5, 'pf': 2.0, 'phase': 1},
                {'t': 500, 'ct': 93.0, 'cp': 8.0, 'pf': 1.5, 'phase': 1},
            ],
            phases=[
                PhaseTransition(sample_index=0, phase_number=0, phase_name='Preinfusion'),
                PhaseTransition(sample_index=3, phase_number=1, phase_name='Extraction'),
            ],
        )

        phases = process_phases(shot)

        assert len(phases) == 2

        # Preinfusion phase
        assert phases[0]['name'] == 'Preinfusion'
        assert phases[0]['phase_number'] == 0
        assert phases[0]['start_time_seconds'] == 0.0
        assert phases[0]['duration_seconds'] == 0.3
        assert phases[0]['sample_count'] == 3
        assert phases[0]['avg_temperature_c'] == 91.0
        assert phases[0]['avg_pressure_bar'] == 3.0
        assert len(phases[0]['samples']) == 2  # Every other sample from 3 → indices [0, 2]

        # Extraction phase
        assert phases[1]['name'] == 'Extraction'
        assert phases[1]['phase_number'] == 1
        assert phases[1]['start_time_seconds'] == 0.3
        assert phases[1]['duration_seconds'] == 0.3
        assert phases[1]['sample_count'] == 3

    def test_process_phases_without_transitions(self):
        """Test phase processing when no transitions defined."""
        shot = ShotData(
            id='1',
            version=4,
            fields_mask=0xFF,
            sample_count=3,
            sample_interval=100,
            profile_id='test',
            profile_name='Test Profile',
            timestamp=1640000000,
            rating=4,
            duration=30000,
            weight=40.0,
            samples=[
                {'t': 0, 'ct': 90.0, 'cp': 2.0, 'pf': 0.5},
                {'t': 100, 'ct': 92.0, 'cp': 9.0, 'pf': 2.5},
                {'t': 200, 'ct': 93.0, 'cp': 8.0, 'pf': 2.0},
            ],
            phases=[],
        )

        phases = process_phases(shot)

        # Should create single 'extraction' phase
        assert len(phases) == 1
        assert phases[0]['name'] == 'extraction'
        assert phases[0]['phase_number'] == 0
        assert phases[0]['start_time_seconds'] == 0.0
        assert phases[0]['duration_seconds'] == 30.0
        assert phases[0]['sample_count'] == 3

    def test_transform_shot_for_ai(self):
        """Test complete shot transformation."""
        shot = ShotData(
            id='000123',
            version=5,
            fields_mask=0xFF,
            sample_count=4,
            sample_interval=100,
            profile_id='medium_roast',
            profile_name='Medium Roast',
            timestamp=1640000000,
            rating=5,
            duration=28000,
            weight=38.5,
            samples=[
                {'t': 0, 'ct': 90.0, 'tt': 93.0, 'cp': 2.0, 'tp': 9.0, 'pf': 0.5, 'phase': 0},
                {'t': 100, 'ct': 91.0, 'tt': 93.0, 'cp': 4.0, 'tp': 9.0, 'pf': 1.0, 'phase': 0},
                {'t': 200, 'ct': 93.0, 'tt': 93.0, 'cp': 9.0, 'tp': 9.0, 'pf': 2.5, 'phase': 1},
                {'t': 300, 'ct': 93.0, 'tt': 93.0, 'cp': 8.5, 'tp': 9.0, 'pf': 2.0, 'phase': 1},
            ],
            phases=[
                PhaseTransition(sample_index=0, phase_number=0, phase_name='Preinfusion'),
                PhaseTransition(sample_index=2, phase_number=1, phase_name='Extraction'),
            ],
        )

        transformed = transform_shot_for_ai(shot)

        # Metadata
        assert transformed['shot_id'] == '000123'
        assert transformed['profile_name'] == 'Medium Roast'
        assert transformed['profile_id'] == 'medium_roast'
        assert transformed['timestamp'] == 1640000000
        assert transformed['duration_seconds'] == 28.0
        assert transformed['final_weight_g'] == 38.5

        # Summary
        assert 'summary' in transformed
        assert 'temperature' in transformed['summary']
        assert 'pressure' in transformed['summary']
        assert 'flow' in transformed['summary']
        assert 'extraction' in transformed['summary']

        # Phases
        assert len(transformed['phases']) == 2
        assert transformed['phases'][0]['name'] == 'Preinfusion'
        assert transformed['phases'][1]['name'] == 'Extraction'

    def test_transform_shot_no_weight(self):
        """Test transformation when weight is not available."""
        shot = ShotData(
            id='1',
            version=4,
            fields_mask=0xFF,
            sample_count=2,
            sample_interval=100,
            profile_id='test',
            profile_name='Test',
            timestamp=1640000000,
            rating=0,
            duration=25000,
            weight=None,
            samples=[
                {'t': 0, 'ct': 90.0, 'cp': 0.0, 'pf': 0.0},
                {'t': 100, 'ct': 93.0, 'cp': 9.0, 'pf': 2.0},
            ],
            phases=[],
        )

        transformed = transform_shot_for_ai(shot)

        assert transformed['final_weight_g'] is None

    def test_time_to_first_weight(self):
        """Test time_to_first_weight_s is computed from cup weight."""
        shot = ShotData(
            id='1',
            version=4,
            fields_mask=0xFF,
            sample_count=4,
            sample_interval=100,
            profile_id='test',
            profile_name='Test',
            timestamp=1640000000,
            rating=0,
            duration=25000,
            weight=36.0,
            samples=[
                {'t': 0, 'ct': 90.0, 'cp': 0.0, 'pf': 0.5, 'v': 0.0},
                {'t': 100, 'ct': 91.0, 'cp': 2.0, 'pf': 1.0, 'v': 0.0},
                {'t': 200, 'ct': 92.0, 'cp': 9.0, 'pf': 2.5, 'v': 0.0},
                {'t': 300, 'ct': 93.0, 'cp': 8.5, 'pf': 2.0, 'v': 2.1},
            ],
            phases=[],
        )

        summary = calculate_summary(shot)
        assert summary['flow']['time_to_first_weight_s'] == 0.3

    def test_time_to_first_weight_no_weight_data(self):
        """Test time_to_first_weight_s is None when no weight data exists."""
        shot = ShotData(
            id='1',
            version=4,
            fields_mask=0xFF,
            sample_count=3,
            sample_interval=100,
            profile_id='test',
            profile_name='Test',
            timestamp=1640000000,
            rating=0,
            duration=25000,
            weight=None,
            samples=[
                {'t': 0, 'ct': 90.0, 'cp': 0.0, 'pf': 0.0},
                {'t': 100, 'ct': 91.0, 'cp': 2.0, 'pf': 1.0},
                {'t': 200, 'ct': 92.0, 'cp': 9.0, 'pf': 2.5},
            ],
            phases=[],
        )

        summary = calculate_summary(shot)
        assert summary['flow']['time_to_first_weight_s'] is None

    def test_transform_shot_incomplete(self):
        """Test transformation with incomplete shot data."""
        shot = ShotData(
            id='1',
            version=4,
            fields_mask=0xFF,
            sample_count=2,
            sample_interval=100,
            profile_id='test',
            profile_name='Test',
            timestamp=1640000000,
            rating=0,
            duration=25000,
            weight=None,
            samples=[
                {'t': 0, 'ct': 90.0, 'cp': 0.0, 'pf': 0.0},
                {'t': 100, 'ct': 93.0, 'cp': 9.0, 'pf': 2.0},
            ],
            phases=[],
            incomplete=True,
        )

        transformed = transform_shot_for_ai(shot)

        # Should still transform successfully
        assert transformed['shot_id'] == '1'
        assert len(transformed['phases']) == 1
