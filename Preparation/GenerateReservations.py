import json
import math
import random

f = open("players.txt", "r")
data = f.read().strip().split('\n')
f.close()

data = [d.split('\t') for d in data]
num_pairs = int(len(data) / 2)
num_tables = math.ceil(num_pairs / 2)

pairs = [[data[i][0], data[i + num_pairs][0]] for i in range(num_pairs)]

random.shuffle(pairs)

reservations = {}
reservations["num_tables"] = num_tables
reservations["prevent_unreserved_login"] = False
reservations["seat_assignments"] = []

tables = [pairs[n:n+2] for n in range(0, len(pairs), 2)]
print(tables)

for i, table in enumerate(tables):
    table[0] = random.sample(table[0], 2)
    table[1] = random.sample(table[1], 2)
    
    reservation = {}
    reservation["n"] = table[0][0]
    reservation["s"] = table[0][1]
    reservation["e"] = table[1][0]
    reservation["w"] = table[1][1]
    reservation["table"] = i + 1
    
    reservations["seat_assignments"].append(reservation)

print(reservations)

with open("reservations.json", "w") as outfile:  
    json.dump(reservations, outfile) 

