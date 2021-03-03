player_link = input("Enter player link: ")
director_link = input("Enter director link: ")
f = open("players.txt", "r")
data = f.read().strip().split('\n')
f.close()

data = [d.split('\t') for d in data]
data = ["{},{},{},{}\n".format(d[0], player_link + "&n={}".format(d[0].replace(" ", "%20").replace('"', "%22")), director_link + "&n={}".format(d[0].replace(" ", "%20").replace('"', "%22")), d[1]) for d in data]

print(data)

f = open("players.csv", "w")
f.writelines(data)