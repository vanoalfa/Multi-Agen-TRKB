import asyncio
import random
from typing import Dict, List, Optional
from common import AssignmentHistoryEntry, Logger
from directory_agent import GLOBAL_DIRECTORY


class ManagerAgent:
    """ManagerAgent: mengatur alur Contract Net Protocol (CNP)"""

    def __init__(self, jid: str, config: Dict, logger: Logger, seed: Optional[int] = None):
        self.jid = jid
        self.config = config
        self.logger = logger
        self.assignment_history: Dict[str, List[Dict]] = {}
        self.reputation: Dict[str, float] = {}
        self.w_proposal = config['utility_weights']['w_proposal']
        self.w_rep = config['utility_weights']['w_rep']
        if seed is not None:
            random.seed(seed)

    # -----------------------------------------------------------
    # Inisialisasi reputasi awal semua worker
    # -----------------------------------------------------------
    def init_reputations(self, worker_jids: List[str]):
        init = self.config['reputation']['initial']
        for w in worker_jids:
            self.reputation[w] = init

    # -----------------------------------------------------------
    # Proses utama pengumuman task dan eksekusi CNP
    # -----------------------------------------------------------
    async def announce_task(self, task: Dict):
        workers = GLOBAL_DIRECTORY.find_workers()
        random.shuffle(workers)  # tambahkan ini
        print(f"[Manager] Mengumumkan {task['id']} ke {len(workers)} worker...")
        self.logger.log_event({'type': 'announce', 'task': task, 'workers': workers})

        # === Kirim Call for Proposal ke semua worker ===
        proposals = []
        bid_timeout = self.config['timeouts']['bid_timeout']
        tasks = [asyncio.create_task(self.send_call_for_proposal(w, task)) for w in workers]

        try:
            done, _ = await asyncio.wait(tasks, timeout=bid_timeout)
            for d in done:
                if not d.cancelled() and d.exception() is None:
                    result = d.result()
                    if result:
                        proposals.append(result)
        except Exception as e:
            print('[!] Error gathering proposals:', e)

        if not proposals:
            print(f"[Manager] Tidak ada proposal untuk task {task['id']}")
            self.logger.log_event({'type': 'no_proposal', 'task': task})
            return None

        # === Pilih pemenang ===
        winner = self.select_winner(task, proposals)
        print(f"[Manager] Pemenang task {task['id']}: {winner['worker']}")
        self.logger.log_event({'type': 'award', 'task': task, 'winner': winner['worker']})

        # Catat assignment
        self.assignment_history.setdefault(task['id'], []).append(
            AssignmentHistoryEntry(task_id=task['id'], worker_jid=winner['worker'], status='assigned').__dict__)

        # === Jalankan eksekusi oleh worker ===
        exec_timeout = self.config['timeouts']['exec_timeout']
        try:
            result = await asyncio.wait_for(self.send_execute(winner, task), timeout=exec_timeout)
        except asyncio.TimeoutError:
            result = {'status': 'fail', 'reason': 'timeout'}

        status = result.get('status', 'fail')

        if status == 'success':
            print(f"[Manager] {winner['worker']} berhasil menyelesaikan {task['id']}")
            self.assignment_history[task['id']].append(
                AssignmentHistoryEntry(task_id=task['id'], worker_jid=winner['worker'], status='success').__dict__)
            self.update_reputation(winner['worker'], True)
        else:
            print(f"[Manager] {winner['worker']} gagal ({result.get('reason', 'unknown')}) → reassign...")
            self.assignment_history[task['id']].append(
                AssignmentHistoryEntry(task_id=task['id'], worker_jid=winner['worker'],
                                       status='fail', reason=result.get('reason', 'unknown')).__dict__)
            self.update_reputation(winner['worker'], False)
            await self.reassign(task, exclude=[winner['worker']])

        # Simpan riwayat
        self.logger.log_event({
            'type': 'assignment_history_snapshot',
            'task_id': task['id'],
            'history': self.assignment_history[task['id']]
        })

        return status

    # -----------------------------------------------------------
    # Reassign jika gagal
    # -----------------------------------------------------------
    async def reassign(self, task: Dict, exclude: List[str]):
        workers = [w for w in GLOBAL_DIRECTORY.find_workers() if w not in exclude]
        if not workers:
            print(f"[Manager] Tidak ada worker tersisa untuk reassign {task['id']}")
            self.logger.log_event({'type': 'reassign_failed', 'task': task})
            return None

        print(f"🔁 [Manager] Reassign {task['id']} ke {len(workers)} worker (exclude={exclude})")

        proposals = []
        tasks = [asyncio.create_task(self.send_call_for_proposal(w, task)) for w in workers]
        try:
            done, _ = await asyncio.wait(tasks, timeout=self.config['timeouts']['bid_timeout'])
            for d in done:
                if not d.cancelled() and d.exception() is None:
                    result = d.result()
                    if result:
                        proposals.append(result)
        except Exception as e:
            print('[!] Error gathering proposals in reassign:', e)

        winner = self.select_winner(task, proposals)
        if not winner:
            print(f"[Manager] Tidak ada proposal saat reassign {task['id']}")
            self.logger.log_event({'type': 'reassign_no_proposal', 'task': task})
            return None

        print(f"[Manager] Pemenang reassign {task['id']}: {winner['worker']}")
        self.assignment_history.setdefault(task['id'], []).append(
            AssignmentHistoryEntry(task_id=task['id'], worker_jid=winner['worker'], status='reassigned').__dict__)

        try:
            result = await asyncio.wait_for(self.send_execute(winner, task),
                                            timeout=self.config['timeouts']['exec_timeout'])
        except asyncio.TimeoutError:
            result = {'status': 'fail', 'reason': 'timeout'}

        status = result.get('status', 'fail')
        if status == 'success':
            print(f"[Manager] {winner['worker']} sukses pada reassign {task['id']}")
            self.assignment_history[task['id']].append(
                AssignmentHistoryEntry(task_id=task['id'], worker_jid=winner['worker'], status='success').__dict__)
            self.update_reputation(winner['worker'], True)
        else:
            print(f"[Manager] {winner['worker']} gagal lagi ({result.get('reason', 'unknown')})")
            self.assignment_history[task['id']].append(
                AssignmentHistoryEntry(task_id=task['id'], worker_jid=winner['worker'],
                                       status='fail', reason=result.get('reason', 'unknown')).__dict__)
            self.update_reputation(winner['worker'], False)

            # Rekursif reassign ke worker lain
            failed = [entry['worker_jid'] for entry in self.assignment_history[task['id']] if entry['status'] == 'fail']
            return await self.reassign(task, exclude=failed)

        return status

    # -----------------------------------------------------------
    # Update reputasi worker
    # -----------------------------------------------------------
    def update_reputation(self, worker_jid: str, success: bool):
        delta = self.config['reputation']['delta_success'] if success else self.config['reputation']['delta_fail']
        new_val = max(0.0, min(1.0, self.reputation.get(worker_jid, 0.5) + delta))
        self.reputation[worker_jid] = new_val
        state = "⬆️" if success else "⬇️"
        print(f"   {state} Reputasi {worker_jid}: {self.reputation[worker_jid]:.2f}")

    # -----------------------------------------------------------
    # Seleksi pemenang
    # -----------------------------------------------------------
    def select_winner(self, task: Dict, proposals: List[Dict]) -> Optional[Dict]:
        if not proposals:
            return None
        utilities = []
        for p in proposals:
            rep = self.reputation.get(p['worker'], self.config['reputation']['initial'])
            util = self.w_proposal * p['score_prop'] + self.w_rep * rep
            utilities.append((util, p))
        utilities.sort(key=lambda x: x[0], reverse=True)
        top_util = utilities[0][0]
        top_candidates = [p for u, p in utilities if abs(u - top_util) < 1e-9]
        return random.choice(top_candidates)

    # -----------------------------------------------------------
    # Adapter komunikasi lokal (tanpa XMPP)
    # -----------------------------------------------------------
    async def send_call_for_proposal(self, worker_jid: str, task: Dict):
        info = GLOBAL_DIRECTORY.registry.get(worker_jid)
        if not info:
            return None
        worker = info.get('obj')
        return await worker.on_cfp(task)

    async def send_execute(self, winner: Dict, task: Dict):
        worker = GLOBAL_DIRECTORY.registry.get(winner['worker'], {}).get('obj')
        if not worker:
            return {'status': 'fail', 'reason': 'worker_offline'}
        return await worker.execute(task)