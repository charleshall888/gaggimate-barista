"""Transform shot data to AI-friendly format.

This module converts raw binary shot data into a structured format
optimized for AI analysis and natural language processing.
"""

from math import ceil, sqrt
from typing import TypedDict, Optional
from gaggimate_mcp.parsers.shot import ShotData

MAX_SAMPLES_PER_PHASE = 25


class TemperatureSummary(TypedDict):
    """Temperature summary statistics."""
    min_c: float
    max_c: float
    avg_c: float
    target_avg_c: float


class PressureSummary(TypedDict):
    """Pressure summary statistics."""
    min_bar: float
    max_bar: float
    avg_bar: float
    peak_time_s: float


class FlowSummary(TypedDict):
    """Flow summary statistics."""
    total_volume_ml: float
    avg_flow_ml_s: float
    peak_flow_ml_s: float
    time_to_first_drip_s: Optional[float]
    time_to_first_weight_s: Optional[float]


class ExtractionSummary(TypedDict):
    """Extraction timing summary."""
    preinfusion_time_s: float
    main_extraction_time_s: float
    total_time_s: float


class ShotSummary(TypedDict):
    """Complete shot summary statistics."""
    temperature: TemperatureSummary
    pressure: PressureSummary
    flow: FlowSummary
    extraction: ExtractionSummary


class ComplianceMetrics(TypedDict):
    """Profile compliance metrics comparing actual vs target pump behaviour."""
    pressure_rmse_bar: Optional[float]
    max_pressure_overshoot_bar: Optional[float]
    max_pressure_undershoot_bar: Optional[float]
    flow_rmse_ml_s: Optional[float]
    brew_phase_sample_count: int


class TransformedSample(TypedDict):
    """Transformed sample data point."""
    time_seconds: float
    temperature_c: float
    pressure_bar: float
    flow_ml_s: float
    weight_g: float
    resistance: float


class PhaseData(TypedDict):
    """Phase data for AI analysis."""
    name: str
    phase_number: int
    start_time_seconds: float
    duration_seconds: float
    sample_count: int
    avg_temperature_c: float
    avg_pressure_bar: float
    total_flow_ml: float
    samples: list[TransformedSample]


class TransformedShot(TypedDict):
    """Transformed shot data for AI analysis."""
    shot_id: str
    profile_name: str
    profile_id: str
    timestamp: int
    duration_seconds: float
    final_weight_g: Optional[float]
    summary: ShotSummary
    phases: list[PhaseData]
    compliance_metrics: ComplianceMetrics


def calculate_total_volume(samples: list[dict], interval_ms: int) -> float:
    """Calculate total volume from flow samples.

    Args:
        samples: List of sample dictionaries with 'pf' (puck flow) field
        interval_ms: Sample interval in milliseconds

    Returns:
        Total volume in ml, rounded to 1 decimal place
    """
    total_volume = 0.0
    interval_seconds = interval_ms / 1000.0

    for sample in samples:
        flow = sample.get('pf', 0.0)  # ml/s
        total_volume += flow * interval_seconds  # ml

    return round(total_volume * 10) / 10


def trim_trailing_artifacts(samples: list[dict]) -> list[dict]:
    """Remove trailing post-pump-stop artifact samples.

    After the pump stops, firmware continues recording for ~0.5-1s.
    These trailing samples show pressure decaying toward 0 and flow at 0,
    which distort summary stats and mislead analysis.

    Walks backwards and removes contiguous trailing samples where
    pf (puck flow) <= 0.05 AND cp (current pressure) < 1.0.
    Always preserves at least 1 sample.

    Args:
        samples: List of raw sample dicts

    Returns:
        Trimmed list (may be same object if no trimming needed)
    """
    if len(samples) <= 1:
        return samples

    trim_from = len(samples)
    for i in range(len(samples) - 1, 0, -1):  # stop at index 1 to preserve at least 1
        s = samples[i]
        if s.get('pf', 0.0) <= 0.05 and s.get('cp', 0.0) < 1.0:
            trim_from = i
        else:
            break

    return samples[:trim_from] if trim_from < len(samples) else samples


def select_representative_samples(
    phase_samples: list[dict], sample_interval: int
) -> list['TransformedSample']:
    """Select representative samples from a phase for AI analysis.

    Adaptive downsampling: caps output at MAX_SAMPLES_PER_PHASE (25).
    Short phases use step=2 (current behavior). Long phases increase
    the step to stay within budget.

    Args:
        phase_samples: Raw samples for this phase
        sample_interval: Sample interval in ms (unused, reserved)

    Returns:
        List of TransformedSample dicts
    """
    if not phase_samples:
        return []

    step = max(2, ceil(len(phase_samples) / MAX_SAMPLES_PER_PHASE))
    indices = range(0, len(phase_samples), step)

    result: list[TransformedSample] = []
    for idx in indices:
        sample = phase_samples[idx]
        result.append(TransformedSample(
            time_seconds=round((sample.get('t', 0.0) / 1000.0) * 10) / 10,
            temperature_c=round(sample.get('ct', 0.0) * 10) / 10,
            pressure_bar=round(sample.get('cp', 0.0) * 10) / 10,
            flow_ml_s=round(sample.get('pf', 0.0) * 10) / 10,
            weight_g=round(sample.get('v', 0.0) * 10) / 10,
            resistance=round(sample.get('pr', 0.0) * 100) / 100,
        ))

    return result


def _get_brew_phase_samples(samples: list[dict]) -> list[dict]:
    """Return samples that belong to the brew (main extraction) phase.

    Identifies the brew phase using a 50% peak-pressure threshold:
    any sample whose current pressure ('cp') is at least half the
    overall peak pressure is considered a brew-phase sample.

    Args:
        samples: Full list of raw sample dicts for a shot.

    Returns:
        Filtered list of brew-phase samples.  Returns an empty list
        when there are no samples or when peak pressure is zero.
    """
    if not samples:
        return []

    peak_cp = max(s.get('cp', 0.0) for s in samples)
    if peak_cp == 0:
        return []

    threshold = peak_cp * 0.5
    return [s for s in samples if s.get('cp', 0.0) >= threshold]


def compute_compliance_metrics(shot: ShotData) -> ComplianceMetrics:
    """Compute profile-compliance metrics for a shot.

    Compares actual pump behaviour ('cp' current pressure, 'pf' puck flow)
    against the profile targets ('tp' target pressure, 'tf' target flow)
    across brew-phase samples only.

    Args:
        shot: Parsed shot data.

    Returns:
        ComplianceMetrics TypedDict.  Always populated — degenerate cases
        (no brew samples, fewer than 3 samples with targets) produce None
        for the metric fields but brew_phase_sample_count is always set.
    """
    brew_samples = _get_brew_phase_samples(shot.samples)
    brew_phase_sample_count = len(brew_samples)

    # Pressure metrics — require at least 3 samples that carry a target pressure
    brew_samples_with_tp = [s for s in brew_samples if 'tp' in s]

    if len(brew_samples_with_tp) < 3:
        pressure_rmse_bar = None
        max_pressure_overshoot_bar = None
        max_pressure_undershoot_bar = None
    else:
        errors = [s['cp'] - s['tp'] for s in brew_samples_with_tp]
        pressure_rmse_bar = round(sqrt(sum(e ** 2 for e in errors) / len(errors)), 2)
        max_pressure_overshoot_bar = round(max(0.0, max(e for e in errors)), 2)
        max_pressure_undershoot_bar = round(max(0.0, max(-e for e in errors)), 2)

    # Flow metric — require at least 3 samples that carry a target flow
    brew_samples_with_tf = [s for s in brew_samples if 'tf' in s]

    if len(brew_samples_with_tf) < 3:
        flow_rmse_ml_s = None
    else:
        flow_errors = [s.get('pf', 0.0) - s['tf'] for s in brew_samples_with_tf]
        flow_rmse_ml_s = round(sqrt(sum(e ** 2 for e in flow_errors) / len(flow_errors)), 2)

    return ComplianceMetrics(
        pressure_rmse_bar=pressure_rmse_bar,
        max_pressure_overshoot_bar=max_pressure_overshoot_bar,
        max_pressure_undershoot_bar=max_pressure_undershoot_bar,
        flow_rmse_ml_s=flow_rmse_ml_s,
        brew_phase_sample_count=brew_phase_sample_count,
    )


def calculate_summary(shot: ShotData) -> ShotSummary:
    """Calculate summary statistics for shot.

    Args:
        shot: Parsed shot data

    Returns:
        Summary statistics
    """
    samples = shot.samples

    # Trim trailing post-pump artifacts for clean stats (skip for incomplete shots)
    clean_samples = samples if shot.incomplete else trim_trailing_artifacts(samples)

    # Extract values from clean samples for averages
    temperatures = [s['ct'] for s in clean_samples if 'ct' in s]
    target_temps = [s['tt'] for s in clean_samples if 'tt' in s]
    pressures = [s['cp'] for s in clean_samples if 'cp' in s]
    flows = [s['pf'] for s in clean_samples if 'pf' in s]
    times = [s.get('t', 0.0) / 1000.0 for s in clean_samples]  # Convert to seconds

    # Temperature summary
    temp_summary = TemperatureSummary(
        min_c=round(min(temperatures) * 10) / 10 if temperatures else 0.0,
        max_c=round(max(temperatures) * 10) / 10 if temperatures else 0.0,
        avg_c=round(sum(temperatures) / len(temperatures) * 10) / 10 if temperatures else 0.0,
        target_avg_c=round(sum(target_temps) / len(target_temps) * 10) / 10 if target_temps else 0.0,
    )

    # Pressure summary
    peak_pressure = max(pressures) if pressures else 0.0
    peak_pressure_index = pressures.index(peak_pressure) if pressures and peak_pressure > 0 else 0
    peak_time = times[peak_pressure_index] if peak_pressure_index < len(times) else 0.0

    pressure_summary = PressureSummary(
        min_bar=round(min(pressures) * 10) / 10 if pressures else 0.0,
        max_bar=round(max(pressures) * 10) / 10 if pressures else 0.0,
        avg_bar=round(sum(pressures) / len(pressures) * 10) / 10 if pressures else 0.0,
        peak_time_s=round(peak_time * 10) / 10,
    )

    # Flow summary — use clean samples for volume/avg/peak
    total_volume = calculate_total_volume(clean_samples, shot.sample_interval)
    avg_flow = round(sum(flows) / len(flows) * 10) / 10 if flows else 0.0
    peak_flow = round(max(flows) * 10) / 10 if flows else 0.0

    # Find time to first drip (first non-zero flow) — use all samples
    all_times = [s.get('t', 0.0) / 1000.0 for s in samples]
    time_to_first_drip = None
    for i, sample in enumerate(samples):
        if sample.get('pf', 0.0) > 0.0:
            time_to_first_drip = round(all_times[i] * 10) / 10 if i < len(all_times) else None
            break

    # Find time to first weight (first non-zero cup weight) — use all samples
    time_to_first_weight = None
    for i, sample in enumerate(samples):
        weight = sample.get('v', 0.0)
        if weight is not None and weight > 0.0:
            time_to_first_weight = round(all_times[i] * 10) / 10 if i < len(all_times) else None
            break

    flow_summary = FlowSummary(
        total_volume_ml=total_volume,
        avg_flow_ml_s=avg_flow,
        peak_flow_ml_s=peak_flow,
        time_to_first_drip_s=time_to_first_drip,
        time_to_first_weight_s=time_to_first_weight,
    )

    # Extraction timing
    # Preinfusion: time from start until pressure reaches 50% of max
    preinfusion_time = 0.0
    if peak_pressure > 0:
        threshold = peak_pressure * 0.5
        for i, pressure in enumerate(pressures):
            if pressure >= threshold:
                preinfusion_time = times[i] if i < len(times) else 0.0
                break

    total_time = shot.duration / 1000.0  # Convert to seconds
    main_extraction_time = max(0.0, total_time - preinfusion_time)

    extraction_summary = ExtractionSummary(
        preinfusion_time_s=round(preinfusion_time * 10) / 10,
        main_extraction_time_s=round(main_extraction_time * 10) / 10,
        total_time_s=round(total_time * 10) / 10,
    )

    return ShotSummary(
        temperature=temp_summary,
        pressure=pressure_summary,
        flow=flow_summary,
        extraction=extraction_summary,
    )


def process_phases(shot: ShotData) -> list[PhaseData]:
    """Process shot phases for AI analysis.

    Args:
        shot: Parsed shot data

    Returns:
        List of phase data with statistics and representative samples
    """
    phases: list[PhaseData] = []
    samples = shot.samples

    if not samples:
        return phases

    # If shot has defined phases, process each one
    if shot.phases:
        num_phases = len(shot.phases)
        for i, phase in enumerate(shot.phases):
            start_index = phase.sample_index
            end_index = shot.phases[i + 1].sample_index if i + 1 < num_phases else len(samples)
            phase_samples = samples[start_index:end_index]

            if not phase_samples:
                continue

            is_last_phase = (i == num_phases - 1)

            # Trim trailing artifacts from last phase only (skip for incomplete shots)
            stats_samples = phase_samples
            if is_last_phase and not shot.incomplete:
                stats_samples = trim_trailing_artifacts(phase_samples)

            # Calculate phase statistics from (possibly trimmed) samples
            temperatures = [s['ct'] for s in stats_samples if 'ct' in s]
            pressures = [s['cp'] for s in stats_samples if 'cp' in s]

            avg_temp = round(sum(temperatures) / len(temperatures) * 10) / 10 if temperatures else 0.0
            avg_pressure = round(sum(pressures) / len(pressures) * 10) / 10 if pressures else 0.0
            total_flow = calculate_total_volume(stats_samples, shot.sample_interval)

            representative_samples = select_representative_samples(
                stats_samples, shot.sample_interval
            )

            start_time = phase_samples[0].get('t', 0.0) / 1000.0
            end_time = phase_samples[-1].get('t', 0.0) / 1000.0
            duration = max(0.0, end_time - start_time + shot.sample_interval / 1000.0)

            phases.append(PhaseData(
                name=phase.phase_name,
                phase_number=phase.phase_number,
                start_time_seconds=round(start_time * 10) / 10,
                duration_seconds=round(duration * 10) / 10,
                sample_count=len(stats_samples),
                avg_temperature_c=avg_temp,
                avg_pressure_bar=avg_pressure,
                total_flow_ml=total_flow,
                samples=representative_samples,
            ))
    else:
        # No phases defined - create single 'extraction' phase
        # Trim trailing artifacts (skip for incomplete shots)
        clean_samples = samples if shot.incomplete else trim_trailing_artifacts(samples)

        temperatures = [s.get('ct', 0.0) for s in clean_samples]
        pressures = [s.get('cp', 0.0) for s in clean_samples]

        avg_temp = round(sum(temperatures) / len(temperatures) * 10) / 10 if temperatures else 0.0
        avg_pressure = round(sum(pressures) / len(pressures) * 10) / 10 if pressures else 0.0
        total_flow = calculate_total_volume(clean_samples, shot.sample_interval)

        representative_samples = select_representative_samples(
            clean_samples, shot.sample_interval
        )

        phases.append(PhaseData(
            name='extraction',
            phase_number=0,
            start_time_seconds=0.0,
            duration_seconds=round(shot.duration / 1000.0 * 10) / 10,
            sample_count=len(clean_samples),
            avg_temperature_c=avg_temp,
            avg_pressure_bar=avg_pressure,
            total_flow_ml=total_flow,
            samples=representative_samples,
        ))

    return phases


def transform_shot_for_ai(shot: ShotData) -> TransformedShot:
    """Transform shot data for AI analysis.

    Converts raw binary shot data into a structured format optimized
    for AI analysis, including summary statistics and phase breakdowns.

    Args:
        shot: Parsed shot data

    Returns:
        Transformed shot data
    """
    summary = calculate_summary(shot)
    phases = process_phases(shot)
    compliance = compute_compliance_metrics(shot)

    return TransformedShot(
        shot_id=shot.id,
        profile_name=shot.profile_name,
        profile_id=shot.profile_id,
        timestamp=shot.timestamp,
        duration_seconds=round(shot.duration / 1000.0 * 10) / 10,
        final_weight_g=shot.weight,
        summary=summary,
        phases=phases,
        compliance_metrics=compliance,
    )
