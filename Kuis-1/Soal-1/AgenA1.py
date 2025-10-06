import asyncio
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from datetime import datetime

HISTORY_FILE = "soal1History.txt"

class AgentA(Agent):
    async def setup(self):
        self.urutan_pesan = 1
        print("[Agent A] Siap dan berjalan secara autonomous.")
        self.add_behaviour(self.SendMsgBehaviour())
        self.add_behaviour(self.ReceiveBehaviour())

    class SendMsgBehaviour(OneShotBehaviour):
        async def run(self):
            msg = Message(to="B@localhost")
            msg.body = f"Halo dari Agent A pada {datetime.now()}. Pesan ke-{self.agent.urutan_pesan}"
            print(f"[Agent A] Mengirim pesan ke-{self.agent.urutan_pesan} ke Agent B...")

            await self.send(msg)

            with open(HISTORY_FILE, "a") as f:
                f.write(f"A -> B: {msg.body}\n")

            print(f"[Agent A] Pesan ke-{self.agent.urutan_pesan} terkirim dan disimpan di file.")

    class ReceiveBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=100)
            if msg:
                print(f"[Agent A] Balasan diterima: {msg.body}")
                with open(HISTORY_FILE, "a") as f:
                    f.write(f"A menerima dari B: {msg.body}\n")
                    f.write(f"===================================================================================================================================================\n")

                self.agent.urutan_pesan += 1

                if self.agent.urutan_pesan <= 13:
                    next_msg = Message(to="B@localhost")
                    next_msg.body = f"Halo lagi dari Agent A (pesan ke-{self.agent.urutan_pesan}) pada {datetime.now()}"
                    await self.send(next_msg)
                    with open(HISTORY_FILE, "a") as f:
                        f.write(f"A -> B: {next_msg.body}\n")
                    print(f"[Agent A] Mengirim ulang pesan ke-{self.agent.urutan_pesan} ke Agent B...")
                else:
                    print(f"[Agent A] Selesai. Sudah mencapai pesan ke-{self.agent.urutan_pesan-1}.")
                    await self.agent.stop()
            else:
                await asyncio.sleep(1)

if __name__ == "__main__":
    agentA = AgentA("A@localhost", "1234")
    future = agentA.start(auto_register=True)
    asyncio.get_event_loop().run_until_complete(future)
    asyncio.get_event_loop().run_forever()