import csv
from common import ensure_dir

class MonitorAgent:
    """MonitorAgent: mengumpulkan event dan menulis ke CSV"""

    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        ensure_dir(self.out_dir)
        self.metrics = []

    def receive_event(self, event: dict):
        """Menerima dan menyimpan event"""
        self.metrics.append(event)

    def dump_csv(self, filename='metrics_summary.csv'):
        """Menulis hasil event ke CSV"""
        path = f"{self.out_dir}/{filename}"
        with open(path, 'w', newline='') as csvfile:
            fieldnames = ['time_iso', 'type', 'task', 'worker', 'status', 'reason']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for e in self.metrics:
                row = {k: e.get(k, '') for k in fieldnames}
                writer.writerow(row)