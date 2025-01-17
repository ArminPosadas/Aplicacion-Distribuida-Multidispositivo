import socket
import sys
import os

from trainer import Jugador
from pokemon import Pokemon

HOST = "server"
PORT = 5000
DATA_DIR = "/app/client_data"

def main_menu():
    print("\n===== MENU =====")
    print("[1] Create New Trainer")
    print("[2] Load Existing Trainer")
    print("[3] Create a Pokemon & Save to JSON")
    print("[4] Add Pokemon to Current Trainer's Team (from JSON)")
    print("[5] Connect & Battle")
    print("[6] Exit")
    return input("Choose an option: ")

def create_new_trainer():
    tid = input("Enter trainer ID: ")
    name = input("Enter trainer name: ")
    trainer = Jugador(tid, name)
    save_opt = input("Save this trainer to JSON? (y/n): ").lower()
    if save_opt == 'y':
        filename = input("Enter filename (without .json if you like): ").strip()
        if not filename.endswith(".json"):
            filename += ".json"
        path = os.path.join(DATA_DIR, filename)
        trainer.to_json(path)
        print(f"Saved trainer to {path}")
    return trainer

def load_trainer():
    filename = input("Enter trainer filename (no need to type .json): ").strip()
    if not filename.endswith(".json"):
        filename += ".json"
    path = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(path):
        print("File not found in client_data!")
        return None
    try:
        tr = Jugador.from_json(path)
        print(f"Loaded trainer '{tr.name}' with {len(tr.equipo)} Pokemon.")
        return tr
    except Exception as e:
        print(f"Error loading trainer: {e}")
        return None

def create_pokemon():
    pname = input("Pokemon Name: ")
    ptype = input("Type: ")
    lvl = int(input("Level: "))
    hp = int(input("Life Points (HP): "))
    atk = int(input("Attack: "))
    defe = int(input("Defense: "))
    spatk = int(input("SpAttack: "))
    spdef = int(input("SpDefense: "))
    spd = int(input("Speed: "))
    pkmn = Pokemon(pname, ptype, lvl, hp, atk, defe, spatk, spdef, spd)
    save_opt = input("Save to JSON? (y/n): ").lower()
    if save_opt == 'y':
        filename = input("Filename (no need to type .json): ").strip()
        if not filename.endswith(".json"):
            filename += ".json"
        path = os.path.join(DATA_DIR, filename)
        pkmn.to_json_file(path)
        print(f"Saved Pokemon '{pname}' to {path}")

def add_pokemon_to_trainer(trainer):
    if not trainer:
        print("No current trainer loaded/created!")
        return
    filename = input("Enter Pokemon JSON filename (no need .json): ").strip()
    if not filename.endswith(".json"):
        filename += ".json"
    path = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(path):
        print("File not found in client_data!")
        return
    try:
        pkmn = Pokemon.from_json_file(path)
        trainer.add_pokemon(pkmn)
        print(f"Added {pkmn.name} to {trainer.name}'s team.")
    except Exception as e:
        print(f"Error adding Pokemon: {e}")
    save_res = input("Re-save trainer to JSON? (y/n): ").lower()
    if save_res == 'y':
        out_name = input("Trainer JSON filename (no need .json): ").strip()
        if not out_name.endswith(".json"):
            out_name += ".json"
        out_path = os.path.join(DATA_DIR, out_name)
        trainer.to_json(out_path)
        print(f"Trainer updated at {out_path}")

def build_team_string(equipo):
    n = len(equipo)
    parts = [str(n)]
    for p in equipo:
        record = f"{p.name},{p.life_points},{p.attack},{p.defense},{p.speed}"
        parts.append(record)
    return "|".join(parts)

def connect_and_battle(trainer):
    if not trainer:
        print("No current trainer. Create or load one first!")
        return
    if not trainer.equipo:
        print("No Pokemon in your team! Add at least one first.")
        return
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
        print(f"Connected to server at {HOST}:{PORT}")
        sock.sendall((trainer.name + "\n").encode('utf-8'))
        while True:
            data = sock.recv(1024)
            if not data:
                print("Server closed the connection.")
                break
            msg = data.decode().rstrip()
            print("[SERVER]:", msg)
            if "Send your full team" in msg:
                team_str = build_team_string(trainer.equipo)
                sock.sendall((team_str + "\n").encode('utf-8'))
                continue
            if "Which Pokemon do you send out first?" in msg:
                for i, pkmn in enumerate(trainer.equipo):
                    print(f"[{i}] {pkmn.name} (HP={pkmn.life_points})")
                idx = input("Choose index: ")
                sock.sendall((idx + "\n").encode('utf-8'))
                continue
            if "Enter your action" in msg:
                user_action = input("(fight/giveup/pokemon)> ").strip().lower()
                sock.sendall((user_action + "\n").encode('utf-8'))
                continue
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        sock.close()

def run_client():
    current_trainer = None
    while True:
        choice = main_menu()
        if choice == '1':
            current_trainer = create_new_trainer()
        elif choice == '2':
            tr = load_trainer()
            if tr:
                current_trainer = tr
        elif choice == '3':
            create_pokemon()
        elif choice == '4':
            add_pokemon_to_trainer(current_trainer)
        elif choice == '5':
            connect_and_battle(current_trainer)
        elif choice == '6':
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    run_client()

