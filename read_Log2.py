import time
from threading import Thread
from copy import deepcopy
import re


def check_for_update(file, file_name, end_time):
    wait = 1
    print("===========\nWaiting on file update.....\n===========")
    while wait:
        file.close()
        time.sleep(5)
        file = open(file_name)
        line = file.readline()
        while line:
            lineList = line.split()
            if lineList[1] <= end_time:
                line = file.readline()
                continue
            else:
                wait = 0
                break
    return file, line


def get_attr_match(line, attr, debug=False):
    try:
        regex = re.compile(".*\s" + attr + "=([\w\d]*)")
        if debug:
            x = re.match(regex, line).group(1)
            print(x, " found in", line)
        return re.match(regex, line).group(1)
    except AttributeError:
        if debug:
            print("No attribute:", attr, "in", line)
        return ""


def get_entity_or_target(line, attr, debug=False):
    try:
        regex = re.compile(".*\s" + attr + "=\[([\w\d\s=]*)]")
        if debug:
            x = re.match(regex, line).group(1)
            print(x, " found in", line)
        return re.match(regex, line).group(1)
    except AttributeError:
        try:
            regex = re.compile(".*\s" + attr + "=\[([\w\d\s=]*)\[[\w\d\s=]*]([\w\d\s=]*)]")
            if debug:
                x = re.match(regex, line).group(1) + re.match(regex, line).group(2)
                print(x, " found in", line)
            return re.match(regex, line).group(1) + re.match(regex, line).group(2)
        except:
            if debug:
                print("No attribute:", attr, "in", line)
            return ""


def get_block(line, debug=False):
    try:
        regex = re.compile(".*\s-\s+([\w\d]*_[\w\d]*)")
        if debug:
            x = re.match(regex, line).group(1)
            print(x, " found in", line)
        return re.match(regex, line).group(1)
    except AttributeError:
        if debug:
            print("No Block in", line)
        return ""


def get_func(line, debug=False):
    try:
        regex = re.compile("(.*)\.(\w*)\(\)\s-\s(.*)")
        if debug:
            x = re.match(regex, line).group(2)
            print(x, " found in", line)

        return re.match(regex, line).group(2)
    except AttributeError:
        if debug:
            print("No function in", line)
        return ""


def get_type(line, debug=False):
    try:
        regex = re.compile("(.*)\s(\w*)\.(.*)")
        if debug:
            x = re.match(regex, line).group(2)
            print(x, " found in", line)
        return re.match(regex, line).group(2)
    except AttributeError:
        if debug:
            print("No type in", line)
        return ""


def get_time(line, debug=False):
    try:
        regex = re.compile("(.*)(\d{2}:\d{2}:\d{2}\.\d*)(.*)")
        if debug:
            x = re.match(regex, line).group(2)
            print(x, " found in", line)
        return re.match(regex, line).group(2)
    except AttributeError:
        if debug:
            print("No time in", line)
        return ""


def get_entity(command, f, players, debug=False):
        card_id = get_attr_match(command, "CardID", debug)
        entity = get_attr_match(command, "Entity", debug)
        if entity == "":
            entity = get_attr_match(command, "id", debug)
        player_id = get_attr_match(command, "player", debug)

        attack = -1
        health = -1
        mana = -1
        while attack == -1 or health == -1 or mana == -1 or player_id == "":
            command = f.readline()
            if command == "":
                return players
            tag = get_attr_match(command, "tag", debug)
            if tag == "COST":
                mana = int(get_attr_match(command, "value", debug))
            elif tag == "HEALTH":
                health = int(get_attr_match(command, "value", debug))
            elif tag == "ATK":
                attack = int(get_attr_match(command, "value", debug))
            elif tag == "CARDTYPE":
                if get_attr_match(command, "value", debug) == "SPELL":
                    health = 0
                    attack = 0
                elif get_attr_match(command, "value", debug) == "HERO":
                    attack = 0
            elif tag == "CONTROLLER":
                player_id = get_attr_match(command, "value", debug)
        players[int(player_id)]["Hand"].append([entity, card_id, mana, attack, health, 0])


def skip_non_game_state(f, command):
    while get_type(command) != "GameState":
        command = f.readline()
        if command == "":
            return f, command
    return f, command


def cast_hero_power(hero_power, target):
    return 0


def dmg_player(target, dmg):
    armor = target["Life"][1]
    life = target["Life"][0]
    dmg = dmg - armor
    if dmg >= 0:
        target["Life"] = [life - dmg, 0]
    else:
        target["Life"] = [life, -1 * dmg]


def main(verbose=False, last_state="IDLE"):
    lastRead = 0
    game = {"State": "IDLE", "Winner": None, "Loser": None}
    player = {}
    opponent = {}
    players = [game, player, opponent]
    player["Current Board"] = []
    player["Hand"] = []
    player["Life"] = [30, 0]
    player["Mana"] = 0
    opponent["Current Board"] = []
    opponent["Hand"] = []
    opponent["Life"] = [30, 0]
    opponent["Mana"] = 0
    filename = "E:\Hearthstone\Logs\Power_4.txt"
    # filename = "E:\Hearthstone\Logs\Power_1.txt"
    if game["State"] == "SETUP" or game["State"] == "MULLIGAN" or game["State"] == "IDLE":
        if verbose:
            print("SETTING UP")
        with open(filename) as f:
            while f:
                command = f.readline()
                f, command = skip_non_game_state(f, command)
                if command == "":
                    return players
                lastRead = get_time(command)
                if get_block(command) == "CREATE_GAME":
                    game["State"] = "SETUP"
                    while get_block(command) != "TAG_CHANGE" or not (
                          get_attr_match(command, "Entity") == "GameEntity" and
                          get_attr_match(command, "tag") == "STEP" and
                          get_attr_match(command, "value") == "BEGIN_MULLIGAN"):
                        f, command = skip_non_game_state(f, command)
                        if command == "":
                            return players
                        if get_block(command) == "FULL_ENTITY":
                            entity_id = get_attr_match(command, "ID")
                            card_id = get_attr_match(command, "CardID")
                            if entity_id == "64":
                                player["Hero"] = (card_id, entity_id)
                            if entity_id == "65":
                                player["Hero Power"] = (card_id, entity_id)
                            if entity_id == "66":
                                opponent["Hero"] = (card_id, entity_id)
                            if entity_id == "67":
                                opponent["Hero Power"] = (card_id, entity_id)
                        elif get_attr_match(command, "PlayerID") == '1':
                            x = get_attr_match(command, "PlayerName")
                            if x != "":
                                player["Player Name"] = x
                        elif get_attr_match(command, "PlayerID") == '2':
                            x = get_attr_match(command, "PlayerName")
                            if x != "":
                                opponent["Player Name"] = x
                        elif get_block(command) == "SHOW_ENTITY":
                            get_entity(command, f, players)
                        elif get_block(command) == "TAG_CHANGE" and get_attr_match(command, "tag") == "ZONE" and \
                                get_attr_match(command, "value") == "HAND":
                            opponent["Hand"].append([get_attr_match(command, "Entity"), -1, -1, -1, -1, 0])
                        command = f.readline()
                        if command == "":
                            return players
                elif (get_block(command) == "TAG_CHANGE" and
                        get_attr_match(command, "Entity") == opponent["Player Name"] and
                        get_attr_match(command, "tag") == "MULLIGAN_STATE" and
                        get_attr_match(command, "value") == "INPUT"):
                    game["State"] = "MULLIGAN"
                    if verbose:
                        print("Starting Game: ", player["Player Name"], "vs", opponent["Player Name"])
                elif get_func(command) == "SendChoices" and get_attr_match(command, "ChoiceType") == "MULLIGAN":
                    if verbose:
                        print("Geting the mulling: ", player["Player Name"], "vs", opponent["Player Name"])
                    while get_func(command) != "DebugPrintEntitiesChosen":
                        command = f.readline()
                        f, command = skip_non_game_state(f, command)
                        if command == "":
                            return players
                    player_id = int(get_attr_match(command, "id"))
                    num_choices = int(get_attr_match(command, "EntitiesCount"))
                    mulligan_choices = []
                    for i in range(num_choices):
                        command = f.readline()
                        if command == "":
                            return players
                        mulligan_choices.append(get_attr_match(command, "id"))
                    players[player_id]["Hand"] = [x for x in player["Hand"] if x[0] in mulligan_choices]

                    while (get_block(command) != "TAG_CHANGE" or not(
                           get_attr_match(command, "Entity") == "GameEntity" and
                           get_attr_match(command, "tag") == "NEXT_STEP" and
                           get_attr_match(command, "value") == "MAIN_READY")):
                        f, command = skip_non_game_state(f, command)
                        if command == "":
                            return players
                        if get_block(command) == "SHOW_ENTITY":
                            get_entity(command, f, players)
                        command = f.readline()
                        if command == "":
                            return players
                    lastRead = get_time(command)
                    game["State"] == "MULL_DONE"
                    break
    ordered_players = []
    if len(player["Hand"]) == 3:
        ordered_players.append(opponent)
        ordered_players.append(player)
    else:
        ordered_players.append(player)
        ordered_players.append(opponent)
    ordered_players[0]["Hand"].append(['68', 'GAME_005', 0, 0, 0, 0])
    turn = 0
    game["State"] = "PLAYING"
    f, command = check_for_update(f, filename, lastRead)
    while game["State"] == "PLAYING":
        if turn == 90:
            game["State"] = "TIE"
            continue
        if (get_block(command) == "TAG_CHANGE" and
                get_attr_match(command, "Entity") == "GameEntity" and
                get_attr_match(command, "value") == "MAIN_READY" and
                get_attr_match(command, "tag") == "STEP"):
            turn += 1
            current_player = ordered_players[turn % 2]
            current_opponent = ordered_players[(turn + 1) % 2]
            current_player["Mana"] += 1
            if verbose:
                print("STARTING TURN", turn, current_player["Player Name"])
            while (get_block(command) != "TAG_CHANGE" or not (
                    get_attr_match(command, "Entity") == "GameEntity" and
                    get_attr_match(command, "value") == "MAIN_NEXT" and
                    get_attr_match(command, "tag") == "STEP")):

                if (get_block(command) == "TAG_CHANGE" and
                        get_attr_match(command, "Entity") == "GameEntity" and
                        get_attr_match(command, "value") == "MAIN_START" and
                        get_attr_match(command, "tag") == "STEP"):
                    if verbose:
                        print("DRAWING CARD", turn, current_player["Player Name"])
                    while (get_block(command) != "TAG_CHANGE" or not(
                           get_attr_match(command, "Entity") == "GameEntity" and
                           get_attr_match(command, "tag") == "STEP" and
                           get_attr_match(command, "value") == "MAIN_ACTION")):
                        if current_player == opponent:
                            if (get_block(command) == "TAG_CHANGE" and
                                    get_attr_match(command, "tag") == "ZONE" and
                                    get_attr_match(command, "value") == "HAND"):
                                opponent["Hand"].append([get_attr_match(command,"id"), -1, -1, -1, -1, 0])
                        else:
                            if get_block(command) == "SHOW_ENTITY":
                                get_entity(command, f, players)
                        command = f.readline()
                        f, command = skip_non_game_state(f, command)
                        if command == "":
                            return players
                if (get_block(command) == "TAG_CHANGE" and
                        get_attr_match(command, "Entity") == "GameEntity" and
                        get_attr_match(command, "value") == "MAIN_ACTION" and
                        get_attr_match(command, "tag") == "STEP"):
                    if verbose:
                        print("STARTING MAIN ACTION", turn, current_player["Player Name"])
                    while (get_block(command, verbose) != "TAG_CHANGE" or not (
                            get_attr_match(command, "Entity") == "GameEntity" and
                            get_attr_match(command, "tag") == "STEP" and
                            get_attr_match(command, "value") == "MAIN_END")):
                        if get_block(command) == "BLOCK_START" and get_attr_match(command, "BlockType") == "PLAY":
                            entity = get_entity_or_target(command, "Entity")
                            target = get_entity_or_target(command, "Target")
                            if entity == "":
                                entity = command
                            card_id = get_attr_match(entity, "cardId")
                            target_id = get_attr_match(target, "id")

                            if card_id == current_player["Hero Power"][0]:
                                if current_player["Hero Power"][0] == "CS2_102":
                                    current_player["Life"][1] += 2
                                else:
                                    if target_id == current_opponent["Hero"][1]:
                                        dmg_player(current_opponent, 1)
                                        if current_opponent["Life"][0] <= 0:
                                            players[0]["State"] = "GAMEOVER"
                                            players[0]["Winner"] = current_player["Player Name"]
                                            players[0]["Loser"] = current_opponent["Player Name"]
                                    else:
                                        defender = [x for x in current_opponent["Current Board"]
                                                    if x[0] == target_id][0]
                                        defender[4] -= 1
                                        if defender[4] <= 0:
                                            current_opponent["Current Board"].remove(defender)
                            else:
                                entity = get_entity_or_target(command, "Entity")
                                target = get_entity_or_target(command, "Target")
                                card_id = get_attr_match(entity, "id")
                                stack = deepcopy([x for x in current_player["Hand"] if x[0] == card_id][0])
                                current_player["Hand"].remove(stack)
                                if current_player == opponent:
                                    while get_block(command) != "SHOW_ENTITY":
                                        command = f.readline()
                                        if command == "":
                                            return players
                                    get_entity(command, f, players)
                                    stack = deepcopy(opponent["Hand"][-1])
                                    opponent["Hand"].remove(opponent["Hand"][-1])

                                if stack[4] == 0:
                                    print("CAST", stack, " on", target)
                                else:
                                    stack[-1] = 0
                                    current_player["Current Board"].append(stack)
                        elif get_block(command) == "BLOCK_START" and get_attr_match(command, "BlockType") == "ATTACK":
                            entity = get_entity_or_target(command, "Entity")
                            target = get_entity_or_target(command, "Target")

                            if entity == "":
                                while get_block(command, verbose) != "METADATA":
                                    command = f.readline()
                                    if command == "":
                                        return players
                            card_id = get_attr_match(entity, "id")
                            target_id = get_attr_match(target, "id")

                            if target_id == current_opponent["Hero"][1]:
                                card = [x for x in current_player["Current Board"] if x[0] == card_id][0]
                                dmg_player(current_opponent, card[3])
                                if current_opponent["Life"][0] <= 0:
                                    players[0]["State"] = "GAMEOVER"
                                    players[0]["Winner"] = current_player["Player Name"]
                                    players[0]["Loser"] = current_opponent["Player Name"]
                            else:
                                defender = [x for x in current_opponent["Current Board"] if x[0] == target_id][0]
                                attacker = [x for x in current_player["Current Board"] if x[0] == card_id][0]
                                defender[4] -= attacker[3]
                                attacker[4] -= defender[3]
                                if defender[4] <= 0:
                                    current_opponent["Current Board"].remove(defender)
                                if attacker[4] <= 0:
                                    current_player["Current Board"].remove(attacker)
                        elif get_block(command) == "TAG_CHANGE" and get_attr_match(command, "value") == "CONCEDED":
                            players[0]["State"] = "CONCEDE"
                            players[0]["Winner"] = current_opponent["Player Name"]
                            players[0]["Loser"] = current_player["Player Name"]
                            break
                        if verbose:
                            print("STARTING NEXT ACTION LOOP+++++++!")
                        command = f.readline()
                        f, command = skip_non_game_state(f, command)
                        if command == "":
                            return players
                        if verbose:
                            print("STARTING NEXT ACTION LOOP============")
                        if command == "":
                            return players
                if game["State"] != "PLAYING":
                    break
                command = f.readline()
                f, command = skip_non_game_state(f, command)
                if command == "":
                    return players
            for x in players[1:]:
                for y in x["Hand"]:
                    y[-1] += 1
                for y in x["Current Board"]:
                    y[-1] += 1
            if verbose:
                print(opponent["Hero"], opponent["Life"])
                print("\t", opponent["Hand"])
                print("\t", opponent["Current Board"])
                print("\t", player["Current Board"])
                print("\t", player["Hand"])
                print(player["Hero"], player["Life"])
        command = f.readline()
        f, command = skip_non_game_state(f, command)
        if command == "":
            return players
    if verbose:
        print("=============================================================================")
        print("====== \t\t", game["Winner"], " Victory\t\t======")
        print("=============================================================================")
    return players


if __name__ == "__main__":
    main()
