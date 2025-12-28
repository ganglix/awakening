import random


class Player:
    def __init__(self, name, kp=0, level=1, hp=10, coins=0, location="Town"):
        self.name = name
        self.kp = kp
        self.level = level
        self.hp = hp
        self.coins = coins
        self.location = location
        self.active_quests = []

    def describe(self):
        return (
            f"{self.name} | Level {self.level} | KP {self.kp} | "
            f"HP {self.hp} | Coins {self.coins}"
        )


class Quest:
    def __init__(self, name, topic, target, correct_needed, rewards, min_level=1):
        self.name = name
        self.topic = topic
        self.target = target
        self.correct_needed = correct_needed
        self.rewards = rewards
        self.min_level = min_level
        self.attempts = 0
        self.correct = 0

    def record_attempt(self, topic, correct):
        if topic != self.topic:
            return
        self.attempts += 1
        if correct:
            self.correct += 1

    def is_complete(self):
        if self.attempts < self.target:
            return False
        return self.correct >= self.correct_needed

    def describe(self):
        return (
            f"{self.name} | Topic: {self.topic} | "
            f"Progress {self.correct}/{self.correct_needed} "
            f"in {self.attempts}/{self.target} attempts"
        )

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            topic=data["topic"],
            target=data["target"],
            correct_needed=data["correct_needed"],
            rewards=data["rewards"],
            min_level=data.get("min_level", 1),
        )


class Beastie:
    def __init__(self, name, hp, topic, difficulty):
        self.name = name
        self.hp = hp
        self.topic = topic
        self.difficulty = difficulty

    @classmethod
    def random_beastie(cls, level):
        pool = [
            {"name": "Glimmerfox", "hp": 8, "topic": "fractions", "difficulty": 1},
            {"name": "Sumling", "hp": 8, "topic": "addition", "difficulty": 1},
            {"name": "Shadeclaw", "hp": 8, "topic": "subtraction", "difficulty": 1},
            {"name": "Gearling", "hp": 8, "topic": "place_value", "difficulty": 1},
            {"name": "Ironjaw", "hp": 10, "topic": "integers", "difficulty": 2},
            {"name": "Cogrunner", "hp": 10, "topic": "multiplication", "difficulty": 2},
            {"name": "Divider", "hp": 10, "topic": "division", "difficulty": 2},
            {"name": "Chronosh", "hp": 10, "topic": "time", "difficulty": 2},
            {"name": "Mintcoil", "hp": 10, "topic": "money", "difficulty": 2},
            {"name": "Gemark", "hp": 10, "topic": "geometry", "difficulty": 2},
            {"name": "Tapespine", "hp": 10, "topic": "measurement", "difficulty": 2},
            {"name": "Stormwing", "hp": 12, "topic": "forces", "difficulty": 3},
        ]
        max_difficulty = min(level, 3)
        options = [entry for entry in pool if entry["difficulty"] <= max_difficulty]
        data = random.choice(options)
        return cls(data["name"], data["hp"], data["topic"], data["difficulty"])
