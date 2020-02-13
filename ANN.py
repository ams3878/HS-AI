import read_Log2 as logger
from copy import deepcopy
import random as rand
import math
import statistics

WEIGHTS_FILE_NAME = 'weights.tsv'
FACE_THRESHOLD = 1
HPWR_THRESHOLD = 1


def get_printNode(node):
    r_str = "\n"
    for x in node:
        r_str += str(x) + '\n'
    return r_str


def get_play(weights, state_matrix, bias, sort, order=True, cost=False):
    result = []

    play_card_weights_cost = deepcopy(weights)
    state_matrix_cost = deepcopy(state_matrix)

    if order:
        none_value = -10
    else:
        none_value = 10
    state_matrix_cost[2] = sorted([x for x in state_matrix_cost[2]],
                                  key=lambda x: none_value if x[0] is None else x[sort], reverse=order)
    state_matrix_cost[3] = sorted([x for x in state_matrix_cost[3]],
                                  key=lambda x: none_value if x[0] is None else x[3], reverse=order)

    state_matrix_cost[4] = sorted([x for x in state_matrix_cost[4]],
                                  key=lambda x: none_value if x[0] is None else x[sort], reverse=order)
    state_matrix_cost[5] = sorted([x for x in state_matrix_cost[5]],
                                  key=lambda x: none_value if x[0] is None else x[sort], reverse=order)

    state_matrix_cost_t = [[row[i] for row in state_matrix_cost] for i in range(len(state_matrix_cost[0]))]
    state_matrix_bias = bias

    for k in range(len(play_card_weights_cost)):
        result.append(0)
        for i in range(len(play_card_weights_cost)):
            for j in range(len(play_card_weights_cost[0])):
                # weights between 0 and 2
                card = state_matrix_cost_t[k][j]
                if j <= 1:
                    # life
                    result[k] += math.exp(card * (1 - play_card_weights_cost[i][j]))
                elif card[0]:
                    if j == 2:
                        # mana cost
                        if state_matrix_bias < card[0] and cost:
                            pass
                        else:
                            result[k] += math.exp(card[0] * (1 - play_card_weights_cost[i][j]))
                    elif j == 3:
                        # num turns in opponent hand
                        result[k] += math.exp(card[3] * (1 - play_card_weights_cost[i][j]))
                    else:
                        # sum of attack and health
                        result[k] += math.exp((card[1] + card[2]) / 2 * (1 - play_card_weights_cost[i][j]))

    return [x/163.1 for x in result]


def init_weights(width, length):
    play_card_weights = [[], [], [], [], [], []]
    attk_card_weights = [[], [], [], [], [], []]
    trgt_card_weights = [[], [], [], [], [], []]
    hpwr_weights = [[], [], [], [], [], []]
    weights = [play_card_weights, attk_card_weights, trgt_card_weights, hpwr_weights]
    for m in weights:
        for k in range(len(m)):
            for i in range(length):
                m[k].append([])
                for j in range(width):
                    m[k][i].append(rand.random()*2)
    return weights


def read_weights(filename):
    weights = []
    with open(filename, 'r') as f:
        read_str = f.read().split('\t')
        width = int(read_str[0])
        length = int(read_str[1])
        num_nodes = int(read_str[2])
        num_weights = int(read_str[3])
        m_size = width * length
        n_size = m_size * num_nodes
        for k in range(num_weights):
            weights.append([])
            for l in range(num_nodes):
                weights[k].append([])
                for i in range(length):
                    weights[k][l].append([])
                    for j in range(width):
                        weights[k][l][i].append(float(read_str[4 + + k*n_size + l*m_size + i*width + j]))
    return weights


def write_weights(filename, weights):
    with open(filename, 'w') as f:
        write_str = ""
        write_str += str(len(weights[0][0][0])) + "\t"
        write_str += str(len(weights[0][0])) + "\t"
        write_str += str(str(len(weights[0]))) + "\t"
        write_str += str(len(weights)) + "\t"
        # def the best way to do this
        for x in weights:
            for y in x:
                for z in y:
                    for zz in z:
                        write_str += str(zz) + "\t"

        f.write(write_str)


def validate(p, a, t, h, players):
    is_valid = []
    if p and p[2] <= players[1]["Mana"]:
        if p[4] != 0 and len(players[1]["Current Board"]) < 7:
            is_valid.append(1)
        elif t:
            is_valid.append(1)
        else:
            is_valid.append(0)
    else:
        is_valid.append(0)
    if a and t:
        is_valid.append(1)
    else:
        is_valid.append(0)
    if t:
        is_valid.append(1)
    else:
        is_valid.append(0)
    if h and players[1]["Mana"] >= 2:
        is_valid.append(1)
    else:
        is_valid.append(0)
    return is_valid


def select_valid(is_valid, play, players):
    if is_valid[0] == 1:
        if play[0][4] != 0:
            return "Play", play[0]
        else:
            return "Play Spell", play[0], play[2]
    if is_valid[1] == 1:
        return "Attack", play[1], play[2]
    if is_valid[3] == 1:
        return "ARMOR UP!", players[1]["Hero Power"]
    if sum(is_valid) == 0:
        return "PASS", 0


def get_cost(results, is_valid, play, players):
    player_board = players[1]["Current Board"]
    opponent_board = players[2]["Current Board"]
    board_dif = (sum([x[3] + x[4] for x in players[1]["Current Board"]]) -
                sum([x[3] + x[4] for x in players[2]["Current Board"]]))
    hand_dif = len(players[1]["Hand"]) - len(players[2]["Hand"])
    life_dif = sum(players[1]["Life"]) - sum(players[2]["Life"])
    pre_value = life_dif + board_dif + hand_dif

    if play:
        if play[0] == "Attack":
            if play[2] == players[2]["Hero"]:
                life_dif -= play[1][3]
            else:
                t_index = opponent_board.index(play[2])
                a_index = player_board.index(play[1])
                t = opponent_board[t_index]
                a = player_board[a_index]
                t[4] -= a[3]
                a[4] -= t[3]
                if t[4] <= 0:
                    opponent_board.remove(t)
                if a[4] <= 0:
                    player_board.remove(a)
        elif play[0] == "Play Spell":
            if play[2] == players[2]["Hero"]:
                life_dif -= play[1][3]
            else:
                t_index = opponent_board.index(play[2])
                a_index = players[1]["Hand"].index(play[1])
                t = opponent_board[t_index]
                a = players[1]["Hand"][a_index]
                t[4] -= a[3]
                if t[4] <= 0:
                    opponent_board.remove(t)
                players[1]["Hand"].remove(a)
        elif play[0] == "ARMOR UP!":
            life_dif += 2
    board_dif = (sum([x[3] + x[4] for x in players[1]["Current Board"]]) -
                sum([x[3] + x[4] for x in players[2]["Current Board"]]))
    hand_dif = len(players[1]["Hand"]) - len(players[2]["Hand"])
    post_value = life_dif + hand_dif + board_dif

    p = sigmoid((post_value-pre_value))[0]
    # is_True = 1 if pre_value < post_value else 0
    cost = deepcopy(results)
    for k in range(len(cost)):
        for i in range(len(cost[k][1])):
            for j in range(len(cost[k][1][i])):
                try:
                    cost[k][1][i][j] = (-1 * p * math.log(cost[k][1][i][j]) +
                                        ((1 - p) * math.log(1 - cost[k][1][i][j])))
                except ValueError:
                    print( cost[k][1][i][j])
                #              x, x_prime = sigmoid(cost[k][1][i][j])
                # cost[k][1][i][j] = (-(p/cost[k][1][i][j]) - ((1-p)/(1-cost[k][1][i][j])))*x


    return cost

def sigmoid(a):
    try:
        s = math.exp(a)/(math.exp(a) + 1)
        s_prime = s/(math.exp(a) + 1)
    except OverflowError:
        print(a)
    return s, s_prime


def sim_new_board(p):
    p2mana = int(p[2]["Mana"])
    if len(p[2]["Current Board"]) != 7:
        p[2]["Current Board"].append(('00', 'FAKE', p2mana, p2mana, p2mana, 0))

def sim_game_state():
    game = {"State": "IDLE", "Winner": None, "Loser": None}
    player = {}
    opponent = {}
    mana = rand.randint(1, 10)
    player["Hero"] = "HERO_01"
    opponent["Hero"] = "HERO_08"
    player["Hero Power"] = "CS2_102"
    opponent["Hero Power"] = "CS2_034"
    players = [game, player, opponent]

    player["Life"] = [rand.randint(0, 30), rand.randint(0, 30)]
    player["Mana"] = mana
    opponent["Life"] = [rand.randint(0, 30), rand.randint(0, 30)]
    opponent["Mana"] = mana
    player["Current Board"] = []
    player["Hand"] = []
    opponent["Current Board"] = []
    opponent["Hand"] = []

    for i in range(rand.randint(0, 6)):
        player["Current Board"].append([str(rand.randint(0, 5000)), 'Fake', rand.randint(0, 10),
                                        rand.randint(0, 10), rand.randint(0, 10), rand.randint(0, 10)])

    for i in range(rand.randint(0, 6)):
        player["Hand"].append([str(rand.randint(0, 5000)), 'Fake', rand.randint(0, 10),
                               rand.randint(0, 10), rand.randint(0, 10), rand.randint(0, 10)])

    for i in range(rand.randint(0, 6)):
        opponent["Current Board"].append([str(rand.randint(0, 5000)), 'Fake', rand.randint(0, 10),
                                          rand.randint(0, 10), rand.randint(0, 10), rand.randint(0, 10)])

    for i in range(rand.randint(0, 6)):
        opponent["Hand"].append([str(rand.randint(0, 5000)), 'Fake', rand.randint(0, 10),
                                 rand.randint(0, 10), rand.randint(0, 10), rand.randint(0, 10)])

    return players


def main(verbose=False, read_file=False, n=80, init=0):
    if read_file:
        players = logger.main()
        for x, y in players[1].items():
            print(x, y)
        for x, y in players[2].items():
            print(x, y)
    else:
        players = sim_game_state()
    iter = 0
    while iter < n:
        iter += 1

        player_mana = players[1]["Mana"]
        player_life = players[1]["Life"][0] + players[1]["Life"][1]
        opponent_life = players[2]["Life"][0] + players[2]["Life"][1]
        life_normal = max([player_life, opponent_life])

        player_hand = players[1]["Hand"]
        opponent_hand = players[2]["Hand"]
        if len(player_hand) > 0:
            hand_normal_p = [max([x[2] if x[2] > 0 else 1 for x in player_hand]),
                             max([x[3] if x[3] > 0 else 1 for x in player_hand]),
                             max([x[4] if x[4] > 0 else 1 for x in player_hand]),
                             max([x[5] if x[5] > 0 else 1 for x in player_hand])
                             ]
        else:
            hand_normal_p = [1, 1, 1, 1]
        if len(opponent_hand) > 0:
            hand_normal_o = [max([x[2] if x[2] > 0 else 1 for x in opponent_hand]),
                             max([x[3] if x[3] > 0 else 1 for x in opponent_hand]),
                             max([x[4] if x[4] > 0 else 1 for x in opponent_hand]),
                             max([x[5] if x[5] > 0 else 1 for x in opponent_hand])
                             ]
        else:
            hand_normal_o = [1, 1, 1, 1]
        hand_normal = [max([hand_normal_o[0], hand_normal_p[0]]),
                       max([hand_normal_o[1], hand_normal_p[1]]),
                       max([hand_normal_o[2], hand_normal_p[2]]),
                       max([hand_normal_o[3], hand_normal_p[3]]),
                       ]
        player_board = players[1]["Current Board"]
        opponent_board = players[2]["Current Board"]
        if len(player_board) > 0:
            board_normal_p = [max([x[2] if x[2] > 0 else 1 for x in player_board]),
                              max([x[3] if x[3] > 0 else 1 for x in player_board]),
                              max([x[4] if x[4] > 0 else 1 for x in player_board]),
                              max([x[5] if x[5] > 0 else 1 for x in player_board])
                              ]
        else:
            board_normal_p = [1, 1, 1, 1]
        if len(opponent_board) > 0:
            board_normal_o = [max([x[2] if x[2] > 0 else 1 for x in opponent_board]),
                              max([x[3] if x[3] > 0 else 1 for x in opponent_board]),
                              max([x[4] if x[4] > 0 else 1 for x in opponent_board]),
                              max([x[5] if x[5] > 0 else 1 for x in opponent_board])
                              ]
        else:
            board_normal_o = [1, 1, 1, 1]
        board_normal = [max([board_normal_o[0], board_normal_p[0]]),
                       max([board_normal_o[1], board_normal_p[1]]),
                       max([board_normal_o[2], board_normal_p[2]]),
                       max([board_normal_o[3], board_normal_p[3]]),
                       ]
        node_length = 10

        player_life_node = [player_life/life_normal for x in range(node_length)]
        opponent_life_node = [opponent_life/life_normal for x in range(node_length)]

        player_hand_node = [[abs(x[2]/hand_normal[0]), abs(x[3]/hand_normal[1]),
                             abs(x[4]/hand_normal[2]), abs(x[5]/hand_normal[3])] for
                            x in player_hand]
        opponent_hand_node = [[abs(x[2]/hand_normal[0]), abs(x[3]/hand_normal[1]),
                               abs(x[4]/hand_normal[2]), abs(x[5]/hand_normal[3])] for
                              x in opponent_hand]

        player_board_node = [[abs(x[2]/board_normal[0]), abs(x[3]/board_normal[1]),
                             abs(x[4]/board_normal[2]), abs(x[5]/board_normal[3])] for
                             x in player_board]
        opponent_board_node = [[abs(x[2]/board_normal[0]), abs(x[3]/board_normal[1]),
                                abs(x[4]/board_normal[2]), abs(x[5]/board_normal[3])] for
                               x in opponent_board]

        state_matrix = [player_life_node,
                        opponent_life_node,
                        player_hand_node,
                        opponent_hand_node,
                        player_board_node,
                        opponent_board_node]
        for x in state_matrix:
            for i in range(10 - len(x)):
                x.append([None])

        if iter == 1:
            try:
                if verbose:
                    print("================================================")
                    print("=====          Reading Weights            ======")
                    print("================================================")
                if not init:
                    weights = read_weights(WEIGHTS_FILE_NAME)
                    if iter == 1:
                        start_weights = deepcopy(weights)
                    print("\n============Weights at", iter, " =======================")
                    for z in range(4):
                        print(weights[2][3][z])
                    print("================================================\n")
                else:
                    weights = init_weights(len(state_matrix), len(state_matrix[0]))
                    print("===========Inital Weights=============")
                    for z in range(4):
                        print(weights[2][3][z])
                    print("================================================")
            except FileNotFoundError:
                if verbose:

                    print("================================================")
                    print("=====  No weights found making new ones   ======")
                    print("================================================")
                weights = init_weights(len(state_matrix), len(state_matrix[0]))
                print("===========Inital Weights=============")
                for z in range(4):
                    print(weights[2][3][z])
                print("================================================")
                write_weights(WEIGHTS_FILE_NAME, weights)

        results = [("PLAY_nodes", []), ("ATTK_nodes", []), ("TRGT_nodes", []), ("HPWR_nodes", [])]
        if verbose:
            print("================================================")
            print("=====       Running Nodes                 ======")
            print("================================================")

        for i in range(3):
            results[0][1].append(get_play(weights[0][i], state_matrix, player_mana, i, cost=True))
            results[1][1].append(get_play(weights[1][i], state_matrix, player_mana, i))
            results[2][1].append(get_play(weights[2][i], state_matrix, player_mana, i))
            results[3][1].append(get_play(weights[3][i], state_matrix, player_mana, i))

        for i in range(3):
            results[0][1].append(get_play(weights[0][i+3], state_matrix, player_mana, i, order=False, cost=True))
            results[1][1].append(get_play(weights[1][i+3], state_matrix, player_mana, i, order=False))
            results[2][1].append(get_play(weights[2][i+3], state_matrix, player_mana, i, order=False))
            results[3][1].append(get_play(weights[3][i+3], state_matrix, player_mana, i, order=False))
        if verbose:
            print("================================================")
            print("=====       Select Move                   ======")
            print("================================================")

        best = []
        for i in range(len(results)):
            top = [-1]
            for j in range(len(results[i][1])):
                if j > 3:
                    rev = False
                else:
                    rev = True
                sub_best = max(results[i][1][j])
                if sub_best > top[0]:
                    top = [sub_best, j, results[i][1][j].index(sub_best), rev]
            best.append(top)
        try:
            best_play = sorted(player_hand, key=lambda x: x[best[0][2]], reverse=best[0][3])[best[0][1]]
        except IndexError:
            best_play = None
        try:
            best_attk = sorted(player_board, key=lambda x: x[best[1][2]], reverse=best[1][3])[best[1][1]]
        except IndexError:
            best_attk = None

        try:
            if best[2][0] > FACE_THRESHOLD:
                best_trgt = sorted(opponent_board, key=lambda x: x[best[2][2]], reverse=best[2][3])[best[2][1]]
            else:
                best_trgt = players[2]['Hero']
        except IndexError:
            best_trgt = None

        try:
            if best[3][0] > HPWR_THRESHOLD:
                best_hprw = True
            else:
                best_hprw = False
        except IndexError:
            best_hprw = None

        is_valid = validate(best_play, best_attk, best_trgt, best_hprw, players)
        play = select_valid(is_valid, [best_play, best_attk, best_trgt, best_hprw], players)
        if read_file:
            print("NEXT PLAY TO MAKE:", play)
        if verbose:
            print("================================================")
            print("=====       UPDATE WEIGHTS                ======")
            print("================================================")

        cost = get_cost(results, is_valid, play, players)
        for k in range(len(weights)):
            for i in range(len(weights[k])):
                update = cost[k][1][i]
                ln_res = results[k][1][i]
                for j in range(len(weights[k][i])):
                    for l in range(len(weights[k][i][j])):
                        weights[k][i][j][l] -= (2*sigmoid(update[j])[0]-1) *\
                                               math.log(ln_res[j])/(60*(1-weights[k][i][j][l]))
                        if weights[k][i][j][l] < 0:
                            weights[k][i][j][l] = 0
                        if weights[k][i][j][l] > 2:
                            weights[k][i][j][l] = 2

        if read_file:
            break
        players = sim_game_state()

    write_weights(WEIGHTS_FILE_NAME, weights)
    print("\n============Weights at", iter, " =======================")
    for z in range(4):
        print(weights[2][3][z])
    print("================================================\n")
    total_delta = 0
    for z in range(len(weights)):
        for x in range(len(weights[z])):
            for y in range(len(weights[z][x])):
                for w in range(len(weights[z][x][y])):
                    start_weights[z][x][y][w] -= weights[z][x][y][w]
                    total_delta += abs(start_weights[z][x][y][w])
    print("\n============Weights at", iter, " =======================")
    for z in range(4):
        print(start_weights[2][3][z])
    print("================================================\n")
    print(total_delta)
if __name__ == "__main__":
    init = 0
    if init:
        main(init=init, n=1)
    else:
        main(read_file=True, n=5000)
        main(n=50000)
        main(read_file=True, n=5000)
