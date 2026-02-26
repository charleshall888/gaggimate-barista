"""Tests for shot transformer."""

from gaggimate_mcp.parsers.shot import ShotData, PhaseTransition
from gaggimate_mcp.transformers.shot import (
    transform_shot_for_ai,
    calculate_summary,
    process_phases,
    calculate_total_volume,
    trim_trailing_artifacts,
    select_representative_samples,
    compute_compliance_metrics,
    MAX_SAMPLES_PER_PHASE,
)


class TestCalculateTotalVolume:
    """Test volume calculation from flow samples."""

    def test_basic_volume(self):
        samples = [
            {'pf': 2.0},  # 2 ml/s
            {'pf': 3.0},  # 3 ml/s
            {'pf': 2.5},  # 2.5 ml/s
        ]
        interval_ms = 100  # 0.1 seconds

        volume = calculate_total_volume(samples, interval_ms)

        # (2.0 + 3.0 + 2.5) * 0.1 = 0.75 ml
        assert volume == 0.8  # Rounded to 1 decimal


class TestTrimTrailingArtifacts:
    """Test trailing artifact removal."""

    def test_trailing_zeros_removed(self):
        """5 good samples + 3 trailing artifacts → 5 returned."""
        samples = [
            {'cp': 9.0, 'pf': 2.5},
            {'cp': 8.5, 'pf': 2.0},
            {'cp': 7.0, 'pf': 1.8},
            {'cp': 5.0, 'pf': 1.2},
            {'cp': 3.0, 'pf': 0.8},
            # Trailing artifacts
            {'cp': 0.5, 'pf': 0.02},
            {'cp': 0.2, 'pf': 0.0},
            {'cp': 0.0, 'pf': 0.0},
        ]
        result = trim_trailing_artifacts(samples)
        assert len(result) == 5
        assert result[-1]['cp'] == 3.0

    def test_mid_shot_bloom_pause_preserved(self):
        """Bloom phase (low pressure, low flow) followed by brew → only trailing removed."""
        samples = [
            # Pre-infusion fill
            {'cp': 2.0, 'pf': 3.0},
            # Bloom pause — low pressure AND low flow, but mid-shot
            {'cp': 0.5, 'pf': 0.0},
            {'cp': 0.3, 'pf': 0.0},
            # Extraction ramp
            {'cp': 5.0, 'pf': 1.5},
            {'cp': 8.0, 'pf': 2.0},
            {'cp': 7.5, 'pf': 1.8},
            # Trailing artifact
            {'cp': 0.3, 'pf': 0.0},
        ]
        result = trim_trailing_artifacts(samples)
        assert len(result) == 6
        # Bloom pause samples preserved
        assert result[1]['cp'] == 0.5
        assert result[2]['cp'] == 0.3
        # Last good sample is the extraction
        assert result[-1]['cp'] == 7.5

    def test_no_artifacts_unchanged(self):
        """Samples with no trailing artifacts returned unchanged."""
        samples = [
            {'cp': 9.0, 'pf': 2.5},
            {'cp': 8.0, 'pf': 2.0},
            {'cp': 7.0, 'pf': 1.5},
        ]
        result = trim_trailing_artifacts(samples)
        assert len(result) == 3
        assert result is samples  # Same object, not a copy

    def test_single_sample_preserved(self):
        """Single sample always preserved even if it looks like an artifact."""
        samples = [{'cp': 0.0, 'pf': 0.0}]
        result = trim_trailing_artifacts(samples)
        assert len(result) == 1

    def test_all_artifact_shot_preserves_one(self):
        """If every sample looks like an artifact, at least 1 is preserved."""
        samples = [
            {'cp': 0.0, 'pf': 0.0},
            {'cp': 0.0, 'pf': 0.0},
            {'cp': 0.0, 'pf': 0.0},
        ]
        result = trim_trailing_artifacts(samples)
        assert len(result) == 1

    def test_boundary_values_at_thresholds(self):
        """pf=0.05 and cp=0.99 are artifacts; pf=0.06 or cp=1.0 are not."""
        # Exactly at threshold — IS an artifact (pf <= 0.05 AND cp < 1.0)
        samples_at_threshold = [
            {'cp': 5.0, 'pf': 2.0},
            {'cp': 0.99, 'pf': 0.05},
        ]
        result = trim_trailing_artifacts(samples_at_threshold)
        assert len(result) == 1

        # Flow just above threshold — NOT an artifact
        samples_flow_above = [
            {'cp': 5.0, 'pf': 2.0},
            {'cp': 0.5, 'pf': 0.06},
        ]
        result = trim_trailing_artifacts(samples_flow_above)
        assert len(result) == 2

        # Pressure at threshold — NOT an artifact (cp < 1.0 required, 1.0 fails)
        samples_pressure_at = [
            {'cp': 5.0, 'pf': 2.0},
            {'cp': 1.0, 'pf': 0.0},
        ]
        result = trim_trailing_artifacts(samples_pressure_at)
        assert len(result) == 2

    def test_empty_samples(self):
        """Empty list returns empty."""
        result = trim_trailing_artifacts([])
        assert result == []


class TestSelectRepresentativeSamples:
    """Test adaptive downsampling."""

    def test_short_phase_step_2(self):
        """10 samples → step=2, 5 output samples."""
        phase_samples = [
            {'t': i * 100, 'ct': 93.0, 'cp': 9.0, 'pf': 2.0, 'v': float(i)}
            for i in range(10)
        ]
        result = select_representative_samples(phase_samples, 100)
        assert len(result) == 5
        # Verify indices 0, 2, 4, 6, 8
        assert result[0]['weight_g'] == 0.0
        assert result[1]['weight_g'] == 2.0
        assert result[4]['weight_g'] == 8.0

    def test_long_phase_capped(self):
        """100 samples → capped at ~25."""
        phase_samples = [
            {'t': i * 100, 'ct': 93.0, 'cp': 9.0, 'pf': 2.0, 'v': 0.0}
            for i in range(100)
        ]
        result = select_representative_samples(phase_samples, 100)
        assert len(result) <= MAX_SAMPLES_PER_PHASE

    def test_empty_returns_empty(self):
        result = select_representative_samples([], 100)
        assert result == []

    def test_resistance_populated_from_pr(self):
        """Resistance field populated from raw 'pr' field."""
        phase_samples = [
            {'t': 0, 'ct': 93.0, 'cp': 9.0, 'pf': 2.0, 'v': 0.0, 'pr': 4.56},
            {'t': 100, 'ct': 93.0, 'cp': 9.0, 'pf': 2.0, 'v': 0.0, 'pr': 5.12},
            {'t': 200, 'ct': 93.0, 'cp': 9.0, 'pf': 2.0, 'v': 0.0},  # No pr
        ]
        result = select_representative_samples(phase_samples, 100)
        # Step=2, so indices 0 and 2
        assert result[0]['resistance'] == 4.56
        assert result[1]['resistance'] == 0.0  # Default when pr missing

    def test_resistance_defaults_to_zero(self):
        """Resistance defaults to 0.0 when no pr field in samples."""
        phase_samples = [
            {'t': 0, 'ct': 93.0, 'cp': 9.0, 'pf': 2.0, 'v': 0.0},
            {'t': 100, 'ct': 93.0, 'cp': 9.0, 'pf': 2.0, 'v': 0.0},
        ]
        result = select_representative_samples(phase_samples, 100)
        assert result[0]['resistance'] == 0.0


class TestCalculateSummary:
    """Test summary statistics calculation."""

    def test_basic_summary(self):
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
        assert summary['extraction']['preinfusion_time_s'] == 0.2
        assert summary['extraction']['main_extraction_time_s'] == 24.8
        assert summary['extraction']['total_time_s'] == 25.0

    def test_summary_excludes_trailing_artifacts(self):
        """Verify avg_bar and avg_flow are computed from clean samples only."""
        shot = ShotData(
            id='1',
            version=4,
            fields_mask=0xFF,
            sample_count=5,
            sample_interval=100,
            profile_id='test',
            profile_name='Test',
            timestamp=1640000000,
            rating=0,
            duration=5000,
            weight=36.0,
            samples=[
                {'t': 0, 'ct': 93.0, 'tt': 93.0, 'cp': 9.0, 'pf': 2.0, 'v': 0.0},
                {'t': 100, 'ct': 93.0, 'tt': 93.0, 'cp': 8.0, 'pf': 1.8, 'v': 5.0},
                {'t': 200, 'ct': 93.0, 'tt': 93.0, 'cp': 7.0, 'pf': 1.5, 'v': 10.0},
                # Trailing artifacts — should be excluded
                {'t': 300, 'ct': 91.0, 'tt': 93.0, 'cp': 0.3, 'pf': 0.0, 'v': 10.0},
                {'t': 400, 'ct': 90.0, 'tt': 93.0, 'cp': 0.0, 'pf': 0.0, 'v': 10.0},
            ],
            phases=[],
        )

        summary = calculate_summary(shot)

        # Without trimming: avg_bar = (9+8+7+0.3+0)/5 = 4.86
        # With trimming: avg_bar = (9+8+7)/3 = 8.0
        assert summary['pressure']['avg_bar'] == 8.0
        # Without trimming: avg_flow = (2.0+1.8+1.5+0+0)/5 = 1.06
        # With trimming: avg_flow = (2.0+1.8+1.5)/3 = 1.8 (rounded)
        assert summary['flow']['avg_flow_ml_s'] == 1.8

    def test_summary_preserves_artifacts_for_incomplete_shot(self):
        """Incomplete shots should NOT have artifacts trimmed."""
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
            duration=3000,
            weight=None,
            samples=[
                {'t': 0, 'ct': 93.0, 'tt': 93.0, 'cp': 2.0, 'pf': 0.5, 'v': 0.0},
                # These look like artifacts but shot is incomplete (aborted mid-bloom)
                {'t': 100, 'ct': 93.0, 'tt': 93.0, 'cp': 0.3, 'pf': 0.0, 'v': 0.0},
                {'t': 200, 'ct': 93.0, 'tt': 93.0, 'cp': 0.0, 'pf': 0.0, 'v': 0.0},
            ],
            phases=[],
            incomplete=True,
        )

        summary = calculate_summary(shot)

        # All 3 samples included: avg_bar = (2.0+0.3+0.0)/3 ≈ 0.8
        assert summary['pressure']['avg_bar'] == 0.8


class TestProcessPhases:
    """Test phase processing."""

    def test_phases_with_transitions(self):
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

    def test_phases_without_transitions(self):
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

    def test_last_phase_trimmed(self):
        """Verify last phase stats exclude trailing artifacts, earlier phases untouched."""
        shot = ShotData(
            id='1',
            version=5,
            fields_mask=0xFF,
            sample_count=8,
            sample_interval=100,
            profile_id='test',
            profile_name='Test',
            timestamp=1640000000,
            rating=0,
            duration=8000,
            weight=36.0,
            samples=[
                # Phase 0: Preinfusion (3 samples)
                {'t': 0, 'ct': 90.0, 'cp': 2.0, 'pf': 0.5, 'phase': 0},
                {'t': 100, 'ct': 91.0, 'cp': 3.0, 'pf': 0.8, 'phase': 0},
                {'t': 200, 'ct': 92.0, 'cp': 4.0, 'pf': 1.0, 'phase': 0},
                # Phase 1: Extraction (3 good + 2 trailing artifacts)
                {'t': 300, 'ct': 93.0, 'cp': 9.0, 'pf': 2.5, 'phase': 1},
                {'t': 400, 'ct': 93.0, 'cp': 8.0, 'pf': 2.0, 'phase': 1},
                {'t': 500, 'ct': 93.0, 'cp': 7.0, 'pf': 1.5, 'phase': 1},
                # Trailing artifacts
                {'t': 600, 'ct': 91.0, 'cp': 0.3, 'pf': 0.0, 'phase': 1},
                {'t': 700, 'ct': 90.0, 'cp': 0.0, 'pf': 0.0, 'phase': 1},
            ],
            phases=[
                PhaseTransition(sample_index=0, phase_number=0, phase_name='Preinfusion'),
                PhaseTransition(sample_index=3, phase_number=1, phase_name='Extraction'),
            ],
        )

        phases = process_phases(shot)

        assert len(phases) == 2

        # Phase 0 (preinfusion): NOT trimmed — all 3 samples
        assert phases[0]['sample_count'] == 3
        assert phases[0]['avg_pressure_bar'] == 3.0

        # Phase 1 (extraction): trimmed — only 3 good samples, not 5
        assert phases[1]['sample_count'] == 3
        # Without trimming: avg = (9+8+7+0.3+0)/5 = 4.86
        # With trimming: avg = (9+8+7)/3 = 8.0
        assert phases[1]['avg_pressure_bar'] == 8.0

    def test_samples_have_resistance_field(self):
        """Verify representative samples include resistance from pr field."""
        shot = ShotData(
            id='1',
            version=5,
            fields_mask=0xFFF,
            sample_count=3,
            sample_interval=100,
            profile_id='test',
            profile_name='Test',
            timestamp=1640000000,
            rating=0,
            duration=3000,
            weight=None,
            samples=[
                {'t': 0, 'ct': 93.0, 'cp': 9.0, 'pf': 2.0, 'v': 0.0, 'pr': 3.5},
                {'t': 100, 'ct': 93.0, 'cp': 8.0, 'pf': 1.8, 'v': 5.0, 'pr': 4.2},
                {'t': 200, 'ct': 93.0, 'cp': 7.0, 'pf': 1.5, 'v': 10.0, 'pr': 5.0},
            ],
            phases=[],
        )

        phases = process_phases(shot)
        # Step=2 from 3 samples → indices [0, 2]
        assert len(phases[0]['samples']) == 2
        assert phases[0]['samples'][0]['resistance'] == 3.5
        assert phases[0]['samples'][1]['resistance'] == 5.0


class TestTransformShotForAI:
    """Test complete shot transformation."""

    def test_full_transformation(self):
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

    def test_no_weight(self):
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

    def test_incomplete_shot(self):
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


class TestTimeToFirstWeight:
    """Test time_to_first_weight_s computation."""

    def test_computed_from_cup_weight(self):
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

    def test_none_when_no_weight_data(self):
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


class TestComputeComplianceMetrics:
    """Test compliance metrics computation."""

    def _make_shot(self, samples):
        """Build a minimal ShotData fixture with the given samples."""
        return ShotData(
            id='1',
            version=4,
            fields_mask=0xFF,
            sample_count=len(samples),
            sample_interval=100,
            profile_id='test',
            profile_name='Test Profile',
            timestamp=1640000000,
            rating=0,
            duration=25000,
            weight=None,
            samples=samples,
            phases=[],
        )

    def test_happy_path(self):
        """5 brew-phase samples with tp and tf, 2 preinfusion samples without.

        All 4 metrics should be non-None and mathematically correct.
        brew_phase_sample_count should equal 5.

        Sample math:
          - cp=7.0, tp=7.5 → error = cp - tp = -0.5 (undershoot 0.5)
          - RMSE = sqrt(5 * 0.25 / 5) = sqrt(0.25) = 0.5
          - max overshoot = max(0, max(-0.5)) = 0.0
          - max undershoot = max(0, max(0.5)) = 0.5
          - pf=2.0, tf=2.5 → flow error = pf - tf = -0.5
          - flow RMSE = sqrt(5 * 0.25 / 5) = 0.5
        """
        # 2 preinfusion samples (cp=0.5, below 50% threshold of 7.5 peak → excluded)
        preinfusion = [
            {'cp': 0.5, 'pf': 1.0},
            {'cp': 0.5, 'pf': 1.0},
        ]
        # 5 brew-phase samples at cp=7.0 with tp=7.5 and tf=2.5
        brew = [
            {'cp': 7.0, 'tp': 7.5, 'pf': 2.0, 'tf': 2.5},
            {'cp': 7.0, 'tp': 7.5, 'pf': 2.0, 'tf': 2.5},
            {'cp': 7.0, 'tp': 7.5, 'pf': 2.0, 'tf': 2.5},
            {'cp': 7.0, 'tp': 7.5, 'pf': 2.0, 'tf': 2.5},
            {'cp': 7.0, 'tp': 7.5, 'pf': 2.0, 'tf': 2.5},
        ]
        shot = self._make_shot(preinfusion + brew)
        metrics = compute_compliance_metrics(shot)

        assert metrics['brew_phase_sample_count'] == 5
        assert metrics['pressure_rmse_bar'] == 0.5
        assert metrics['max_pressure_overshoot_bar'] == 0.0
        assert metrics['max_pressure_undershoot_bar'] == 0.5
        assert metrics['flow_rmse_ml_s'] == 0.5

    def test_sparse_tp_fewer_than_3(self):
        """Only 2 brew-phase samples with tp → pressure metrics are None.

        Flow metrics may still compute if tf is present on those samples.
        """
        samples = [
            {'cp': 8.0, 'tp': 9.0, 'pf': 2.0, 'tf': 2.5},
            {'cp': 8.0, 'tp': 9.0, 'pf': 2.0, 'tf': 2.5},
        ]
        shot = self._make_shot(samples)
        metrics = compute_compliance_metrics(shot)

        assert metrics['pressure_rmse_bar'] is None
        assert metrics['max_pressure_overshoot_bar'] is None
        assert metrics['max_pressure_undershoot_bar'] is None
        # Only 2 tf samples also — flow RMSE is also None
        assert metrics['flow_rmse_ml_s'] is None

    def test_no_tp_at_all(self):
        """Brew-phase samples have no tp key → all pressure metrics None."""
        samples = [
            {'cp': 8.0, 'pf': 2.0},
            {'cp': 8.0, 'pf': 2.0},
            {'cp': 8.0, 'pf': 2.0},
            {'cp': 8.0, 'pf': 2.0},
            {'cp': 8.0, 'pf': 2.0},
        ]
        shot = self._make_shot(samples)
        metrics = compute_compliance_metrics(shot)

        assert metrics['pressure_rmse_bar'] is None
        assert metrics['max_pressure_overshoot_bar'] is None
        assert metrics['max_pressure_undershoot_bar'] is None
        # No tf either
        assert metrics['flow_rmse_ml_s'] is None

    def test_no_tf(self):
        """Brew-phase samples have tp but no tf → flow_rmse_ml_s is None.

        Pressure metrics should still be computed normally.
        """
        samples = [
            {'cp': 7.0, 'tp': 7.5, 'pf': 2.0},
            {'cp': 7.0, 'tp': 7.5, 'pf': 2.0},
            {'cp': 7.0, 'tp': 7.5, 'pf': 2.0},
            {'cp': 7.0, 'tp': 7.5, 'pf': 2.0},
            {'cp': 7.0, 'tp': 7.5, 'pf': 2.0},
        ]
        shot = self._make_shot(samples)
        metrics = compute_compliance_metrics(shot)

        assert metrics['flow_rmse_ml_s'] is None
        # Pressure metrics computed from the 5 tp samples
        assert metrics['pressure_rmse_bar'] == 0.5
        assert metrics['max_pressure_overshoot_bar'] == 0.0
        assert metrics['max_pressure_undershoot_bar'] == 0.5

    def test_zero_peak_cp(self):
        """All samples have cp=0.0 → brew_phase_sample_count=0, all metrics None."""
        samples = [
            {'cp': 0.0, 'tp': 9.0, 'pf': 0.0, 'tf': 2.5},
            {'cp': 0.0, 'tp': 9.0, 'pf': 0.0, 'tf': 2.5},
            {'cp': 0.0, 'tp': 9.0, 'pf': 0.0, 'tf': 2.5},
        ]
        shot = self._make_shot(samples)
        metrics = compute_compliance_metrics(shot)

        assert metrics['brew_phase_sample_count'] == 0
        assert metrics['pressure_rmse_bar'] is None
        assert metrics['max_pressure_overshoot_bar'] is None
        assert metrics['max_pressure_undershoot_bar'] is None
        assert metrics['flow_rmse_ml_s'] is None

    def test_brew_phase_filter(self):
        """Brew-phase filter excludes bloom samples using peak * 0.5 threshold.

        3 bloom samples at cp=0.5, 5 brew samples at cp=7.5.
        Peak = 7.5, threshold = 3.75.
        Only the 5 brew samples (cp >= 3.75) are included.
        """
        bloom = [
            {'cp': 0.5, 'tp': 0.5, 'pf': 1.0, 'tf': 1.0},
            {'cp': 0.5, 'tp': 0.5, 'pf': 1.0, 'tf': 1.0},
            {'cp': 0.5, 'tp': 0.5, 'pf': 1.0, 'tf': 1.0},
        ]
        brew = [
            {'cp': 7.5, 'tp': 7.5, 'pf': 2.0, 'tf': 2.0},
            {'cp': 7.5, 'tp': 7.5, 'pf': 2.0, 'tf': 2.0},
            {'cp': 7.5, 'tp': 7.5, 'pf': 2.0, 'tf': 2.0},
            {'cp': 7.5, 'tp': 7.5, 'pf': 2.0, 'tf': 2.0},
            {'cp': 7.5, 'tp': 7.5, 'pf': 2.0, 'tf': 2.0},
        ]
        shot = self._make_shot(bloom + brew)
        metrics = compute_compliance_metrics(shot)

        # Only the 5 brew samples should be used
        assert metrics['brew_phase_sample_count'] == 5
        # cp == tp for brew samples → error=0 → RMSE=0.0, no overshoot, no undershoot
        assert metrics['pressure_rmse_bar'] == 0.0
        assert metrics['max_pressure_overshoot_bar'] == 0.0
        assert metrics['max_pressure_undershoot_bar'] == 0.0
        # pf == tf for brew samples → flow RMSE=0.0
        assert metrics['flow_rmse_ml_s'] == 0.0

    def test_flush_cleaning_shot_undershoot(self):
        """Flush/cleaning shot: actual pressure far below profile target.

        Samples with cp≈2.0, tp≈7.5 → undershoot ≈ 5.5 bar.
        Should not crash.
        """
        samples = [
            {'cp': 2.0, 'tp': 7.5, 'pf': 3.0},
            {'cp': 2.0, 'tp': 7.5, 'pf': 3.0},
            {'cp': 2.0, 'tp': 7.5, 'pf': 3.0},
            {'cp': 2.0, 'tp': 7.5, 'pf': 3.0},
            {'cp': 2.0, 'tp': 7.5, 'pf': 3.0},
        ]
        shot = self._make_shot(samples)
        metrics = compute_compliance_metrics(shot)

        # Error per sample = cp - tp = 2.0 - 7.5 = -5.5 (pure undershoot)
        assert metrics['max_pressure_undershoot_bar'] == 5.5
        assert metrics['max_pressure_overshoot_bar'] == 0.0
        # RMSE = sqrt(5 * 5.5^2 / 5) = 5.5
        assert metrics['pressure_rmse_bar'] == 5.5
        # No crash
        assert metrics['brew_phase_sample_count'] == 5
