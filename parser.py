import requests
import json
import math
import random
import pytz
import heapq
import numpy as np

from datetime import datetime
from fuzzywuzzy import fuzz

characters = []
char_library = {}
guild_library = {}

URL_WDF = "https://storymaple.com/raw-drops"
request_WDF = requests.get(URL_WDF).json()
raw_drops = request_WDF["data"]

monsters = {}
items = {}

for monster, item in raw_drops:
	if monster in monsters:
		monsters[monster].append(item)
	else:
		monsters[monster] = [item]
	if item in items:
		items[item].append(monster)
	else:
		items[item] = [monster]

def refresh_rankings_info():
	print("refreshing rankings...")
	global characters
	global char_library
	global guild_library

	URL = "https://storymaple.com/rankings/player"
	request = requests.get(URL).json()

	# characters: [rank #, ign, guild, job, level, nirvana]
	characters = request["data"]
	char_library = {}
	guild_library = {}

	for character in characters:
		rank_number = character[0]

		if rank_number in char_library:
			char_library[rank_number].append(character)
		else:
			char_library[rank_number] = [character]

		if character[2]:
			guild = character[2]
			if guild in guild_library:
				guild_library[guild].append(character[1])
			else:
				guild_library[guild] = [character[1]]

	print("finished refreshing rankings")

'''
PRIVATE
params: string - the in-game name of the character
returns: int - the rank number of the character which acts as a unique ID
'''
def __get_rank(ign):
	for character in characters:
		if character[1].lower() == ign.lower():
			return character[0]

	return -1

'''
PUBLIC
params: string - the in-game name of the character
returns: array of an array - information about all the characters of a specific user
'''
def get_all_char_info(ign):
	rank = __get_rank(ign)

	if rank == -1:
		return []

	return char_library[rank]

'''
PRIVATE
params: ign - a string which represents the in game name of the character
returns: character - an array of information about a single character
'''
def __get_single_char_info(ign):
	for character in characters:
		if character[1].lower() == ign.lower():
			return character

	return []

def get_links(ign):
	link_levels = 0
	characters = get_all_char_info(ign)

	for character in characters:
		link_levels += character[4]

	return link_levels

'''
PUBLIC
params: igns - an array of strings containing in game names of characters
returns: roster - an array of array of strings containing information about those characters
'''
def get_roster(igns):
	roster = []
	for ign in igns:
		if ign[0] == '[' and not ign[-1] == ']':
			return []
		elif ign[0] == '[' and ign[-1] == ']':
			roster.append([ign])
		else:
			character_info = __get_single_char_info(ign)
			roster.append(character_info)

	return roster

'''
PUBLIC
params: guild - a string that represents the guild
returns: guild_info - a tuple which contains the true name, an array of the guild members,
					  and the count for guild members
'''
def get_guild_members(guild):
	for guild_name, guild_members in guild_library.items():
		if guild_name.lower() == guild.lower():
			return (guild_name, guild_members, len(guild_members))

	return (None, None, 0)

'''
PUBLIC
returns: RL_stars - an array of information for the rising stars for levels
'''
def get_rising_level():
	URL_RL = "https://storymaple.com/rankings/rising-level"
	request_RL = requests.get(URL_RL).json()
	RL_stars = request_RL["data"]

	return RL_stars

'''
PUBLIC
returns: RQ_stars - an array of information for the rising stars for quests
'''
def get_rising_quest():
	URL_RQ = "https://storymaple.com/rankings/rising-quest"
	request_RQ = requests.get(URL_RQ).json()
	RQ_stars = request_RQ["data"]

	return RQ_stars

'''
PUBLIC
params: monster - a string which represents a monster in the game
returns: monsters[monster] - an array of items which the monster drops
'''
def what_drops_from(monster):
	for key, value in monsters.items():
		if monster.title() == key.title():
			return (key, value)

	return (monster, [])

'''
PRIVATE
params: input_item - a string which represents the item to search for
		items - an array of strings where each string represents all items in the game
returns: match - a string that best matches the string similarity ratio
'''
def __get_similar_string(input_item, items):
	matches = []

	for item in items:
		token_ratio = fuzz.token_set_ratio(input_item, item)

		if token_ratio == 100:
			similarity_ratio = fuzz.ratio(input_item, item)
			heapq.heappush(matches, (item, similarity_ratio))

	match = heapq.nlargest(1, matches, key=lambda x: x[1])[0][0] if matches else input_item

	return match

'''
PUBLIC
params: item - a string which represents an item in the game
returns: items[item] - an array of monsters who drop the item
'''
def who_drops(item):
	if item not in items.keys():
		item = __get_similar_string(item, items.keys())

	for key, value in items.items():
		if item.title() == key.title():
			return (key, value)

	return (item, [])

'''
PRIVATE
params: max_gain - max gain of the soul scroll
		pool_count - pool_count which I don't really know what it does
returns: probabilities - an array of the probability to get each roll from +1 to +max gain
'''
def __get_probabilities(max_gain, pool_count):
	probabilities = []

	probabilities.append((7 - (1/8)) / (pool_count - 2))

	for i in range(2, max_gain):
		probabilities.append(((4 * i) + 2) / (pool_count - 2))

	probabilities.append(1 - (2 * math.pow(max_gain, 2) - 9/8) / (pool_count - 2))

	return probabilities

'''
PUBLIC
params: amount - an int which represents that amount of the stat
		stat - a string which represents whether the stat is wa/ma or not
returns: (gain, max_gain, expected_gain, equal_or_better) - a tuple of the gain, max possible gain, expected gain, and cumulative probability for better or equal stats
'''
def simulate_soul_scroll(amount, stat):
	modifier = 16 if stat == "wa" or stat == "ma" else 4

	limit = 1 + (amount / modifier)
	pool_count = (limit * (limit + 1) / 2) + limit
	
	if pool_count <= 71/8:
		return (1, 1, 1, 100)
	
	gain = max(1, math.floor(math.sqrt(8 * np.random.uniform(1, pool_count - 1) + 1)/4))
	max_gain = math.ceil(math.sqrt(8 * pool_count - 7)/4 - 1)
	expected_gain = max_gain + (7/8 + 19/24 * max_gain - math.pow(max_gain, 2) - 2/3 * math.pow(max_gain, 3)) / (pool_count - 2)

	probabilities = __get_probabilities(max_gain, pool_count)

	return (gain, max_gain, round(expected_gain, 2), round(sum(probabilities[gain - 1:]) * 100, 2))

'''
PUBLIC
params: stat - a string which contains either a number of characters
returns: bool - True if stat is a string, otherwise False
'''
def is_number(stat):
	try:
		stat = int(stat)
		return True
	except ValueError:
		return False

'''
PUBLIC
params: jobs - a dictionary where the key is a job and the value is the count
		output - an array which stores strings used for the output
'''
def job_count_msg(jobs):
	unique_chars = len(jobs)
	total_chars = sum(jobs.values())
	job_count_msg = []

	for job, count in sorted(jobs.items(), key=lambda j: j[1], reverse=True):
		job_count_msg.append("{}: **{}**\n".format(job, count))

	job_count_msg.append("\nUnique jobs: **{}**\n".format(unique_chars))
	job_count_msg.append("Total characters: **{}**".format(total_chars))

	return job_count_msg

def get_server_time():
	CST = pytz.timezone('US/Central')
	server_time = datetime.now(CST)

	hour = server_time.strftime("%H")
	minute = server_time.strftime("%M")
	second = server_time.strftime("%S")
	weekday = server_time.strftime("%A")
	month = server_time.strftime("%B")
	day = server_time.strftime("%d")
	year = server_time.strftime("%Y")

	return "Current server time:\n**{}:{}:{}**\n{}, {} {}, {}".format(hour, minute, second, weekday, month, day, year)

def get_help_messages(command):
	BOT_CREATOR = "@gamja#9941"

	if not command:
		return """
		Hello! I am PikachuBot. Use the following syntax to use some of my commands: `!<command> <arguments>`. For example, `!p char david francis`, `!r string`, `!guild pokemon`.
		
		__**Commands**__
		**party** or **p:** Constructs a party or expedition up to 12 players
		**rank** or **r:** Gets the ranking information of a character and all their alternatives
		**guild** or **g:** Gets who is in the inputted guild and how many members are in it
		**risinglevel** or **rl:** Shows the current rising stars (levels)
		**risingquest** or **rq:** Shows the current rising stars (quests)
		**whatdropsfrom** or **wdf:** Provides which items are dropped by the specific monster
		**whodrops** or **wd:** Provides which monster(s) drop the specific item
		**soulscroll** or **ss:** Simulates using a soul scroll with the given amount and stat
		**mention** or **m:** Mentions all the mentioned users in a replied post
		**bbb:** Fetches a link to the bbb.hidden-street.net database with your searched results
		**love:** Writes a love message to the inputted name
		**scold:** Writes a scold message to the inputted name
		**time:** Outputs the current server time
		**help:** Sends a direct message (this message)

		For more information on each command, enter this command: `!help <command>`

		If you have further questions, please message {}
		""".format(BOT_CREATOR)

	elif command == "party" or command == "p":
		return """
		Information about **party** or **p** command:

		**Syntax:** `!party <igns>` or `!p <igns>`

		**For example:**

			- **1 player:** `!party char`
			- **Multiple players:** `!p char francis david worrier snowiie jakey cara`
			- **Reserved:** `!p char [SE] [DK] [Warrior]`

		**Note:** For reserved, you must include square brackets in between what specific
		class or job you are reserving. Do **NOT** include spaces. For example, use
		`!p [SE]` instead of `!p [Sharp Eyes]`.

		The first 6 players in <igns> will be formed in party 1, and the
		last 6 players in <igns> will be formed in party 2. The party command
		will only take a maximum of 12 players.
		"""

	elif command == "rank" or command == "r":
		return """
		Information about **rank** or **r** command:

		**Syntax:** `!rank <ign>` or `!r <ign>`

		**<ign>** is replaced by a player ign. 

		**For example:** `!rank char` or `!r yuta`

		The command will provide information for the specified character,
		alternative characters, rank number, link levels, and nirvana.
		"""

	elif command == "guild" or command == "g":
		return """
		Information about **guild** or **g** command:

		**Syntax:** `!guild <guild_name>` or `!g <guild_name>`

		**<guild_name>** is replaced by a guild name.

		**For example:** `!guild pokemon` or `!g pokemon`

		The command will provide all the guild members in the specific guild
		and how many members are in it.
		"""

	elif command == "risinglevel" or command == "rl":
		return """
		Information about **risinglevel** or **rl** command:

		**Syntax:** `!risinglevel` or `!rl`

		The command will list all the rising stars (levels) for this week.
		"""

	elif command == "risingquest" or command == "rq":
		return """
		Information about **risingquest** or **rq** command:

		**Syntax:** `!risingquest` or `!rq`

		The command will list all the rising stars (quests) for this week.
		"""

	elif command == "whatdropsfrom" or command == "wdf":
		return """
		Information about **whatdropsfrom** or **wdf** command:

		**Syntax:** `!whatdropsfrom <monster_name>` or `!wdf <monster_name>`

		**<monster_name>** is replaced by the monster's name.

		**For example:** `!whatdropsfrom horntail` or `!wdf orange mushroom`

		The command will list all the items dropped by the specified monster.
		"""

	elif command == "whodrops" or command == "wd":
		return """
		Information about **whodrops** or **wd** command:

		**Syntax:** `!whodrops <item>` or `!wd <item>`

		**<item>** is replaced by the monster's name.

		**For example:** `!whodrops power crystal ore` or `!wd fairfrozen`

		The command will list all the monsters that  drop the specified item.
		"""

	elif command == "soulscroll" or command == "ss":
		return """
		Information about **soulscroll** or **ss** command:

		**Syntax:** `!soulsscroll <amount> <stat>` or `!ss <amount> <stat>`

		**<amount** is replaced by the stat amount of the item to soul scroll.

		**<stat>** is the stat type in particular of the item to soul scroll.

		**For example:** `!soulscroll 100 luk` or `!ss 90 wa`

		The command will display a simulation of using a soul scroll with the respective stats.
		"""

	elif command == "mention" or command == "m":
		return """
		Information about **mention** or **m** command:

		**Syntax:** `!mention` or `!m`

		Note: You must reply to the post with mentioned people.

		The command will mention everyone who was mentioned in the replied post.
		"""

	elif command == "bbb":
		return """
		Information about **bbb** command:

		**Syntax:** `!bbb <search_query>`

		**<search_query>** is what to search for in the bbb.hidden-street.net database.

		**For example:** `!bbb horntail` or `!bbb elemental wand`

		The command will return a link to the searched results in the bbb.hidden-street.net database.
		"""

	elif command == "love":
		return """
		Information about **love** command:

		**Syntax:** `!love <name>`

		**<name>** is replaced by the person's name to love.

		**For example:** `!love gamja`

		The command will randomly generate a love message for the specified person.
		"""

	elif command == "scold":
		return """
		Information about **scold** command:

		**Syntax:** `!scold <name>`

		**<name>** is replaced by the person's name to scold.

		**For example:** `!scold gamja`

		The command will randomly generate a scold message for the specified person.
		"""

	elif command == "time":
		return """
		Information about **time** command:

		**Syntax:** `!time`

		The command will output the current server time (Central Standard Time).
		"""

	elif command == "help":
		return """
		Information about **help** command:

		**Syntax:** `!help` or `!help <command>`

		**<command>** is replaced by a command listed in `!help`

		**For example:** `!help party` or `!help rl`

		The command without any arguments will provide information about all the commands
		supported by this bot. The command with an argument will provide specific information
		for the specified argument.
		"""

	return """
	`{}` is not a command supported by PikachuBot.

	Here is a list of commands that are supported:

	- **party** or **p**
	- **rank** or **r**
	- **guild** or **g**
	- **risinglevel** or **rl**
	- **risingquest** or **rq**
	- **whatdropsfrom** or **wdf**
	- **whodrops** or **wd**
	- **soulscroll** or **ss**
	- **mention** or **m**
	- **bbb**
	- **love**
	- **scold**
	- **help**
	""".format(command)

if __name__ == "__main__":
	# refresh_rankings_info()

	# characters = get_all_char_info("char")

	# print(characters)

	print(who_drops("scroll for overall armor for luk 10%"))

