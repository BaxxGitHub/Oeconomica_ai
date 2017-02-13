import numpy as np

#######################
# Oeconomica AI player#
#######################

# Notes:
# can participate in practice mode, 2-5 player games

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


############
# Game play#
############

# main while loop for rounds of the game: start
game_round = 0
while max(pl_money) < 12:
    # investment phase
    pl_order = np.roll(np.arange(npl),-game_round)  # player order, rolling clockwise each round
    for i in pl_order:
        print("Round "+str(game_round+1)+" Player "+str(i+1)+".")
        investment_dec = gen_input("Enter investment decision (place/move/pass): ", str.lower, range_=('place','move','pass'))
        if investment_dec == 'place':
            place_man(i)
        elif investment_dec == 'move':
            move_man(i)


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

#print check
#print(companies)