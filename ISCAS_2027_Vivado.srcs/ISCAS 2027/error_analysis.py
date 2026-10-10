from typing import Dict

import numpy as np


def summarize_experiment_error(reference_voltage: np.ndarray, estimated_voltage: np.ndarray, reference_current: np.ndarray, estimated_current: np.ndarray) -> Dict[str, float]:
    v_err = np.asarray(estimated_voltage, dtype=np.float64) - np.asarray(reference_voltage, dtype=np.float64)
    i_err = np.asarray(estimated_current, dtype=np.float64) - np.asarray(reference_current, dtype=np.float64)

    return {
        "max_voltage_error": float(np.max(np.abs(v_err))),
        "rms_voltage_error": float(np.sqrt(np.mean(np.square(v_err)))),
        "mae_voltage_error": float(np.mean(np.abs(v_err))),
        "max_current_error": float(np.max(np.abs(i_err))),
        "rms_current_error": float(np.sqrt(np.mean(np.square(i_err)))),
        "mean_current_error": float(np.mean(np.abs(i_err))),
    }


def transient_error(reference_voltage: np.ndarray, estimated_voltage: np.ndarray, transient_mask: np.ndarray) -> Dict[str, float]:
    v_err = np.asarray(estimated_voltage, dtype=np.float64) - np.asarray(reference_voltage, dtype=np.float64)
    mask = np.asarray(transient_mask, dtype=bool)
    if mask.size == 0:
        return {"transient_max_abs_error": 0.0, "transient_rms_error": 0.0}
    return {
        "transient_max_abs_error": float(np.max(np.abs(v_err[mask]))),
        "transient_rms_error": float(np.sqrt(np.mean(np.square(v_err[mask])))),
    }


def error_budget_metrics(stale_refresh_counts: np.ndarray, refresh_threshold: float) -> Dict[str, float]:
    return {
        "refresh_events": int(np.sum(stale_refresh_counts > 0)),
        "mean_refresh_interval": float(np.mean(stale_refresh_counts[stale_refresh_counts > 0])) if np.any(stale_refresh_counts > 0) else 0.0,
        "threshold_exhaustion_count": int(np.sum(stale_refresh_counts >= refresh_threshold)),
    }
