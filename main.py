import numpy as np

#######################
# Oeconomica AI player#
#######################

# Notes:
# can participate in practice mode, 2-5 player games

#simple game with one AI player switch
play_simple_game = 1

#depth of minmax tree
max_round_depth = 3 # finish x + 0th round

###################
# Prior game setup#
###################

# define function for general inputs
def gen_input(prompt, type_=None, min_=None, max_=None, range_=None):
    if min_ is not None and max_ is not None and max_ < min_:
        raise ValueError("min_ must be less than or equal to max_.")
    while True:
        ui = input(prompt)
        if type_ is not None:
            try:
                ui = type_(ui)
            except ValueError:
                print("Input type must be {0}.".format(type_.__name__))
                continue
        if max_ is not None and ui > max_:
            print("Input must be less than or equal to {0}.".format(max_))
        elif min_ is not None and ui < min_:
            print("Input must be greater than or equal to {0}.".format(min_))
        elif range_ is not None and ui not in range_:
            if isinstance(range_, range):
                template = "Input must be between {0.start} and {0.stop}."
                print(template.format(range_))
            else:
                template = "Input must be {0}."
                if len(range_) == 1:
                    print(template.format(*range_))
                else:
                    print(template.format(" or ".join((", ".join(map(str,
                                                                     range_[:-1])),
                                                       str(range_[-1])))))
        else:
            return ui

# player info setup
npl = gen_input("Enter number of players (2 to 5): ", int, 2, 5)  # number of players
ai_pos = gen_input("Enter position of AI player: ", int, 1, npl) - 1  # position of AI player, -1 for proper python order in sequences

# game objects initialization
energy_price = 3
energy_supply = 0
energy_demand = 0

transport_price = 4
transport_supply = 0
transport_demand = 0

pl_free_man = np.zeros(npl,dtype=np.int)  # free managers for players in respective collumns
for i in range(0,npl):
    pl_free_man[i] = 4

pl_money = np.zeros(npl,dtype=np.int)  # money stack of players in respective collumns
for i in range(0,npl):
    pl_money[i] = 5

list_companies = ['elektrarna','automobilka','dopravce','it_firma']
companies = np.zeros((npl,4, 3),dtype=np.int)  # player X company X level (clockwise starting from bottom)

###################################################
# Defining procedures of individual player actions#
###################################################

#procedure to place a manager
def place_man(pl):
    pl_money[pl] = pl_money[pl]-4  # cost of placing 4

    pl_free_man[pl] = pl_free_man[pl]-1  # remove a free manager

    place_company_to = gen_input("Enter company to: ", str.lower, range_=list_companies) #which company to place a new manager in
    companies[pl,list_companies.index(place_company_to),0] = companies[pl,list_companies.index(place_company_to),0]+1

# procedure to move a manager
def move_man(pl):
    pl_money[pl] = pl_money[pl]-1 # cost of moving 1

    move_company_from = gen_input("Enter company from: ", str.lower, range_=list_companies) #from which company to withdraw
    move_level_from = gen_input("Enter level from: ", int, 1, 3)-1 #from what level to withdraw, -1 for python
    companies[pl,list_companies.index(move_company_from),move_level_from] = companies[pl,list_companies.index(move_company_from),move_level_from]-1

    move_company_to = gen_input("Enter company to: ", str.lower, range_=list_companies) #to which company to move
    move_level_to = gen_input("Enter level to: ", int, 1, 3)-1 #to what level to move, -1 for python
    companies[pl,list_companies.index(move_company_to),move_level_to] = companies[pl,list_companies.index(move_company_to),move_level_to]+1

# function seeking for optimal AI player action based on the minmax algorithm
def ai_action(game_round, companies, pl_money, pl_free_man, energy_price, transport_price):

    current_ai_pos = np.roll(np.arange(npl),-game_round).tolist().index(ai_pos)  # position(index) of AI player in a given round
    max_depth = npl - current_ai_pos + max_round_depth * npl

    # initialize key driving vectors
    who_on_turn = np.zeros(max_depth,dtype=np.int)
    end_of_turn = np.zeros(max_depth,dtype=np.int)
    turn_value = np.zeros(max_depth,dtype=np.int)

    # initialize vector to save optimal action
    action_optimal = np.zeros(6,dtype=np.int)
    action_temporary = np.zeros(6,dtype=np.int)

    #initialize key driving matrices
    companies_mat = np.zeros((max_depth+1, npl, 4, 3),dtype=np.int)  # depth X player X company X level (clockwise starting from bottom)
    companies_mat[0,:,:,:] = companies

    pl_money_mat = np.zeros((max_depth+1, npl),dtype=np.int)  # depth X player
    pl_money_mat[0,:] = pl_money

    pl_free_man_mat = np.zeros((max_depth+1, npl),dtype=np.int) # depth X player
    pl_free_man_mat[0,:] = pl_free_man

    energy_price_mat = np.zeros(max_depth+1,dtype=np.int)
    energy_price_mat[0] = energy_price

    transport_price_mat = np.zeros(max_depth+1,dtype=np.int)
    transport_price_mat[0] = transport_price

    # who plays which turn
    for j in range(0,npl - current_ai_pos): # 0th round (from AI further)
        who_on_turn[j] = np.roll(np.arange(npl),-game_round).tolist()[j+current_ai_pos]

    for j in range(1,max_round_depth+1): # rest of full rounds
      who_on_turn[(j*npl - current_ai_pos):(j+1)*npl - current_ai_pos] = np.roll(np.arange(npl),-(game_round+j))


    # is this the last player move in this round ?
    for j in range(1,max_round_depth+2):
        end_of_turn[j*npl - current_ai_pos-1] = 1

    # the value to which the comparison should be initially made in a given turn (max for AI, min for non-AI)
    for j in range(0,max_depth):
        if who_on_turn[j] == ai_pos:
            turn_value[j] = -1000
        else:
            turn_value[j] = 1000

    # definition of minmax procedure
    def minmax(depth):
        if depth < max_depth:

            # basic transfer to next turn
            companies_mat[depth+1, :, :, :] = companies_mat[depth, :, :, :]
            pl_money_mat[depth+1, :] = pl_money_mat[depth, :]
            pl_free_man_mat[depth+1, :] = pl_free_man_mat[depth, :]
            energy_price_mat[depth+1]=energy_price_mat[depth]
            transport_price_mat[depth+1]=transport_price_mat[depth]

            # pass
            if depth == 0:  # saving potentially optimal action
                action_temporary[0] = 0

            trans_proc_pass(depth)

            # place
            if (pl_money_mat[depth, who_on_turn[depth]] >= 4) and (pl_free_man_mat[depth, who_on_turn[depth]] >= 1): # if feasible

                for c in range(0,4): # for all of the 4 companies
                    # move forward
                    pl_free_man_mat[depth+1, who_on_turn[depth]] = pl_free_man_mat[depth,who_on_turn[depth]]-1  # remove a free manager
                    companies_mat[depth+1, who_on_turn[depth],c,0] = companies_mat[depth, who_on_turn[depth],c,0]+1 # place the manager

                    if depth == 0:  # saving potentially optimal action
                        action_temporary[0] = 1
                        action_temporary[1] = c

                    trans_proc_place(depth)

                    # move backward (reset state before choice of another action
                    companies_mat[depth+1, :, :, :] = companies_mat[depth, :, :, :]
                    pl_money_mat[depth+1, :] = pl_money_mat[depth, :]

            # move
            if (pl_money_mat[depth, who_on_turn[depth]] >= 1): # if feasible

                for cf in range(0,4): # from all of the 4 companies
                    for lf in range(0,3): # from all of the 3 levels

                        if (companies_mat[depth, who_on_turn[depth],cf,lf] >= 1): # if there is anything to be moved with

                            for ct in range(0,4): # to all of the 4 companies
                                for lt in range(0,3): # to all of the 3 levels

                                    if (cf == ct and lf != lt) or (cf != ct and lf == 0 and lt == 0):

                                        # move forward
                                        companies_mat[depth+1, who_on_turn[depth],cf,lf] = companies_mat[depth, who_on_turn[depth],cf,lf]-1  # move a manager from
                                        companies_mat[depth+1, who_on_turn[depth],ct,lt] = companies_mat[depth, who_on_turn[depth],ct,lt]+1 # move a manager to

                                        if depth == 0:  # saving potentially optimal action
                                            action_temporary[0] = 2
                                            action_temporary[2] = cf
                                            action_temporary[3] = lf
                                            action_temporary[4] = ct
                                            action_temporary[5] = lt

                                        trans_proc_move(depth)

                                        # move backward (reset state before choice of another action
                                        companies_mat[depth+1, :, :, :] = companies_mat[depth, :, :, :]
                                        pl_money_mat[depth+1, :] = pl_money_mat[depth, :]


            if depth > 0:
                # sending the minmax value up the tree
                if who_on_turn[depth-1] == ai_pos:  # last player is the AI

                    if depth == 1:  # saving optimal action
                        if turn_value[depth] >= turn_value[depth-1]:
                            for a in range(0,6):
                                action_optimal[a]=action_temporary[a]

                    turn_value[depth-1] = max(turn_value[depth-1], turn_value[depth])

                else:  # last player is the regular non-AI player
                    turn_value[depth-1] = min(turn_value[depth-1], turn_value[depth])

                # cleaning the current level
                if who_on_turn[depth] == ai_pos:
                    turn_value[depth] = -1000
                else:
                    turn_value[depth] = 1000

    # definition of transition procedures between minmax recursion steps
    def trans_proc_pass(depth):
        if end_of_turn[depth] == 1:
                # production (payout) phase
                for k in range(0,npl):
                    pl_money_mat[depth+1, k] = pl_money_mat[depth, k] + (
                    # elektrarna
                        companies_mat[depth+1,k,0,0] * (energy_price_mat[depth] - 2) +
                        companies_mat[depth+1,k,0,1] * (2 * energy_price_mat[depth] - 4) +
                        companies_mat[depth+1,k,0,2] * (energy_price_mat[depth] - 1) +
                    # automobilka
                        companies_mat[depth+1,k,1,0] * (transport_price_mat[depth] - energy_price_mat[depth]) +
                        companies_mat[depth+1,k,1,1] * (transport_price_mat[depth] - 2) +
                        companies_mat[depth+1,k,1,2] * (2 * transport_price_mat[depth] - 2 * energy_price_mat[depth]) +
                    # dopravce
                        companies_mat[depth+1,k,2,0] * (5 - transport_price_mat[depth]) +
                        companies_mat[depth+1,k,2,1] * (9 - transport_price_mat[depth] - energy_price_mat[depth]) +
                        companies_mat[depth+1,k,2,2] * (10 - 2 * transport_price_mat[depth]) +
                    # it_firma
                        companies_mat[depth+1,k,3,0] * (4 - energy_price_mat[depth]) +
                        companies_mat[depth+1,k,3,1] * (8 - 2 * energy_price_mat[depth]) +
                        companies_mat[depth+1,k,3,2] * (5 - energy_price_mat[depth])
                    )
                # price adjustment phase - market supply & demand
                energy_supply = (
                # elektrarna
                    sum(companies_mat[depth+1,:,0,0]) * 1 +
                    sum(companies_mat[depth+1,:,0,1]) * 2 +
                    sum(companies_mat[depth+1,:,0,2]) * 1
                )

                energy_demand = (
                # automobilka
                    sum(companies_mat[depth+1,:,1,0]) * 1 +
                    sum(companies_mat[depth+1,:,1,2]) * 2 +
                # dopravce
                    sum(companies_mat[depth+1,:,2,1]) * 1 +
                # it_firma
                    sum(companies_mat[depth+1,:,3,0]) * 1 +
                    sum(companies_mat[depth+1,:,3,1]) * 2 +
                    sum(companies_mat[depth+1,:,3,2]) * 1
                )

                transport_supply = (
                    # automobilka
                    sum(companies_mat[depth+1,:,1,0]) * 1 +
                    sum(companies_mat[depth+1,:,1,1]) * 1 +
                    sum(companies_mat[depth+1,:,1,2]) * 2
                )

                transport_demand = (
                    # dopravce
                    sum(companies_mat[depth+1,:,2,0]) * 1 +
                    sum(companies_mat[depth+1,:,2,1]) * 1 +
                    sum(companies_mat[depth+1,:,2,2]) * 2
                )

                # price adjustment phase - market prices
                if (energy_supply > energy_demand) and (energy_price_mat[depth]>1):
                    energy_price_mat[depth+1] = energy_price_mat[depth] - 1
                elif (energy_supply < energy_demand) and (energy_price_mat[depth]<5):
                    energy_price_mat[depth+1] = energy_price_mat[depth] + 1
                else:
                    energy_price_mat[depth+1] = energy_price_mat[depth]

                if (transport_supply > transport_demand) and (transport_price_mat[depth]>2):
                    transport_price_mat[depth+1] = transport_price_mat[depth] - 1
                elif (transport_supply < transport_demand) and (transport_price_mat[depth]<6):
                    transport_price_mat[depth+1] = transport_price_mat[depth] + 1
                else:
                    transport_price_mat[depth+1] = transport_price_mat[depth]


        depth = depth + 1 # push turn forward

        # static value evaluation if it is already deep enough, else recursion
        if depth == max_depth:
            if who_on_turn[max_depth-1] == ai_pos:  # last player is the AI
                turn_value[max_depth-1] = max(turn_value[max_depth-1],pl_money_mat[max_depth, ai_pos])
            else:  # last player is the regular non-AI player
                turn_value[max_depth-1] = min(turn_value[max_depth-1],pl_money_mat[max_depth, ai_pos])
        else:
            minmax(depth)  # recursion

    def trans_proc_place(depth):
        if end_of_turn[depth] == 1:
                # production (payout) phase
                for k in range(0,npl):
                    pl_money_mat[depth+1, k] = pl_money_mat[depth, k] + (
                    # elektrarna
                        companies_mat[depth+1,k,0,0] * (energy_price_mat[depth] - 2) +
                        companies_mat[depth+1,k,0,1] * (2 * energy_price_mat[depth] - 4) +
                        companies_mat[depth+1,k,0,2] * (energy_price_mat[depth] - 1) +
                    # automobilka
                        companies_mat[depth+1,k,1,0] * (transport_price_mat[depth] - energy_price_mat[depth]) +
                        companies_mat[depth+1,k,1,1] * (transport_price_mat[depth] - 2) +
                        companies_mat[depth+1,k,1,2] * (2 * transport_price_mat[depth] - 2 * energy_price_mat[depth]) +
                    # dopravce
                        companies_mat[depth+1,k,2,0] * (5 - transport_price_mat[depth]) +
                        companies_mat[depth+1,k,2,1] * (9 - transport_price_mat[depth] - energy_price_mat[depth]) +
                        companies_mat[depth+1,k,2,2] * (10 - 2 * transport_price_mat[depth]) +
                    # it_firma
                        companies_mat[depth+1,k,3,0] * (4 - energy_price_mat[depth]) +
                        companies_mat[depth+1,k,3,1] * (8 - 2 * energy_price_mat[depth]) +
                        companies_mat[depth+1,k,3,2] * (5 - energy_price_mat[depth])
                    )
                # price adjustment phase - market supply & demand
                energy_supply = (
                # elektrarna
                    sum(companies_mat[depth+1,:,0,0]) * 1 +
                    sum(companies_mat[depth+1,:,0,1]) * 2 +
                    sum(companies_mat[depth+1,:,0,2]) * 1
                )

                energy_demand = (
                # automobilka
                    sum(companies_mat[depth+1,:,1,0]) * 1 +
                    sum(companies_mat[depth+1,:,1,2]) * 2 +
                # dopravce
                    sum(companies_mat[depth+1,:,2,1]) * 1 +
                # it_firma
                    sum(companies_mat[depth+1,:,3,0]) * 1 +
                    sum(companies_mat[depth+1,:,3,1]) * 2 +
                    sum(companies_mat[depth+1,:,3,2]) * 1
                )

                transport_supply = (
                    # automobilka
                    sum(companies_mat[depth+1,:,1,0]) * 1 +
                    sum(companies_mat[depth+1,:,1,1]) * 1 +
                    sum(companies_mat[depth+1,:,1,2]) * 2
                )

                transport_demand = (
                    # dopravce
                    sum(companies_mat[depth+1,:,2,0]) * 1 +
                    sum(companies_mat[depth+1,:,2,1]) * 1 +
                    sum(companies_mat[depth+1,:,2,2]) * 2
                )

                # price adjustment phase - market prices
                if (energy_supply > energy_demand) and (energy_price_mat[depth]>1):
                    energy_price_mat[depth+1] = energy_price_mat[depth] - 1
                elif (energy_supply < energy_demand) and (energy_price_mat[depth]<5):
                    energy_price_mat[depth+1] = energy_price_mat[depth] + 1
                else:
                    energy_price_mat[depth+1] = energy_price_mat[depth]

                if (transport_supply > transport_demand) and (transport_price_mat[depth]>2):
                    transport_price_mat[depth+1] = transport_price_mat[depth] - 1
                elif (transport_supply < transport_demand) and (transport_price_mat[depth]<6):
                    transport_price_mat[depth+1] = transport_price_mat[depth] + 1
                else:
                    transport_price_mat[depth+1] = transport_price_mat[depth]


        pl_money_mat[depth+1, who_on_turn[depth]] = pl_money_mat[depth+1, who_on_turn[depth]] - 4 #cost of placing for the given player

        depth = depth + 1 # push turn forward

        # static value evaluation if it is already deep enough, else recursion
        if depth == max_depth:
            if who_on_turn[max_depth-1] == ai_pos: # last player is the AI
                turn_value[max_depth-1] = max(turn_value[max_depth-1],pl_money_mat[max_depth, ai_pos])
            else: # last player is the regular non-AI player
                turn_value[max_depth-1] = min(turn_value[max_depth-1],pl_money_mat[max_depth, ai_pos])
        else:
            minmax(depth) # recursion

    def trans_proc_move(depth):
        if end_of_turn[depth] == 1:
                # production (payout) phase
                for k in range(0,npl):
                    pl_money_mat[depth+1, k] = pl_money_mat[depth, k] + (
                    # elektrarna
                        companies_mat[depth+1,k,0,0] * (energy_price_mat[depth] - 2) +
                        companies_mat[depth+1,k,0,1] * (2 * energy_price_mat[depth] - 4) +
                        companies_mat[depth+1,k,0,2] * (energy_price_mat[depth] - 1) +
                    # automobilka
                        companies_mat[depth+1,k,1,0] * (transport_price_mat[depth] - energy_price_mat[depth]) +
                        companies_mat[depth+1,k,1,1] * (transport_price_mat[depth] - 2) +
                        companies_mat[depth+1,k,1,2] * (2 * transport_price_mat[depth] - 2 * energy_price_mat[depth]) +
                    # dopravce
                        companies_mat[depth+1,k,2,0] * (5 - transport_price_mat[depth]) +
                        companies_mat[depth+1,k,2,1] * (9 - transport_price_mat[depth] - energy_price_mat[depth]) +
                        companies_mat[depth+1,k,2,2] * (10 - 2 * transport_price_mat[depth]) +
                    # it_firma
                        companies_mat[depth+1,k,3,0] * (4 - energy_price_mat[depth]) +
                        companies_mat[depth+1,k,3,1] * (8 - 2 * energy_price_mat[depth]) +
                        companies_mat[depth+1,k,3,2] * (5 - energy_price_mat[depth])
                    )
                # price adjustment phase - market supply & demand
                energy_supply = (
                # elektrarna
                    sum(companies_mat[depth+1,:,0,0]) * 1 +
                    sum(companies_mat[depth+1,:,0,1]) * 2 +
                    sum(companies_mat[depth+1,:,0,2]) * 1
                )

                energy_demand = (
                # automobilka
                    sum(companies_mat[depth+1,:,1,0]) * 1 +
                    sum(companies_mat[depth+1,:,1,2]) * 2 +
                # dopravce
                    sum(companies_mat[depth+1,:,2,1]) * 1 +
                # it_firma
                    sum(companies_mat[depth+1,:,3,0]) * 1 +
                    sum(companies_mat[depth+1,:,3,1]) * 2 +
                    sum(companies_mat[depth+1,:,3,2]) * 1
                )

                transport_supply = (
                    # automobilka
                    sum(companies_mat[depth+1,:,1,0]) * 1 +
                    sum(companies_mat[depth+1,:,1,1]) * 1 +
                    sum(companies_mat[depth+1,:,1,2]) * 2
                )

                transport_demand = (
                    # dopravce
                    sum(companies_mat[depth+1,:,2,0]) * 1 +
                    sum(companies_mat[depth+1,:,2,1]) * 1 +
                    sum(companies_mat[depth+1,:,2,2]) * 2
                )

                # price adjustment phase - market prices
                if (energy_supply > energy_demand) and (energy_price_mat[depth]>1):
                    energy_price_mat[depth+1] = energy_price_mat[depth] - 1
                elif (energy_supply < energy_demand) and (energy_price_mat[depth]<5):
                    energy_price_mat[depth+1] = energy_price_mat[depth] + 1
                else:
                    energy_price_mat[depth+1] = energy_price_mat[depth]

                if (transport_supply > transport_demand) and (transport_price_mat[depth]>2):
                    transport_price_mat[depth+1] = transport_price_mat[depth] - 1
                elif (transport_supply < transport_demand) and (transport_price_mat[depth]<6):
                    transport_price_mat[depth+1] = transport_price_mat[depth] + 1
                else:
                    transport_price_mat[depth+1] = transport_price_mat[depth]


        pl_money_mat[depth+1, who_on_turn[depth]] = pl_money_mat[depth+1, who_on_turn[depth]] - 1 #cost of moving for the given player

        depth = depth + 1 # push turn forward

        # static value evaluation if it is already deep enough, else recursion
        if depth == max_depth:
            if who_on_turn[max_depth-1] == ai_pos: # last player is the AI
                turn_value[max_depth-1] = max(turn_value[max_depth-1],pl_money_mat[max_depth, ai_pos])
            else: # last player is the regular non-AI player
                turn_value[max_depth-1] = min(turn_value[max_depth-1],pl_money_mat[max_depth, ai_pos])
        else:
            minmax(depth) # recursion

    #Min-max recursion
    depth = 0 # initial depth
    minmax(depth)

    # return the optimal action for AI player found based on the minmax algorithm
    return action_optimal



######################################
# Simple Game play with one AI player#
######################################

if play_simple_game == 1:
    # main while loop for rounds of the game: start
    game_round = 0
    while max(pl_money) < 12:

        # investment phase
        pl_order = np.roll(np.arange(npl),-game_round)  # player order, rolling clockwise each round

        for i in pl_order:
            print("Round "+str(game_round+1)+" Player "+str(i+1)+".")

            if i != ai_pos:

                investment_dec = gen_input("Enter investment decision (place/move/pass): ", str.lower, range_=('place','move','pass'))
                if investment_dec == 'place':
                    place_man(i)
                elif investment_dec == 'move':
                    move_man(i)

            else:
                ai_act = ai_action(game_round, companies, pl_money, pl_free_man, energy_price, transport_price)

                if ai_act[0] == 0: # pass
                    print("AI player action: pass.")

                elif ai_act[0] == 1: # place
                    pl_money[ai_pos] = pl_money[ai_pos]-4  # cost of placing 4
                    pl_free_man[ai_pos] = pl_free_man[ai_pos]-1  # remove a free manager

                    companies[ai_pos, ai_act[1], 0] = companies[ai_pos, ai_act[1], 0]+1 #which company to place a new manager in

                    print("AI player action: place a manager to company "+str(list_companies[ai_act[1]])+".")

                elif ai_act[0] == 2: # move
                    pl_money[ai_pos] = pl_money[ai_pos]-1  # cost of moving 1

                    companies[ai_pos,ai_act[2],ai_act[3]] = companies[ai_pos,ai_act[2],ai_act[3]]-1
                    companies[ai_pos,ai_act[4],ai_act[5]] = companies[ai_pos,ai_act[4],ai_act[5]]+1

                    print("AI player action: move a manager from company "+
                    str(list_companies[ai_act[2]])+" level "+str(ai_act[3]+1)+", to company "+
                    str(list_companies[ai_act[4]])+" level "+str(ai_act[5]+1)+".")

        # production (payout) phase
        for i in range(0,npl):
            pl_money[i] = pl_money[i] + (
            # elektrarna
                companies[i,0,0] * (energy_price - 2) +
                companies[i,0,1] * (2 * energy_price - 4) +
                companies[i,0,2] * (energy_price - 1) +
            # automobilka
                companies[i,1,0] * (transport_price - energy_price) +
                companies[i,1,1] * (transport_price - 2) +
                companies[i,1,2] * (2 * transport_price - 2 * energy_price) +
            # dopravce
                companies[i,2,0] * (5 - transport_price) +
                companies[i,2,1] * (9 - transport_price - energy_price) +
                companies[i,2,2] * (10 - 2 * transport_price) +
            # it_firma
                companies[i,3,0] * (4 - energy_price) +
                companies[i,3,1] * (8 - 2 * energy_price) +
                companies[i,3,2] * (5 - energy_price)
            )
        # price adjustment phase - market supply & demand
        energy_supply = (
        # elektrarna
            sum(companies[:,0,0]) * 1 +
            sum(companies[:,0,1]) * 2 +
            sum(companies[:,0,2]) * 1
        )

        energy_demand = (
        # automobilka
            sum(companies[:,1,0]) * 1 +
            sum(companies[:,1,2]) * 2 +
        # dopravce
            sum(companies[:,2,1]) * 1 +
        # it_firma
            sum(companies[:,3,0]) * 1 +
            sum(companies[:,3,1]) * 2 +
            sum(companies[:,3,2]) * 1
        )

        transport_supply = (
            # automobilka
            sum(companies[:,1,0]) * 1 +
            sum(companies[:,1,1]) * 1 +
            sum(companies[:,1,2]) * 2
        )

        transport_demand = (
            # dopravce
            sum(companies[:,2,0]) * 1 +
            sum(companies[:,2,1]) * 1 +
            sum(companies[:,2,2]) * 2
        )

        # price adjustment phase - market prices
        if energy_supply > energy_demand:
            energy_price = energy_price - 1
        elif energy_supply < energy_demand:
            energy_price = energy_price + 1

        if transport_supply > transport_demand:
            transport_price = transport_price - 1
        elif transport_supply < transport_demand:
            transport_price = transport_price + 1

        # check for win condition at the end of the round
        if max(pl_money) >= 12:
            print("Game over!")
            for i in range(0,npl):
                print("Player "+str(i+1)+" final score: "+str(pl_money[i]))
            break

        game_round = game_round + 1
# main while loop for rounds of the game: end
