from __future__ import annotations
import numpy as np
from .sim import MRIQueueSim
from .config import SimConfig

def summarize(sim: MRIQueueSim, cfg: SimConfig) -> dict:
    waits = []
    total_completed = 0
    for rec in sim.records.values():
        if rec.no_show:
            continue
        if rec.start_scan is None or rec.end_scan is None:
            continue

        # warmup: descartar pacientes que llegaron antes del warmup
        if rec.arrival < cfg.warmup_min:
            continue

        waits.append(rec.start_scan - rec.arrival)
        total_completed += 1

    waits_arr = np.array(waits, dtype=float) if waits else np.array([], dtype=float)

    sim_time_effective = max(0.0001, cfg.sim_duration_min - cfg.warmup_min)
    utilization = (sim.busy_time / (cfg.sim_duration_min * cfg.mri_capacity)) if cfg.mri_capacity > 0 else 0.0
    throughput_per_hour = (total_completed / sim_time_effective) * 60.0

    out = {
        "patients_total": len(sim.records),
        "patients_completed_after_warmup": total_completed,
        "wait_mean_min": float(waits_arr.mean()) if waits_arr.size else 0.0,
        "wait_p50_min": float(np.percentile(waits_arr, 50)) if waits_arr.size else 0.0,
        "wait_p95_min": float(np.percentile(waits_arr, 95)) if waits_arr.size else 0.0,
        "utilization_mri": float(utilization),
        "throughput_per_hour": float(throughput_per_hour),
    }
    return out
