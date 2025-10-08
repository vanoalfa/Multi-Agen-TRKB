import asyncio
import time
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from datetime import datetime

ALL_AGENTS = ["a@localhost", "b@localhost", "c@localhost"]
ENERGY = {"a@localhost": 20, "b@localhost": 60, "c@localhost": 100}
HISTORY_FILE = "soal2History.txt"

class AgentC(Agent):
    class MainBehaviour(CyclicBehaviour):
        async def run(self):
            print("\n[C] ================= MULAI SIKLUS BARU =================")
            start_time = time.time()

            if not getattr(self.agent, "has_voted", False):
                choice = max(ENERGY, key=ENERGY.get)
                print(f"[C] Memilih kandidat dengan energi tertinggi -> {choice}")

                print("[C] Mengirim pesan VOTE ke agen lain...")
                for target in ALL_AGENTS:
                    if target != str(self.agent.jid):
                        await self.send(Message(to=target, body=f"VOTE:{choice}"))
                        print(f"[C]    > Pesan VOTE dikirim ke {target}")
                self.agent.votes[str(self.agent.jid)] = choice
                self.agent.has_voted = True

            print("[C] Menunggu pesan VOTE dari agen lain...")
            while len(self.agent.votes) < len(ALL_AGENTS):
                msg = await self.receive(timeout=5)
                if msg and msg.body.startswith("VOTE:"):
                    sender = str(msg.sender)
                    voted_for = msg.body.split(":")[1]
                    if sender not in self.agent.votes:
                        self.agent.votes[sender] = voted_for
                        print(f"[C]    > Diterima VOTE dari {sender} untuk {voted_for}")
                else:
                    print("[C] Masih menunggu agen lain...")

            voting_end = time.time()
            voting_duration = voting_end - start_time
            print(f"\n[C] Durasi Voting: {voting_duration:.2f} detik")

            winner = max(set(self.agent.votes.values()), key=list(self.agent.votes.values()).count)
            print(f"[C] Voting selesai. Koordinator terpilih: {winner}")
            print("=============================================================================\n")

            with open(HISTORY_FILE, "a") as f:
                f.write(f"[{datetime.now()}] [C] Voting: {winner}\n")

            jmlhRotasi = 6
            print(f"[C] Memulai rotasi koordinator sebanyak {jmlhRotasi} kali...\n")
            for i in range(jmlhRotasi):
                current_coord = ALL_AGENTS[i % 3]
                print(f"[C] Rotasi ke-{i+1}: Koordinator aktif -> {current_coord}")
                with open(HISTORY_FILE, "a") as f:
                    f.write(f"[{datetime.now()}] [C] Koordinator aktif: {current_coord}\n")

                total_energy = sum(ENERGY.values())
                portion = (ENERGY[str(self.agent.jid)] / total_energy) * 100
                print(f"[C] Energi total = {total_energy}, porsi C = {portion:.2f}%\n")
                with open(HISTORY_FILE, "a") as f:
                    f.write(f"C porsi={portion:.2f}%\n")

                await asyncio.sleep(10)

            total_duration = time.time() - start_time
            print(f"[C] Semua rotasi selesai. Agent akan berhenti.")
            print(f"[C] Durasi Total: {total_duration:.2f} detik\n")
            await self.agent.stop()

    async def setup(self):
        self.votes = {}
        self.has_voted = False
        print("[C] Agent siap dan berjalan otomatis.\n")
        self.add_behaviour(self.MainBehaviour())

if __name__ == "__main__":
    agent = AgentC("c@localhost", "1234")
    future = agent.start(auto_register=True)
    asyncio.get_event_loop().run_until_complete(future)
    asyncio.get_event_loop().run_forever()