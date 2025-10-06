import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from datetime import datetime

HISTORY_FILE = "soal1History.txt"

class AgentB(Agent):
    async def setup(self):
        print("[Agent B] Siap menerima pesan secara autonomous.")
        self.add_behaviour(self.ReceiveAndReplyBehaviour())

    class ReceiveAndReplyBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=100)
            if msg:
                print(f"[Agent B] Pesan diterima: {msg.body}")

                with open(HISTORY_FILE, "a") as f:
                    f.write(f"B menerima dari A: {msg.body}\n")

                reply = Message(to="A@localhost")
                reply.body = f"Balasan dari Agent B ({datetime.now()}) untuk: {msg.body}"
                await self.send(reply)

                with open(HISTORY_FILE, "a") as f:
                    f.write(f"B -> A: {reply.body}\n")

                print(f"[Agent B] Balasan dikirim untuk pesan: {msg.body}")
            else:
                await asyncio.sleep(1)

if __name__ == "__main__":
    agentB = AgentB("B@localhost", "1234")
    future = agentB.start(auto_register=True)
    asyncio.get_event_loop().run_until_complete(future)
    asyncio.get_event_loop().run_forever()