from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from typing import Dict, Deque, Optional

from ursina import Ursina, Entity, Vec3, time, color

from .sim import MRIQueueSim

@dataclass
class Layout:
    entry: Vec3 = Vec3(-10, 0.3, 0)
    scan_spot: Vec3 = Vec3(10, 0.3, 0)
    wait_spots: tuple = tuple(Vec3(-7 + i*1.5, 0.3, 0) for i in range(12))

class MRI3DViz:
    def __init__(self, sim: MRIQueueSim):
        self.sim = sim
        self.layout = Layout()

        self.entities: Dict[int, Entity] = {}
        self.queue: Deque[int] = deque()
        self.in_scan: Optional[int] = None

        # Piso
        Entity(model="plane", scale=40, color=color.light_gray)
        # Resonador (bloque)
        Entity(model="cube", position=self.layout.scan_spot + Vec3(0, 0.6, 0), scale=(2.5, 1.2, 2.5), color=color.azure)
        # Entrada (bloque)
        Entity(model="cube", position=self.layout.entry + Vec3(0, 0.6, 0), scale=(1.2, 1.2, 1.2), color=color.orange)

        # cartelitos mínimos
        Entity(model='quad', position=self.layout.entry + Vec3(0,2,0), scale=2, color=color.orange)
        Entity(model='quad', position=self.layout.scan_spot + Vec3(0,2,0), scale=2, color=color.azure)

    def _spawn(self, pid: int):
        e = Entity(model="sphere", scale=0.55, color=color.white, position=self.layout.entry)
        self.entities[pid] = e
        self.queue.append(pid)

    def _start_scan(self, pid: int):
        if pid in self.queue:
            self.queue.remove(pid)
        self.in_scan = pid

    def _end_scan(self, pid: int):
        ent = self.entities.get(pid)
        if ent:
            ent.disable()
        if self.in_scan == pid:
            self.in_scan = None

    def _no_show(self, pid: int):
        ent = self.entities.get(pid)
        if ent:
            ent.color = color.red
            ent.disable()

    def consume_events(self):
        while self.sim.events and self.sim.events[0][0] <= self.sim.env.now:
            _, et, pid = self.sim.events.popleft()
            if et == "arrive":
                self._spawn(pid)
            elif et == "start_scan":
                self._start_scan(pid)
            elif et == "end_scan":
                self._end_scan(pid)
            elif et == "no_show":
                self._no_show(pid)

    def animate(self):
        # mover cola
        for idx, pid in enumerate(list(self.queue)[:len(self.layout.wait_spots)]):
            target = self.layout.wait_spots[idx]
            ent = self.entities[pid]
            ent.position = ent.position.lerp(target, 6 * time.dt)

        # mover en escaneo
        if self.in_scan is not None and self.in_scan in self.entities:
            ent = self.entities[self.in_scan]
            ent.position = ent.position.lerp(self.layout.scan_spot, 6 * time.dt)

def run_with_viz(sim: MRIQueueSim, steps_per_frame: int = 2):
    app = Ursina()
    viz = MRI3DViz(sim)

    def update():
        # avanzar simulación "en trocitos"
        for _ in range(steps_per_frame):
            try:
                sim.env.step()
            except Exception:
                # terminó la simulación
                return
        viz.consume_events()
        viz.animate()

    app.run()
