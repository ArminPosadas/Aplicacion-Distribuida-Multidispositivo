import socket
import threading
import time

HOST = '0.0.0.0'
PORT = 5000

connected_clients = []
connected_clients_lock = threading.Lock()

class Player:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.trainer_name = "Unknown"

def matchmaker():
    while True:
        with connected_clients_lock:
            if len(connected_clients) >= 2:
                p1 = connected_clients.pop(0)
                p2 = connected_clients.pop(0)
            else:
                p1 = p2 = None
        if p1 and p2:
            threading.Thread(target=handle_match, args=(p1, p2)).start()
        else:
            time.sleep(0.2)

def handle_match(p1, p2):
    try:
        p1.conn.sendall(b"Matched! Battle is starting...\n")
        p2.conn.sendall(b"Matched! Battle is starting...\n")
        p1.conn.sendall(b"Send your full team (format: 'n|Name,HP,Atk,Def,Spd|...'):\n")
        p2.conn.sendall(b"Send your full team (format: 'n|Name,HP,Atk,Def,Spd|...'):\n")
        data1 = p1.conn.recv(2048).decode().strip()
        data2 = p2.conn.recv(2048).decode().strip()
        p1_team = parse_team_string(data1)
        p2_team = parse_team_string(data2)
        p1_active_idx = choose_pokemon(p1, p1_team, "Which Pokemon do you send out first?: ")
        p2_active_idx = choose_pokemon(p2, p2_team, "Which Pokemon do you send out first?: ")
        p1.conn.sendall(f"You're matched against {p2.trainer_name}, who is using {p2_team[p2_active_idx]['name']}.\n".encode())
        p2.conn.sendall(f"You're matched against {p1.trainer_name}, who is using {p1_team[p1_active_idx]['name']}.\n".encode())
        while True:
            p1_mon = p1_team[p1_active_idx]
            p2_mon = p2_team[p2_active_idx]
            p1.conn.sendall(f"\nYour Pokemon ({p1_mon['name']}) HP: {p1_mon['hp']} | {p2.trainer_name}'s Pokemon ({p2_mon['name']}) HP: {p2_mon['hp']}\n".encode())
            p2.conn.sendall(f"\nYour Pokemon ({p2_mon['name']}) HP: {p2_mon['hp']} | {p1.trainer_name}'s Pokemon ({p1_mon['name']}) HP: {p1_mon['hp']}\n".encode())
            p1.conn.sendall(b"Enter your action (fight/giveup/pokemon): ")
            p2.conn.sendall(b"Enter your action (fight/giveup/pokemon): ")
            cmd1 = p1.conn.recv(1024).decode().strip().lower()
            cmd2 = p2.conn.recv(1024).decode().strip().lower()
            if cmd1 == "giveup":
                p1.conn.sendall(b"You gave up! You lost.\n")
                p2.conn.sendall(b"Opponent gave up! You won.\n")
                break
            if cmd2 == "giveup":
                p2.conn.sendall(b"You gave up! You lost.\n")
                p1.conn.sendall(b"Opponent gave up! You won.\n")
                break
            swapped1 = False
            swapped2 = False
            if cmd1 == "pokemon":
                new_idx = swap_pokemon(p1, p1_team)
                if new_idx is not None and new_idx != p1_active_idx:
                    p1_active_idx = new_idx
                swapped1 = True
            if cmd2 == "pokemon":
                new_idx = swap_pokemon(p2, p2_team)
                if new_idx is not None and new_idx != p2_active_idx:
                    p2_active_idx = new_idx
                swapped2 = True
            p1_mon = p1_team[p1_active_idx]
            p2_mon = p2_team[p2_active_idx]
            if not (swapped1 and swapped2):
                if p1_mon["spd"] >= p2_mon["spd"]:
                    if not swapped1:
                        do_attack(p1_mon, p2_mon, p1, p2)
                        if p2_mon["hp"] <= 0:
                            if not pick_new_if_alive(p2, p2_team, p2_mon):
                                p2.conn.sendall(b"You have no more Pokemon! You lost.\n")
                                p1.conn.sendall(b"Opponent has no more Pokemon! You won.\n")
                                break
                            else:
                                p2_active_idx = get_current_active_idx(p2_team)
                                continue
                    if not swapped2:
                        do_attack(p2_mon, p1_mon, p2, p1)
                        if p1_mon["hp"] <= 0:
                            if not pick_new_if_alive(p1, p1_team, p1_mon):
                                p1.conn.sendall(b"You have no more Pokemon! You lost.\n")
                                p2.conn.sendall(b"Opponent has no more Pokemon! You won.\n")
                                break
                            else:
                                p1_active_idx = get_current_active_idx(p1_team)
                else:
                    if not swapped2:
                        do_attack(p2_mon, p1_mon, p2, p1)
                        if p1_mon["hp"] <= 0:
                            if not pick_new_if_alive(p1, p1_team, p1_mon):
                                p1.conn.sendall(b"You have no more Pokemon! You lost.\n")
                                p2.conn.sendall(b"Opponent has no more Pokemon! You won.\n")
                                break
                            else:
                                p1_active_idx = get_current_active_idx(p1_team)
                    if not swapped1:
                        do_attack(p1_mon, p2_mon, p1, p2)
                        if p2_mon["hp"] <= 0:
                            if not pick_new_if_alive(p2, p2_team, p2_mon):
                                p2.conn.sendall(b"You have no more Pokemon! You lost.\n")
                                p1.conn.sendall(b"Opponent has no more Pokemon! You won.\n")
                                break
                            else:
                                p2_active_idx = get_current_active_idx(p2_team)
        p1.conn.sendall(b"Battle is over. Closing connection...\n")
        p2.conn.sendall(b"Battle is over. Closing connection...\n")
    except Exception as e:
        print("[SERVER] Error in handle_match:", e)
    finally:
        p1.conn.close()
        p2.conn.close()

def parse_team_string(team_str):
    parts = team_str.split('|')
    n = int(parts[0])
    result = []
    for i in range(n):
        seg = parts[i+1].split(',')
        name = seg[0]
        hp   = int(seg[1])
        atk  = int(seg[2])
        defe = int(seg[3])
        spd  = int(seg[4])
        pkmn = {
            "name": name,
            "hp":   hp,
            "atk":  atk,
            "def":  defe,
            "spd":  spd
        }
        result.append(pkmn)
    return result

def build_team_list_message(team):
    lines = ["\nYour Team (alive):\n"]
    for i, p in enumerate(team):
        if p["hp"] > 0:
            lines.append(f"[{i}] {p['name']} (HP={p['hp']})\n")
    return "".join(lines)

def choose_pokemon(player, team, prompt_msg):
    alive_count = sum(1 for p in team if p["hp"] > 0)
    if alive_count <= 1:
        for i, pk in enumerate(team):
            if pk["hp"] > 0:
                return i
        return 0
    else:
        msg = build_team_list_message(team) + prompt_msg
        player.conn.sendall(msg.encode())
        idx_str = player.conn.recv(1024).decode().strip()
        return int(idx_str)

def swap_pokemon(player, team):
    alive_pkmn = [i for i, p in enumerate(team) if p["hp"] > 0]
    if len(alive_pkmn) <= 1:
        player.conn.sendall(b"No other Pokemon alive to swap with!\n")
        return None
    msg = build_team_list_message(team).encode() + b"Choose which Pokemon to swap in: "
    player.conn.sendall(msg)
    new_idx_str = player.conn.recv(1024).decode().strip()
    new_idx = int(new_idx_str)
    if new_idx not in alive_pkmn:
        player.conn.sendall(b"Invalid choice or Pokemon is fainted.\n")
        return None
    return new_idx

def do_attack(attacker, defender, attacker_player, defender_player):
    dmg = max(1, attacker["atk"] - (defender["def"] // 2))
    defender["hp"] -= dmg
    attacker_player.conn.sendall(f"You dealt {dmg} damage to {defender['name']}!\n".encode())
    defender_player.conn.sendall(f"Your {defender['name']} took {dmg} damage!\n".encode())

def pick_new_if_alive(player, team, fainted_mon):
    alive_count = sum(1 for p in team if p["hp"] > 0)
    if alive_count == 0:
        return False
    new_idx = choose_pokemon(player, team, "Your active Pokemon fainted! Choose a new one:\n")
    team[new_idx]["chosen_active"] = True
    return True

def get_current_active_idx(team):
    chosen_idx = None
    for i, p in enumerate(team):
        if p.get("chosen_active") == True:
            chosen_idx = i
            break
    if chosen_idx is not None:
        for p in team:
            p.pop("chosen_active", None)
        return chosen_idx
    for i, p in enumerate(team):
        if p["hp"] > 0:
            return i
    return 0

def start_server():
    print(f"Server starting on {HOST}:{PORT}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    threading.Thread(target=matchmaker, daemon=True).start()
    while True:
        conn, addr = server_socket.accept()
        print(f"Client connected: {addr}")
        player = Player(conn, addr)
        data = conn.recv(1024)
        if data:
            player.trainer_name = data.decode().strip()
        else:
            conn.close()
            continue
        with connected_clients_lock:
            connected_clients.append(player)

if __name__ == "__main__":
    start_server()
