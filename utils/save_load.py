import json
from models import Player, Quest

SAVE_PATH = "savegame.json"


def save_game(player):
    data = {
        "name": player.name,
        "kp": player.kp,
        "level": player.level,
        "hp": player.hp,
        "coins": player.coins,
        "location": player.location,
        "active_quests": [
            {
                "name": q.name,
                "topic": q.topic,
                "target": q.target,
                "correct_needed": q.correct_needed,
                "rewards": q.rewards,
                "min_level": q.min_level,
                "attempts": q.attempts,
                "correct": q.correct,
            }
            for q in player.active_quests
        ],
    }
    with open(SAVE_PATH, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    print("Game saved.")


def load_game():
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return None
    player = Player(
        name=data["name"],
        kp=data.get("kp", 0),
        level=data.get("level", 1),
        hp=data.get("hp", 10),
        coins=data.get("coins", 0),
        location=data.get("location", "Town"),
    )
    for qdata in data.get("active_quests", []):
        quest = Quest.from_dict(qdata)
        quest.attempts = qdata.get("attempts", 0)
        quest.correct = qdata.get("correct", 0)
        player.active_quests.append(quest)
    return player
