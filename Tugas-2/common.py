import asyncio
import json
import os
import random
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


def load_config(path: str):
    """Membaca file konfigurasi JSON"""
    with open(path, "r") as f:
        return json.load(f)


def ensure_dir(path: str):
    """Membuat folder jika belum ada"""
    os.makedirs(path, exist_ok=True)


@dataclass
class AssignmentHistoryEntry:
    """Struktur data untuk riwayat penugasan"""
    task_id: str
    worker_jid: str
    status: str  # 'assigned', 'success', 'fail', 'reassigned'
    reason: str = ""
    timestamp: float = field(default_factory=time.time)


class Logger:
    """Pencatat event ke file log dan JSON"""
    def __init__(self, out_dir: str):
        ensure_dir(out_dir)
        self.out_dir = out_dir
        self.run_logs: List[Dict[str, Any]] = []

    def log_event(self, event: Dict[str, Any]):
        event['time_iso'] = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime())
        self.run_logs.append(event)
        log_file = os.path.join(self.out_dir, 'events.log')
        with open(log_file, 'a') as f:
            f.write(json.dumps(event) + "\n")

    def persist_history(self, filename: str):
        path = os.path.join(self.out_dir, filename)
        with open(path, 'w') as f:
            json.dump(self.run_logs, f, indent=2)