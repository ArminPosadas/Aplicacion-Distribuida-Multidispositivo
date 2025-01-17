import json

class Pokemon:
    def __init__(
            self,
            name,
            p_type,
            level,
            life_points,
            attack,
            defense,
            spattack,
            spdefense,
            speed
    ):
        self.name = name
        self.type = p_type
        self.level = level
        self.life_points = life_points
        self.attack = attack
        self.defense = defense
        self.spattack = spattack
        self.spdefense = spdefense
        self.speed = speed

    def json(self):
        return {
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "life_points": self.life_points,
            "attack": self.attack,
            "defense": self.defense,
            "spattack": self.spattack,
            "spdefense": self.spdefense,
            "speed": self.speed
        }

    def to_json_file(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.json(), f, indent=4)

    @classmethod
    def from_json_file(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            data["name"],
            data["type"],
            data["level"],
            data["life_points"],
            data["attack"],
            data["defense"],
            data["spattack"],
            data["spdefense"],
            data["speed"]
        )
