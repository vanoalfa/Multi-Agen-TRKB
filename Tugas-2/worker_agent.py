import asyncio
import random

class WorkerAgent:
    """WorkerAgent: memberikan proposal dan mengeksekusi tugas"""

    def __init__(self, jid: str, skill: float = 1.0, p_fail: float = 0.1, config: dict = None):
        self.jid = jid
        self.skill = skill
        self.p_fail = p_fail
        self.config = config or {}

    async def on_cfp(self, task: dict):
        """Menghitung proposal berdasarkan formula dari PDF"""
        base_cost = task.get('base_cost', 100.0)
        base_time = task.get('base_time', 5.0)
        net_delay = random.uniform(0, 1)
        cost = base_cost / self.skill
        duration = base_time / self.skill + net_delay
        score_prop = 1.0 / (1.0 + cost + duration)

        proposal = {
            'worker': self.jid,
            'cost': cost,
            'duration': duration,
            'score_prop': score_prop
        }
        await asyncio.sleep(random.uniform(0, 0.5))
        return proposal

    async def execute(self, task: dict):
        """Menjalankan tugas dan mengembalikan status"""
        work_time = task.get('base_time', 5.0) / self.skill
        await asyncio.sleep(work_time)
        if random.random() < self.p_fail:
            return {'status': 'fail', 'reason': 'simulated_failure'}
        return {'status': 'success', 'result': 'ok'}