from __future__ import annotations
import simpy
import random
from dataclasses import dataclass
from collections import deque
from typing import Deque, Tuple, Optional
from .config import SimConfig

Event = Tuple[float, str, int]  # (sim_time, event_type, patient_id)

@dataclass
class PatientRecord:
    pid: int
    arrival: float
    start_scan: Optional[float] = None
    end_scan: Optional[float] = None
    no_show: bool = False

class MRIQueueSim:
    def __init__(self, env: simpy.Environment, cfg: SimConfig):
        self.env = env
        self.cfg = cfg
        random.seed(cfg.seed)

        self.mri = simpy.Resource(env, capacity=cfg.mri_capacity)

        self.events: Deque[Event] = deque()
        self.records: dict[int, PatientRecord] = {}

        self._pid = 0

        # Para utilización: acumulamos tiempo ocupado por servidor total
        self.busy_time = 0.0
        self._last_start_busy = None
        self._in_service = 0

    def log(self, event_type: str, pid: int):
        self.events.append((self.env.now, event_type, pid))

    def _maybe_start_busy(self):
        if self._in_service == 0:
            self._last_start_busy = self.env.now
        self._in_service += 1

    def _maybe_end_busy(self):
        self._in_service -= 1
        if self._in_service == 0 and self._last_start_busy is not None:
            self.busy_time += self.env.now - self._last_start_busy
            self._last_start_busy = None

    def service_time(self) -> float:
        if self.cfg.service_dist == "exp":
            return random.expovariate(1.0 / self.cfg.scan_mean_min)
        # normal truncada a > 1 min
        t = random.gauss(self.cfg.scan_mean_min, self.cfg.scan_sd_min)
        return max(1.0, t)

    def interarrival_time(self) -> float:
        # Poisson => interarrivals ~ Exp(mean)
        return random.expovariate(1.0 / self.cfg.arrival_mean_min)

    def patient(self, pid: int):
        rec = PatientRecord(pid=pid, arrival=self.env.now)
        self.records[pid] = rec
        self.log("arrive", pid)

        # No-show (si lo querés)
        if self.cfg.no_show_rate > 0 and random.random() < self.cfg.no_show_rate:
            rec.no_show = True
            self.log("no_show", pid)
            return

        with self.mri.request() as req:
            yield req
            rec.start_scan = self.env.now
            self.log("start_scan", pid)

            self._maybe_start_busy()
            st = self.service_time()
            yield self.env.timeout(st)
            self._maybe_end_busy()

            rec.end_scan = self.env.now
            self.log("end_scan", pid)

    def arrivals(self):
        while True:
            self._pid += 1
            pid = self._pid
            self.env.process(self.patient(pid))
            yield self.env.timeout(self.interarrival_time())

def run_sim(cfg: SimConfig) -> MRIQueueSim:
    env = simpy.Environment()
    sim = MRIQueueSim(env, cfg)
    env.process(sim.arrivals())

    # correr
    env.run(until=cfg.sim_duration_min)

    # cerrar utilización si quedó ocupado al final
    if sim._in_service > 0 and sim._last_start_busy is not None:
        sim.busy_time += cfg.sim_duration_min - sim._last_start_busy
        sim._last_start_busy = None
        sim._in_service = 0

    return sim
