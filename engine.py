import json
import random
from models import Beastie, Player, Quest
from utils.save_load import load_game, save_game

LOCATIONS = {
    "Town": {
        "description": "A cozy hub of lanterns and friendly faces.",
        "actions": ["talk", "quests", "map", "travel", "status", "save", "quit"],
        "min_level": 1,
    },
    "School": {
        "description": "Classrooms filled with practice scrolls by topic.",
        "actions": ["practice", "quests", "map", "travel", "status", "save", "quit"],
        "min_level": 1,
    },
    "Arcade": {
        "description": "Machines hum with random quiz modes.",
        "actions": ["mini", "map", "travel", "status", "save", "quit"],
        "min_level": 2,
    },
    "Arena": {
        "description": "Beastie battles await the brave.",
        "actions": ["battle", "map", "travel", "status", "save", "quit"],
        "min_level": 3,
    },
}

BATTLE_ART = {
    "encounter": (
        "      /\\_/\\\n"
        "     ( o.o )   A wild {name} appears!\n"
        "      > ^ <    HP {hp}\n"
    ),
    "hit": (
        "   \\  |  /\n"
        "    .-*-.\n"
        "   /  |  \\\n"
        "   Direct hit!\n"
    ),
    "miss": (
        "    .-.\n"
        "   (   )   Ouch!\n"
        "    `-'\n"
        "   / | \\\n"
    ),
    "victory": (
        "    \\o/\n"
        "     |\n"
        "    / \\\n"
        "   Victory!\n"
    ),
    "defeat": (
        "    x_x\n"
        "   /|_|\\\n"
        "    / \\\n"
        "   Defeat...\n"
    ),
}


def level_from_kp(kp):
    if kp < 20:
        return 1
    if kp < 50:
        return 2
    if kp < 90:
        return 3
    if kp < 140:
        return 4
    return 5


def on_level_up(player, old_level):
    if player.level > old_level:
        print(f"Level up! You are now Level {player.level}.")
        for name, data in LOCATIONS.items():
            if data["min_level"] == player.level:
                print(f"Unlocked: {name}.")


def load_questions():
    with open("content/questions.json", "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_quests():
    with open("content/quests.json", "r", encoding="utf-8") as handle:
        return json.load(handle)


def pick_questions(questions, topic=None, difficulty=None, count=1):
    pool = [q for q in questions if (topic is None or q["topic"] == topic)]
    if difficulty is not None:
        pool = [q for q in pool if q["difficulty"] == difficulty]
    if not pool:
        return []
    return random.sample(pool, k=min(count, len(pool)))


def print_box(lines):
    if not lines:
        return
    width = max(len(line) for line in lines)
    print("+" + "-" * (width + 2) + "+")
    for line in lines:
        print(f"| {line.ljust(width)} |")
    print("+" + "-" * (width + 2) + "+")


def list_topics(questions):
    return sorted({q["topic"] for q in questions})


def health_bar(current, maximum, width=10):
    if maximum <= 0:
        maximum = 1
    filled = int(round((current / maximum) * width))
    filled = max(0, min(width, filled))
    return "♥" * filled + "·" * (width - filled)


def ask_question(question):
    print(question["prompt"])
    for idx, choice in enumerate(question["choices"], 1):
        print(f"  {idx}) {choice}")
    while True:
        raw = input("Answer 1-4: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(question["choices"]):
            return question["choices"][int(raw) - 1] == question["answer"]
        print("Please enter a valid choice number.")


def award_kp(player, amount):
    player.kp += amount
    new_level = level_from_kp(player.kp)
    old_level = player.level
    player.level = new_level
    on_level_up(player, old_level)


def practice_quiz(player, questions):
    topics = list_topics(questions)
    topic_raw = input(f"Topic ({', '.join(topics)}; blank for any): ").strip().lower()
    topic = topic_raw or None
    difficulty = input("Difficulty 1-3 (blank for any): ").strip()
    diff_val = int(difficulty) if difficulty.isdigit() else None
    qset = pick_questions(questions, topic=topic, difficulty=diff_val, count=3)
    if not qset:
        print("No questions available for that topic/difficulty.")
        return
    correct = 0
    for q in qset:
        was_correct = ask_question(q)
        if was_correct:
            correct += 1
            award_kp(player, 2)
            print("Correct! +2 KP.")
        else:
            print("Incorrect.")
        update_quest_progress(player, q["topic"], was_correct)
    print(f"You answered {correct}/{len(qset)} correctly.")


def random_mini_game(player, questions):
    qset = pick_questions(questions, count=1)
    if not qset:
        print("No questions available.")
        return
    was_correct = ask_question(qset[0])
    if was_correct:
        award_kp(player, 3)
        print("Mini-game win! +3 KP.")
    else:
        print("Mini-game loss. Try again.")
    update_quest_progress(player, qset[0]["topic"], was_correct)


def show_quests(player):
    if not player.active_quests:
        print_box(["No active quests."])
        return
    lines = ["Active quests:"]
    lines.extend(quest.describe() for quest in player.active_quests)
    print_box(lines)


def show_status(player):
    avatar = [
        "  O  ",
        " /|\\ ",
        " / \\ ",
    ]
    badge = f"[Lv {player.level}]"
    lines = avatar + [badge, player.describe()]
    if player.active_quests:
        lines.append("Active quests:")
        lines.extend(quest.describe() for quest in player.active_quests)
    print_box(lines)


def update_quest_progress(player, topic, correct):
    for quest in list(player.active_quests):
        quest.record_attempt(topic, correct)
        if quest.is_complete():
            print(f"Quest complete: {quest.name}")
            reward = quest.rewards.get("kp", 0)
            coins = quest.rewards.get("coins", 0)
            award_kp(player, reward)
            player.coins += coins
            player.active_quests.remove(quest)


def accept_quest(player, quest_data):
    if any(q.name == quest_data["name"] for q in player.active_quests):
        print("You already have that quest.")
        return
    quest = Quest.from_dict(quest_data)
    player.active_quests.append(quest)
    print(f"Quest accepted: {quest.name}")


def talk_in_town(player, quests_data):
    print("The elder offers you a quest scroll.")
    available = [q for q in quests_data if q["min_level"] <= player.level]
    if not available:
        print("No quests available yet.")
        return
    quest_data = random.choice(available)
    accept = input(f"Accept quest '{quest_data['name']}'? (y/n) ").strip().lower()
    if accept == "y":
        accept_quest(player, quest_data)


def run_battle(player, questions):
    beastie = Beastie.random_beastie(player.level)
    max_hp = beastie.hp
    print(BATTLE_ART["encounter"].format(name=beastie.name, hp=beastie.hp))
    while beastie.hp > 0 and player.hp > 0:
        qset = pick_questions(questions, topic=beastie.topic)
        if not qset:
            print("No questions for this Beastie. It flees.")
            return
        correct = ask_question(qset[0])
        if correct:
            beastie.hp = max(0, beastie.hp - 3)
            award_kp(player, 4)
            print(BATTLE_ART["hit"])
            print("KP +4.")
        else:
            player.hp = max(0, player.hp - 2)
            print(BATTLE_ART["miss"])
            print("You are hit! -2 HP.")
        hp_bar = health_bar(beastie.hp, max_hp)
        print(f"{beastie.name} HP {beastie.hp}/{max_hp} {hp_bar}")
        update_quest_progress(player, qset[0]["topic"], correct)
    if player.hp <= 0:
        print(BATTLE_ART["defeat"])
        print("You collapse and return to Town with 1 HP.")
        player.hp = 1
        player.location = "Town"
        return
    print(BATTLE_ART["victory"])
    print(f"{beastie.name} defeated! You earn 5 coins.")
    player.coins += 5


def travel(player):
    print("Available locations:")
    for name, data in LOCATIONS.items():
        if player.level >= data["min_level"]:
            print(f"- {name}")
    dest = input("Travel to: ").strip().title()
    if dest not in LOCATIONS:
        print("Unknown location.")
        return
    if player.level < LOCATIONS[dest]["min_level"]:
        print("That location is locked by level.")
        return
    player.location = dest
    print(f"You travel to {dest}.")


def show_world_map(player):
    def label(name):
        data = LOCATIONS[name]
        if player.level < data["min_level"]:
            return f"{name} (L{data['min_level']}+)"
        if player.location == name:
            return f"{name} [You]"
        return name

    icons = {
        "Town": [
            "  /\\  ",
            " /__\\ ",
            " |[]| ",
        ],
        "School": [
            "  __  ",
            " /__\\ ",
            " |__| ",
        ],
        "Arcade": [
            " .--. ",
            " |==| ",
            " '--' ",
        ],
        "Arena": [
            " /==\\ ",
            " |||| ",
            " \\__/ ",
        ],
    }
    arena = label("Arena")
    school = label("School")
    arcade = label("Arcade")
    town = label("Town")
    lines = [
        "World Map",
        "==================================",
        f"             {icons['Arena'][0]}",
        f"             {icons['Arena'][1]}",
        f"             {icons['Arena'][2]}",
        f"             {arena}",
        "                |",
        f"{icons['School'][0]}     {icons['Arcade'][0]}",
        f"{icons['School'][1]}     {icons['Arcade'][1]}",
        f"{icons['School'][2]}     {icons['Arcade'][2]}",
        f"{school} -- {arcade}",
        "                |",
        f"             {icons['Town'][0]}",
        f"             {icons['Town'][1]}",
        f"             {icons['Town'][2]}",
        f"             {town}",
        "==================================",
    ]
    print_box(lines)


def main():
    print("Legends of Learning: Awakening (CLI)")
    player = load_game() or Player(name=input("Name: ").strip() or "Seeker")
    questions = load_questions()
    quests_data = load_quests()

    while True:
        loc = LOCATIONS[player.location]
        print(f"\nLocation: {player.location} | Level {player.level} | KP {player.kp} | HP {player.hp} | Coins {player.coins}")
        print(loc["description"])
        print(f"Actions: {', '.join(loc['actions'])}")
        action = input("Action: ").strip().lower()

        if action == "quit":
            save = input("Save before quitting? (y/n) ").strip().lower()
            if save == "y":
                save_game(player)
            print("Farewell.")
            break
        if action == "save":
            save_game(player)
            continue
        if action == "help":
            print("Type one of the actions listed for this location.")
            print("Travel opens available locations; quests show your progress.")
            continue
        if action == "status":
            show_status(player)
            continue
        if action == "map":
            show_world_map(player)
            continue
        if action == "travel":
            travel(player)
            continue
        if action == "quests":
            show_quests(player)
            continue

        if action not in loc["actions"]:
            print("That action is not available here.")
            continue

        if player.location == "Town" and action == "talk":
            talk_in_town(player, quests_data)
            continue
        if player.location == "School" and action == "practice":
            practice_quiz(player, questions)
            continue
        if player.location == "Arcade" and action == "mini":
            random_mini_game(player, questions)
            continue
        if player.location == "Arena" and action == "battle":
            run_battle(player, questions)
            continue


if __name__ == "__main__":
    main()
