from dataclasses import dataclass
import json
from pathlib import Path

@dataclass
class SimConfig:
    seed: int = 42

    # Llegadas (minutos)
    arrival_mean_min: float = 8.0   # promedio entre llegadas (min)
    arrival_mode: str = "poisson"   # "poisson" o "schedule" (futuro)

    # Servicio (minutos)
    scan_mean_min: float = 25.0
    scan_sd_min: float = 6.0        # si usás normal truncada (opcional)
    service_dist: str = "exp"       # "exp" o "normal_trunc"

    # Recursos
    mri_capacity: int = 1

    # Simulación
    sim_duration_min: float = 8 * 60   # 8 horas
    warmup_min: float = 30.0           # descartar métricas iniciales

    # No-shows / abandono (futuro simple)
    no_show_rate: float = 0.0

    # Visual
    viz_speed_steps_per_frame: int = 2  # cuánto avanza SimPy por frame

def load_config(path: str | Path) -> SimConfig:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return SimConfig(**data)
