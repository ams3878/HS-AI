import time

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


def get_action(file):
    action = ""
    line = file.readline
    logLineList = line.split()
    timeupdate = logLineList[1]

    if logLineList[5] == "BlockType=PLAY":
        action = "PLAY"
    return action, timeupdate


def hero_power(hpower, t):
    print("Using hero Power", hpower, t)


def skip_block(file):
   # print("============SKIPPING BLOCK=============")
    lsplit = file.readline().split()
    while lsplit[4] != "BLOCK_END":
        if lsplit[4] == "BLOCK_START":
            file, l, lsplit = skip_block(file)
        lsplit = file.readline().split()
    l = file.readline()
    lsplit = l.split()
    return file, l, lsplit

def play_card(file, cardid):
    l = file.readline()
    lsplit = l.split()
    if lsplit[4] == "BLOCK_START":
        file, l, lsplit = skip_block(file)
    newzone = 0
    pos = 0
    t = 0
    while lsplit[4] != "BLOCK_END":
        try:
            if l.split("cardId=")[1].split()[0] == cardid:
                if l.split("value=")[1].split()[0] == "PLAY":
                    newzone = "PLAY"
                    t = 0
                    templine = file.readline()
                    pos = int(templine.split("value=")[1].split()[0])
        except IndexError:
            pass
        l = file.readline()
        lsplit = l.split()
        if lsplit[4] == "BLOCK_START":
            file, l, lsplit = skip_block(file)

    return newzone, pos, t


lastRead = 0
player = {}
opponent = {}
lines = {}
phase = "Get Hero"
subPhase = "Start"
waitingOnFile = 0
player["Player Name"] = "PerilousPear#1849"
player["Current Board"] = []
opponent["Current Board"] = []
filename = "E:\Hearthstone\Logs\Power.log"
#filename = "E:\Hearthstone\Logs\Power_1.txt"

f = open(filename)

line = f.readline()
print("Getting Hero data")
while phase == "Get Hero":
    logLineList = line.split()
    lastRead = logLineList[1]
    logType = logLineList[2].split('.')[0]
    if logType == "GameState":
        if logLineList[4] == "FULL_ENTITY":
            idSplit = line.split('ID=')
            try:
                entityID = idSplit[1].split()[0]
                cardID = idSplit[2][:-1]
            except IndexError:
                pass
            try:
                if entityID == "64":
                    player["hero"] = (cardID, entityID)
                if entityID == "65":
                    player["hero power"] = (cardID, entityID)
                if entityID == "66":
                    opponent["hero"] = (cardID, entityID)
                if entityID == "67":
                    opponent["hero power"] = (cardID, entityID)
                    phase = "Get Players"
            except NameError:
                pass
    line = f.readline()

while phase == "Get Players":
    logLineList = line.split()
    lastRead = logLineList[1]
    logType = logLineList[2].split('.')[0]
    try:
        if logLineList[4].split('=')[0] == "PlayerID":
            playerName = line.split('=')[-1][:-1]
            playerNum = logLineList[4].split('=')[1][:-1]
            if playerName == player["Player Name"]:
                player["Player Number"] = playerNum
            else:
                opponent["Player Number"] = playerNum
                opponent["Player Name"] = playerName
        opponent["Player Number"]
        player["Player Number"]
        phase = "Get Pre-Mulligan"
    except IndexError:
        pass
    except KeyError:
        pass
    line = f.readline()
print("\t player: ", player["hero"])
print("\t opponent: ", opponent["hero"])
print("Starting Mulligan Phase")
preMullHand = []
while phase == "Get Pre-Mulligan":
    try:
        logLineList = line.split()
        lastRead = logLineList[1]
        logType = logLineList[2].split('.')[0]
        if logType == "GameState":
            if logLineList[4] == "SHOW_ENTITY":
                lineSplit = line.split('=')
                preMullHand.append((lineSplit[2][:-1], 0))
            elif line.split('=')[-1] == "BEGIN_MULLIGAN \n":
                player["Pre Mulligan Hand"] = preMullHand
                phase = "Get Mulligan"
    except IndexError:
        pass
    line = f.readline()

curHand = []
oppHand = [('Unknown', 1, 0), ('Unknown', 2, 0), ('Unknown', 3, 0)]
print("\t player choice: ", player["Pre Mulligan Hand"])
print("Getting Mulligan Choices")
while phase == "Get Mulligan":
    if not line:
        f, line = check_for_update(f, filename, lastRead)
    logLineList = line.split()
    lastRead = logLineList[1]
    logType = logLineList[2].split('.')[0]
    logFunction = logLineList[2].split('.')[1]
    if logType == "GameState":
        if logLineList[4] == "SHOW_ENTITY":
            idSplit = line.split('id=')
            curHand.append((idSplit[1].split('=')[-1][:-1], 0))
        elif line.split('=')[-1] == "MAIN_READY \n":
            if len(player["Pre Mulligan Hand"]) == 3:
                phase = "Player"
                oppHand.append(('Unknown', 4, 0))
                oppHand.append(('COIN', 5, 0))
            else:
                curHand.append(('COIN', 0))
                phase = "Opponent"
            player["Current Hand"] = curHand
            opponent["Current Hand"] = oppHand
        elif logFunction == "SendChoices()":
            try:
                curHand.append((line.split('cardId=')[1].split()[0], 0))
            except IndexError:
                pass
    line = f.readline()

print("\t player hand: ", player["Current Hand"])
print("\t opponent hand: ", opponent["Current Hand"])
print("Starting Main Phases")
while line:
    print(player["Player Name"], "'s turn")
    print("\tOpp hand: ", opponent["Current Hand"])
    print("\tYour hand: ", player["Current Hand"])
    print("\tOpp board: ", opponent["Current Board"])
    print("\tYour board: ", player["Current Board"])
    while phase == "Player":
        if not line:
            f, line = check_for_update(f, filename, lastRead)

        if subPhase == "End":
            tempHand = []
            for i in player["Current Hand"]:
                tempHand.append((i[0], i[1] + 1))
            player["Current Hand"] = tempHand
            phase = "Opponent"
            subPhase = "Start"
            break

        logLineList = line.split()
        lastRead = logLineList[1]
        logType = logLineList[2].split('.')[0]
        logFunction = logLineList[2].split('.')[1]
        if logType == "GameState":
            if subPhase == "Start":
                try:
                    if logLineList[5] == "Entity=GameEntity" \
                            and logLineList[6] == "tag=STEP" and logLineList[7] == "value=MAIN_START":
                        subPhase = "Draw"
                except IndexError:
                    pass
            elif subPhase == "Draw":
                temp = player["Current Hand"]
                if logLineList:
                    if logLineList[4] == "SHOW_ENTITY":
                        print("Drawing....")
                        temp.append((logLineList[-1].split('=')[1], 0))
                        player["Current Hand"] = temp
                        subPhase = "Main"
                        print("\tYour hand: ", player["Current Hand"])
            try:
                if logLineList[5] == "BlockType=PLAY":
                    print("playing")
                    entity = line.split("Entity=")[1]
                    zone = entity.split("zone=")[1].split()[0]
                    cardid = entity.split("cardId=")[1].split()[0]
                    zonePos = int(entity.split("zonePos=")[1].split()[0])
                    target = int(entity.split("Target=")[1].split()[0])
                    if zone == "HAND":
                        print("Playing....", player["Current Hand"][zonePos-1])
                        del player["Current Hand"][zonePos-1]
                        zone, zonePos, target = play_card(f, cardid)
                        print(zone, zonePos, target)
                    elif zone == "PLAY":
                        if zonePos == 0:
                            hero_power(player["hero power"], target)

                if logLineList[5] == "Entity=GameEntity" \
                        and logLineList[6] == "tag=STEP" and logLineList[7] == "value=MAIN_END":
                    subPhase = "End"
            except IndexError:
                pass
        line = f.readline()

    if phase == "Opponent":
        print("===========\n", opponent["Player Name"], "GOING.....\n===========")
    while phase == "Opponent":
        if subPhase == "End":
            tempHand = []
            for i in opponent["Current Hand"]:
                tempHand.append((i[0], i[1], i[2] + 1))
            opponent["Current Hand"] = tempHand
            phase = "Player"
            subPhase = "Start"
            break

        logLineList = line.split()
        lastRead = logLineList[1]
        logType = logLineList[2].split('.')[0]
        logFunction = logLineList[2].split('.')[1]

        if subPhase == "Start":
            opponent["Current Hand"].append(('Unknown', len(opponent["Current Hand"]) + 1, 0))
            subPhase = "Main"
        if logType == "GameState":
            try:
                if logLineList[5] == "Entity=GameEntity"\
                        and logLineList[6] == "tag=STEP" and logLineList[7] == "value=MAIN_END":
                    subPhase = "End"
            except IndexError:
                pass
        line = f.readline()

f.close()
print(player)
print(opponent)
print(lastRead)
print("DONE")


