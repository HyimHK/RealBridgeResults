import xmltodict
import sys
import pprint

html_start = """<!DOCTYPE html>
<html>
<head>
<title>RealBridge Result</title>
<style>
table, th, td {
  padding: 5px;
  border: 1px solid black;
  border-collapse: collapse;
}
th {
  text-align: left;
}
tr.target {
background-color: #fff133
}
</style>
</head>
<body>
"""

html_end = """</body>
</html>
"""

board_script = """
<script>
const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const pair_index = urlParams.get('pair')
</script> 
"""

def strip_chars(name):
    for c in ["/", "\\", ":", "*", "?", "\"", "<", ">", "|"]:
        name = name.replace(c, "")
    return name

def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default

def suit_symbols(s):
    return s.replace("H", "\u2661").replace("S", "\u2660").replace("D", "\u2662").replace("C", "\u2663")
    
def parse_contract(traveler):
    level = safe_cast(traveler.get('CONTRACT', '---')[0], int, 0)
    tricks_taken = safe_cast(traveler.get('TRICKS', 0), int )
    played_by = traveler.get('PLAYED_BY', '')
    result = "" if not level else tricks_taken - (level + 6)
    if result != "":
        result = str(result) if result < 0 else "=" if not result else "+" + str(result)
    return suit_symbols(traveler.get('CONTRACT', '---').replace("PASS", "P")) + played_by + str(result)

f = open(sys.argv[1])
data = f.readlines()
f.close()

data = "".join([d.strip() for d in data])
data = xmltodict.parse(data)

participants = data['USEBIO']['EVENT']['PARTICIPANTS']
pairs = { pair['PAIR_NUMBER']:" and ".join([x['PLAYER_NAME'] for x in pair['PLAYER']]) for pair in participants['PAIR'] } \
if 'PAIRS' in data['USEBIO']['EVENT']['@EVENT_TYPE'] else \
{ pair['PAIR_NUMBER']:" & ".join([x['PLAYER_NAME'] for x in pair['PLAYER']]) for team in participants['TEAM'] for pair in team['PAIR']}

rankings = { pair['PAIR_NUMBER']:pair['PLACE'] for pair in participants['PAIR']} \
    if data['USEBIO']['EVENT']['WINNER_TYPE'] == "1" \
    else { pair['PAIR_NUMBER']:" ".join([pair['PLACE'], pair['DIRECTION']]) for pair in participants['PAIR']}

results = {}

if data['USEBIO']['EVENT']['@EVENT_TYPE'] == 'SWISS_PAIRS':
    for match in data['USEBIO']['EVENT']['MATCH']:
        for board in match["BOARD"]:
            board_number = board['BOARD_NUMBER']
            
            contract = parse_contract(board['TRAVELLER_LINE'])
            traveler = [board_number, 
                pairs[match['NS_PAIR_NUMBER']],
                pairs[match['EW_PAIR_NUMBER']],
                contract,
                suit_symbols(board['TRAVELLER_LINE'].get('LEAD', '---')),
                safe_cast(board['TRAVELLER_LINE']['SCORE'], int, 0),
                -safe_cast(board['TRAVELLER_LINE']['SCORE'], int, 0),
                float(board['TRAVELLER_LINE']['NS_CROSS_IMP_POINTS']),
                float(board['TRAVELLER_LINE']['EW_CROSS_IMP_POINTS']),
                "https://www.bridgebase.com/tools/handviewer.html?lin=" + board['TRAVELLER_LINE']['LIN_DATA']
            ]
            
            if board_number not in results.keys():
                results[board_number] = [traveler]
            else:
                results[board_number].append(traveler)
    pass
else:
    boards = data['USEBIO']['EVENT']['BOARD'] \
    if data['USEBIO']['EVENT']['@EVENT_TYPE'] == 'PAIRS' else \
    [board for match in data['USEBIO']['EVENT']['MATCH'] for board in match['BOARD']]
    for board in boards:
        board_number = board['BOARD_NUMBER']
        
        for traveler in board['TRAVELLER_LINE']:
            contract = parse_contract(traveler)
            traveler = [board_number, 
                        pairs[traveler['NS_PAIR_NUMBER']],
                        pairs[traveler['EW_PAIR_NUMBER']],
                        contract,
                        traveler.get('LEAD', '---'),
                        safe_cast(traveler['SCORE'], int, 0),
                        -safe_cast(traveler['SCORE'], int, 0),
                        float(traveler['NS_CROSS_IMP_POINTS']),
                        float(traveler['EW_CROSS_IMP_POINTS']),
                        "https://www.bridgebase.com/tools/handviewer.html?lin=" + traveler['LIN_DATA']
            ]
            
            if board_number not in results.keys():
                results[board_number] = [traveler]
            else:
                results[board_number].append(traveler)


for board_number, travelers in results.items():
    html = html_start
    html += """<p>
    <table id="table_id">
    <caption>Board {}</caption>
    <tr><th>NS</th><th>EW</th><th>CONTRACT</th><th>LEAD</th><th>NS SCORE</th><th>EW SCORE</th><th>NS IMP</th><th>EW IMP</th><th>MOVIE</th></tr>
    """.format(board_number)
    
    for traveler in travelers:

        html += "<tr>"
        html += "<td>{}</td>".format(traveler[1]) # NS
        html += "<td>{}</td>".format(traveler[2]) # EW
        html += "<td>{}</td>".format(traveler[3]) # Contract
        html += "<td>{}</td>".format(traveler[4]) # Lead
        html += "<td>{}</td>".format(traveler[5]) # NS Score
        html += "<td>{}</td>".format(traveler[6]) # EW Score
        html += "<td>{}</td>".format(round(traveler[7], 2)) # NS IMP
        html += "<td>{}</td>".format(round(traveler[8], 2)) # EW IMP
        html += '<td><a href ="{}" target="_blank">Movie</a></td>'.format(traveler[9]) # Movie
        html += """</tr>
        """   
    html += "</table></p>"
    html += board_script
    html += html_end
    f = open('board_{}.html'.format(strip_chars(board_number)), 'w', encoding="utf-8")
    f.writelines(html)
    f.close()

for index, pair in pairs.items():
    html = html_start
    html += """<p>
    <table id="table_id">
    <caption>{}</caption>
    <tr><th>#</th><th>VS</th><th>CONTRACT</th><th>LEAD</th><th>SCORE</th><th>IMP</th><th>MOVIE</th><th>TRAVELLER</th></tr>
    """.format(pair)
    
    running_total = 0
    count = 0
    for result in [result for travelers in results.values() for result in travelers if result[1] == pair or result[2] == pair]:
        is_ns = True if result[1] == pair else False
        opps = result[2] if is_ns else result[1]
        
        html += "<tr>"
        html += "<td>{}</td>".format(result[0]) # board number
        html += "<td>{}</td>".format(result[2] if is_ns else result[1]) # opponents
        html += "<td>{}</td>".format(result[3]) # contract
        html += "<td>{}</td>".format(result[4]) # lead
        html += "<td>{}</td>".format(result[5] if is_ns else result[6]) # score
        html += "<td>{}</td>".format(result[7] if is_ns else result[8]) # IMP
        html += '<td><a href ="{}" target="_blank">Movie</a></td>'.format(result[-1]) # movie
        html += '<td><a href ="board_{}.html">Traveller</a></td>'.format(result[0], index) # traveller
        html += """</tr>
        """
        
        running_total += result[7] if is_ns else result[8]
        count += 1
        
    html += '<td colspan="5">Average</td>'
    html += '<td>{}</td>'.format(round(float(running_total / count), 2))
    html += '<td colspan="2"></td>'
    html += "</table></p>"
    html += html_end
    f = open('{}.html'.format(strip_chars(pair).replace(" ", "_")), 'w', encoding="utf-8")
    f.writelines(html)
    f.close()
    
    
html = html_start
html += """<p>
<table id="table_id">
<caption>SUMMARY</caption>
<tr><th>#</th><th>PAIR</th><th>RANK</th><th>RESULTS</th></tr>
"""

for index, pair in pairs.items():
    html += "<tr>"
    html += "<td>{}</td>".format(index) # pair number
    html += "<td>{}</td>".format(pair) # pair number
    html += "<td>{}</td>".format(rankings[index]) # ranking
    html += '<td><a href ="{}.html">BOARDS</a></td>'.format(strip_chars(pair).replace(" ", "_")) # BOARDS
    html += """</tr>
    """

html += "</table></p>"
html += html_end

f = open('index.html', 'w')
f.writelines(html)
f.close()

