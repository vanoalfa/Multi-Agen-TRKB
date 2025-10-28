# Simulasi DirectoryAgent sederhana untuk mode lokal (tanpa XMPP)

from typing import Dict

class Directory:
    """Menyimpan registrasi semua agen"""
    def __init__(self):
        self.registry: Dict[str, Dict] = {}

    def register(self, jid: str, info: Dict):
        self.registry[jid] = info

    def unregister(self, jid: str):
        if jid in self.registry:
            del self.registry[jid]

    def find_workers(self):
        """Mengembalikan semua JID dengan role 'worker'"""
        return [jid for jid, info in self.registry.items() if info.get('role') == 'worker']


# Directory global yang dipakai semua modul
GLOBAL_DIRECTORY = Directory()