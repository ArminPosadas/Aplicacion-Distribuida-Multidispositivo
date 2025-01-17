import json

class Jugador:
    def __init__(self, player_id, name, equipo=None, bag=None):
        self.player_id = player_id
        self.name = name
        self.equipo = equipo if equipo else []
        self.bag = bag if bag else []

    def add_pokemon(self, pokemon):
        self.equipo.append(pokemon)

    def to_json(self, path):
        data = {
            "Jugador": {
                "PlayerId": self.player_id,
                "Name": self.name,
                "Equipo": [pkmn.json() for pkmn in self.equipo],
                "Bag": self.bag
            }
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def from_json(cls, path):
        from pokemon import Pokemon
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        j = data["Jugador"]
        player_id = j["PlayerId"]
        name = j["Name"]
        bag_data = j["Bag"]
        equipo_json = j["Equipo"]
        equipo_objs = []
        for p_data in equipo_json:
            pkmn = Pokemon(
                p_data["name"],
                p_data["type"],
                p_data["level"],
                p_data["life_points"],
                p_data["attack"],
                p_data["defense"],
                p_data["spattack"],
                p_data["spdefense"],
                p_data["speed"]
            )
            equipo_objs.append(pkmn)
        return cls(player_id, name, equipo_objs, bag_data)
