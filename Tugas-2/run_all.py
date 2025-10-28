import argparse
import asyncio
import json
import os
import random
import time
from common import load_config, Logger, ensure_dir
from directory_agent import GLOBAL_DIRECTORY
from manager_agent import ManagerAgent
from worker_agent import WorkerAgent
from monitor_agent import MonitorAgent


async def run_scenario(config_path: str, scenario: str, mode: str = 'local', seed: int = None):
    # ------------------- LOAD CONFIG -------------------
    config = load_config(config_path)
    out_dir = config.get('persist_logs_dir', 'logs')
    ensure_dir(out_dir)
    logger = Logger(out_dir)
    monitor = MonitorAgent(out_dir)

    if seed is not None:
        random.seed(seed)

    # ------------------- INISIALISASI WORKER -------------------
    workers_cfg = config['agents']['workers']
    GLOBAL_DIRECTORY.registry.clear()

    # Ambil jumlah worker sesuai skenario
    num_workers = config['scenarios'].get(scenario, {}).get('workers', len(workers_cfg))
    selected_workers = workers_cfg[:num_workers]

    print(f"\nWorker aktif untuk skenario {scenario}:")
    for w in selected_workers:
        print(f"   - {w['jid']} (skill={w.get('skill',1.0)}, p_fail={w.get('p_fail',0.1)})")

    for w in selected_workers:
        jid = w['jid']
        skill = w.get('skill', 1.0)
        p_fail = w.get('p_fail', 0.1)
        worker = WorkerAgent(jid=jid, skill=skill, p_fail=p_fail, config=config)
        GLOBAL_DIRECTORY.register(jid, {'role': 'worker', 'skill': skill, 'obj': worker})

    # ------------------- INISIALISASI MANAGER -------------------
    manager_jid = config['agents']['manager_agent']['jid']
    manager = ManagerAgent(jid=manager_jid, config=config, logger=logger, seed=seed)

    # Reset reputasi dan inisialisasi ulang
    manager.reputation.clear()
    manager.init_reputations(list(GLOBAL_DIRECTORY.registry.keys()))

    # ------------------- MEMBUAT DAFTAR TASK -------------------
    tasks_n = config['scenarios'].get(scenario, {}).get('tasks', 3)
    tasks = []
    for i in range(tasks_n):
        t = {
            'id': f"{scenario}-task-{i}",
            'base_cost': random.uniform(50, 200),
            'base_time': random.uniform(2, 8)
        }
        tasks.append(t)

    print(f"\nMenjalankan skenario {scenario} dengan {tasks_n} task...\n")

    # ------------------- MENJALANKAN SEMUA TASK -------------------
    for t in tasks:
        logger.log_event({'type': 'task_created', 'task': t})
        status = await manager.announce_task(t)

        # Ambil informasi worker terakhir yang menangani task ini
        last_worker = None
        last_reason = ''
        if t['id'] in manager.assignment_history:
            hist = manager.assignment_history[t['id']]
            if hist:
                last_worker = hist[-1]['worker_jid']
                last_reason = hist[-1].get('reason', '')

        # Catat waktu sekarang
        current_time = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime())

        # Simpan hasil ke monitor untuk CSV
        monitor.receive_event({
            'time_iso': current_time,
            'type': 'task_result',
            'task': t['id'],
            'worker': last_worker or '-',
            'status': status,
            'reason': last_reason
        })

    # ------------------- SIMPAN LOG DAN HASIL -------------------
    logger.persist_history('run_events.json')
    monitor.dump_csv()

    # Simpan riwayat tiap task
    for tid, hist in manager.assignment_history.items():
        with open(os.path.join(out_dir, f"history_{tid}.json"), 'w') as f:
            json.dump(hist, f, indent=2)

    print("\nSimulasi selesai.")
    print(f"Hasil log tersimpan di folder: {out_dir}")
    print(f"Lihat file: {os.path.join(out_dir, 'metrics_summary.csv')}\n")


def main():
    parser = argparse.ArgumentParser(description="Simulasi Sistem Multi Agen (CNP)")
    parser.add_argument('--mode', choices=['local', 'prosody'], default='local', help='Mode eksekusi')
    parser.add_argument('--config', required=True, help='Path ke file konfigurasi JSON')
    parser.add_argument('--scenario', choices=['A', 'B', 'C'], default='A', help='Pilih skenario')
    parser.add_argument('--seed', type=int, default=None, help='Seed RNG opsional')
    args = parser.parse_args()

    cfg = load_config(args.config)
    seed = args.seed or cfg.get('seed', None)
    asyncio.run(run_scenario(args.config, args.scenario, mode=args.mode, seed=seed))


if __name__ == '__main__':
    main()