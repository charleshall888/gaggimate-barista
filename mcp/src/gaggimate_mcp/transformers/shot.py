"""Transform shot data to AI-friendly format.

This module converts raw binary shot data into a structured format
optimized for AI analysis and natural language processing.
"""

from typing import TypedDict, Optional
from gaggimate_mcp.parsers.shot import ShotData


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


class TransformedSample(TypedDict):
    """Transformed sample data point."""
    time_seconds: float
    temperature_c: float
    pressure_bar: float
    flow_ml_s: float
    weight_g: float


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


def calculate_summary(shot: ShotData) -> ShotSummary:
    """Calculate summary statistics for shot.

    Args:
        shot: Parsed shot data

    Returns:
        Summary statistics
    """
    samples = shot.samples

    # Extract values - only include samples that have the measurement
    temperatures = [s['ct'] for s in samples if 'ct' in s]
    target_temps = [s['tt'] for s in samples if 'tt' in s]
    pressures = [s['cp'] for s in samples if 'cp' in s]
    flows = [s['pf'] for s in samples if 'pf' in s]
    times = [s.get('t', 0.0) / 1000.0 for s in samples]  # Convert to seconds

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

    # Flow summary
    total_volume = calculate_total_volume(samples, shot.sample_interval)
    avg_flow = round(sum(flows) / len(flows) * 10) / 10 if flows else 0.0
    peak_flow = round(max(flows) * 10) / 10 if flows else 0.0

    # Find time to first drip (first non-zero flow)
    time_to_first_drip = None
    for i, flow in enumerate(flows):
        if flow > 0.0:
            time_to_first_drip = round(times[i] * 10) / 10 if i < len(times) else None
            break

    flow_summary = FlowSummary(
        total_volume_ml=total_volume,
        avg_flow_ml_s=avg_flow,
        peak_flow_ml_s=peak_flow,
        time_to_first_drip_s=time_to_first_drip,
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
        for i, phase in enumerate(shot.phases):
            start_index = phase.sample_index
            end_index = shot.phases[i + 1].sample_index if i + 1 < len(shot.phases) else len(samples)
            phase_samples = samples[start_index:end_index]

            if not phase_samples:
                continue

            # Calculate phase statistics - only include samples that have the measurement
            temperatures = [s['ct'] for s in phase_samples if 'ct' in s]
            pressures = [s['cp'] for s in phase_samples if 'cp' in s]

            avg_temp = round(sum(temperatures) / len(temperatures) * 10) / 10 if temperatures else 0.0
            avg_pressure = round(sum(pressures) / len(pressures) * 10) / 10 if pressures else 0.0
            total_flow = calculate_total_volume(phase_samples, shot.sample_interval)

            # Select every other sample for good curve resolution without context bloat
            representative_samples: list[TransformedSample] = []
            indices = list(range(0, len(phase_samples), 2))
            unique_indices = sorted(set(indices))

            for idx in unique_indices:
                if idx < len(phase_samples):
                    sample = phase_samples[idx]
                    representative_samples.append(TransformedSample(
                        time_seconds=round((sample.get('t', 0.0) / 1000.0) * 10) / 10,
                        temperature_c=round(sample.get('ct', 0.0) * 10) / 10,
                        pressure_bar=round(sample.get('cp', 0.0) * 10) / 10,
                        flow_ml_s=round(sample.get('pf', 0.0) * 10) / 10,
                        weight_g=round(sample.get('v', 0.0) * 10) / 10,
                    ))

            start_time = phase_samples[0].get('t', 0.0) / 1000.0
            end_time = phase_samples[-1].get('t', 0.0) / 1000.0
            duration = max(0.0, end_time - start_time + shot.sample_interval / 1000.0)

            phases.append(PhaseData(
                name=phase.phase_name,
                phase_number=phase.phase_number,
                start_time_seconds=round(start_time * 10) / 10,
                duration_seconds=round(duration * 10) / 10,
                sample_count=len(phase_samples),
                avg_temperature_c=avg_temp,
                avg_pressure_bar=avg_pressure,
                total_flow_ml=total_flow,
                samples=representative_samples,
            ))
    else:
        # No phases defined - create single 'extraction' phase
        temperatures = [s.get('ct', 0.0) for s in samples]
        pressures = [s.get('cp', 0.0) for s in samples]

        avg_temp = round(sum(temperatures) / len(temperatures) * 10) / 10 if temperatures else 0.0
        avg_pressure = round(sum(pressures) / len(pressures) * 10) / 10 if pressures else 0.0
        total_flow = calculate_total_volume(samples, shot.sample_interval)

        # Select every other sample for good curve resolution without context bloat
        representative_samples: list[TransformedSample] = []
        indices = list(range(0, len(samples), 2))
        unique_indices = sorted(set(indices))

        for idx in unique_indices:
            if idx < len(samples):
                sample = samples[idx]
                representative_samples.append(TransformedSample(
                    time_seconds=round((sample.get('t', 0.0) / 1000.0) * 10) / 10,
                    temperature_c=round(sample.get('ct', 0.0) * 10) / 10,
                    pressure_bar=round(sample.get('cp', 0.0) * 10) / 10,
                    flow_ml_s=round(sample.get('pf', 0.0) * 10) / 10,
                    weight_g=round(sample.get('v', 0.0) * 10) / 10,
                ))

        phases.append(PhaseData(
            name='extraction',
            phase_number=0,
            start_time_seconds=0.0,
            duration_seconds=round(shot.duration / 1000.0 * 10) / 10,
            sample_count=len(samples),
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

    return TransformedShot(
        shot_id=shot.id,
        profile_name=shot.profile_name,
        profile_id=shot.profile_id,
        timestamp=shot.timestamp,
        duration_seconds=round(shot.duration / 1000.0 * 10) / 10,
        final_weight_g=shot.weight,
        summary=summary,
        phases=phases,
    )
