import random
import numpy as np

sellers = {
    "Penjual 1": {"price": 8, "reputation": 0.5},
    "Penjual 2": {"price": 5, "reputation": 0.5},
}

alpha = 0.5      # learning rate
gamma = 0.8      # discount factor
epsilon = 0.3    # eksplorasi (probabilitas memilih random)

Q = {
    "Pembeli 1": {"Penjual 1": 0.0, "Penjual 2": 0.0},
    "Pembeli 2": {"Penjual 1": 0.0, "Penjual 2": 0.0},
}

HISTORY_FILE = "soal3History.txt"

def log_to_file(text):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def get_reward(price, reputation):
    return (1 / price) * 10 + reputation * 5

def simulate_transaction(buyer, rounds=5):
    global Q
    header = f"\n===== Simulasi untuk {buyer} ====="
    print(header)
    log_to_file(header)
    for step in range(rounds):
        if random.random() < epsilon:
            seller = random.choice(list(sellers.keys()))  # eksplorasi
        else:
            seller = max(Q[buyer], key=Q[buyer].get)  # eksploitasi

        s_info = sellers[seller]
        reward = get_reward(s_info["price"], s_info["reputation"])

        old_value = Q[buyer][seller]
        new_value = (1 - alpha) * old_value + alpha * (reward + gamma * max(Q[buyer].values()))
        Q[buyer][seller] = new_value

        reputation_update = reward / 15
        sellers[seller]["reputation"] = min(1.0, (sellers[seller]["reputation"] + reputation_update) / 2)

        if random.random() < 0.2:
            sellers[seller]["reputation"] *= 0.7

        result = (
            f"Ronde {step+1}: {buyer} memilih {seller}\n"
            f"  → Reward: {reward:.2f}\n"
            f"  → Q-Value {seller}: {Q[buyer][seller]:.2f}\n"
            f"  → Reputasi Penjual 1: {sellers['Penjual 1']['reputation']:.2f}, Penjual 2: {sellers['Penjual 2']['reputation']:.2f}\n"
        )
        print(result)
        log_to_file(result)

    footer = "====================================="
    print(footer)
    log_to_file(footer)

open(HISTORY_FILE, "w", encoding="utf-8").close()

simulate_transaction("Pembeli 1", rounds=5)
simulate_transaction("Pembeli 2", rounds=5)

summary = "\n=== Q-Table Akhir ===\n"
for buyer, sellers_q in Q.items():
    summary += f"{buyer}: {sellers_q}\n"

summary += "\n=== Reputasi Akhir Penjual ===\n"
for seller, info in sellers.items():
    summary += f"{seller}: reputasi={info['reputation']:.2f}, harga={info['price']}\n"

print(summary)
log_to_file(summary)
