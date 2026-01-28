import argparse
import json
from pathlib import Path

import simpy

from .config import SimConfig, load_config
from .sim import MRIQueueSim
from .metrics import summarize
from .viz_ursina import run_with_viz

def build_sim(cfg: SimConfig) -> MRIQueueSim:
    env = simpy.Environment()
    sim = MRIQueueSim(env, cfg)
    env.process(sim.arrivals())
    return sim

def run_headless(cfg: SimConfig) -> dict:
    import simpy
    env = simpy.Environment()
    sim = MRIQueueSim(env, cfg)
    env.process(sim.arrivals())
    env.run(until=cfg.sim_duration_min)

    # cerrar busy si queda abierto
    if sim._in_service > 0 and sim._last_start_busy is not None:
        sim.busy_time += cfg.sim_duration_min - sim._last_start_busy
        sim._last_start_busy = None
        sim._in_service = 0

    return summarize(sim, cfg)

def main():
    p = argparse.ArgumentParser(prog="mri-sim")
    p.add_argument("--config", type=str, default="", help="Path a config JSON")
    p.add_argument("--viz", action="store_true", help="Ejecutar con visual 3D (Ursina)")
    args = p.parse_args()

    cfg = load_config(args.config) if args.config else SimConfig()

    if args.viz:
        sim = build_sim(cfg)
        # la sim corre paso a paso dentro de Ursina update()
        run_with_viz(sim, steps_per_frame=cfg.viz_speed_steps_per_frame)
    else:
        out = run_headless(cfg)
        print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
