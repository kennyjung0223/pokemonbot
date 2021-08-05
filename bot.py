'''
issues:
	- 1. improve runtime for rising ranks
	- 2. incorporate embed styling for most messages
'''

import os

import discord
from discord.ext import commands, tasks
from discord.channel import DMChannel

from dotenv import load_dotenv
from parser import refresh_rankings_info, get_all_char_info, get_roster, get_links, get_guild_members, get_rising_level, get_rising_quest, what_drops_from, who_drops, simulate_soul_scroll, job_count_msg, get_help_messages

import random
import textwrap

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BOT_CREATOR = "@gamja#9941"

bot = commands.Bot(help_command=None, command_prefix='!')

@bot.event
async def on_ready():
	print(f'{bot.user.name} has connected to Discord!')
	refresh_rankings.start()

@tasks.loop(minutes=5.0, count=None)
async def refresh_rankings():
	refresh_rankings_info()

@bot.command()
async def help(ctx, command=None):
	help_message = get_help_messages(command)

	await ctx.author.send(textwrap.dedent(help_message))

	if not isinstance(ctx.channel, DMChannel):
		await ctx.channel.send("{}, help information was sent to your direct messages!".format(ctx.author.mention))
	
@bot.command()
async def ping(ctx):
	await ctx.channel.send("pikachu")

@bot.command(aliases=["party", "p"])
async def get_party(ctx, *igns):
	if len(igns) == 0:
		embed = discord.Embed(
			title="Parties",
			url="https://storymaple.com/rankings-overall",
			color=discord.Color.red()
		)

		embed.set_author(
			name='{}#{}'.format(ctx.author.name, ctx.author.discriminator),
			url=ctx.message.jump_url,
			icon_url=ctx.author.avatar_url
		)

		embed.add_field(
			name="No Player Inputs",
			value="Please provide at least 1 player in the party."
		)

		embed.set_thumbnail(url="https://pngimage.net/wp-content/uploads/2018/06/maplestory-mushroom-png-1.png")

		await ctx.channel.send(embed=embed)

	elif len(igns) > 12:
		embed = discord.Embed(
			title="Parties",
			url="https://storymaple.com/rankings-overall",
			color=discord.Color.red()
		)

		embed.set_author(
			name='{}#{}'.format(ctx.author.name, ctx.author.discriminator),
			url=ctx.message.jump_url,
			icon_url=ctx.author.avatar_url
		)

		embed.add_field(
			name="Too Many Player Inputs",
			value="There are more than 12 players listed. Please only provide a maximum of 12 players."
		)

		embed.set_thumbnail(url="https://pngimage.net/wp-content/uploads/2018/06/maplestory-mushroom-png-1.png")

		await ctx.channel.send(embed=embed)

	else:
		roster = get_roster(igns)
		links = [get_links(ign) for ign in igns]

		try:
			embed = discord.Embed(
				title="Parties",
				url="https://storymaple.com/rankings-overall",
				color=discord.Color.blue()
			)

			embed.set_author(
				name='{}#{}'.format(ctx.author.name, ctx.author.discriminator),
				url=ctx.message.jump_url,
				icon_url=ctx.author.avatar_url
			)

			jobs = {}		
			party_1 = ["```\n"]
			party_2 = ["```\n"]

			for i in range(min(len(roster), 6)):
				party_1.append("{:<2} {:<15} Lvl {:<5} {:<13} [{}]\n".format(i + 1, roster[i][1], roster[i][4], roster[i][3], links[i]))
					
				jobs[roster[i][3]] = jobs.get(roster[i][3], 0) + 1

			party_1.append("```")

			embed.add_field(
				name="Party 1:",
				value="".join(party_1),
				inline=False
			)

			if len(roster) > 6:
				for i in range(6, min(len(roster), 12)):
					party_2.append("{:<2} {:<15} Lvl {:<5} {:<13} [{}]\n".format(i + 1, roster[i][1], roster[i][4], roster[i][3], links[i]))

					jobs[roster[i][3]] = jobs.get(roster[i][3], 0) + 1

				party_2.append("```")

				embed.add_field(
					name="Party 2:",
					value="".join(party_2),
					inline=False
				)

			job_msg = job_count_msg(jobs)

			embed.add_field(
				name="**Jobs**",
				value="".join(job_msg)
			)

			await ctx.channel.send(embed=embed)
		except:
			embed = discord.Embed(
				title="Parties",
				url="https://storymaple.com/rankings-overall",
				color=discord.Color.red()
			)

			embed.set_author(
				name='{}#{}'.format(ctx.author.name, ctx.author.discriminator),
				url=ctx.message.jump_url,
				icon_url=ctx.author.avatar_url
			)

			embed.add_field(
				name="Invalid Player Input",
				value="There was an invalid IGN. Please make sure all IGNs are typed correctly."
			)

			embed.set_thumbnail(url="https://pngimage.net/wp-content/uploads/2018/06/maplestory-mushroom-png-1.png")

			await ctx.channel.send(embed=embed)

@bot.command(aliases=["rank", "r"])
async def get_rank(ctx, ign):
	if len(ign) < 4:
		await ctx.channel.send(">>> Invalid IGN. IGNs should have at least 4 characters.")
	else:
		try:
			char_infos = get_all_char_info(ign)
			
			output = ["```{:<15} {:<5} {:<15} {:<15}\n\n".format("Name", "Lvl", "Job", "Guild")]

			for char_info in char_infos:
				if char_info[2]:
					output.append("{:<15} {:<5} {:<15} {:<15}\n".format(char_info[1], char_info[4], char_info[3], char_info[2]))
				else:
					output.append("{:<15} {:<5} {:<15}\n".format(char_info[1], char_info[4], char_info[3]))

			output.append("```")

			embed = discord.Embed(
				title="StoryMaple Rankings",
				url="https://storymaple.com/rankings-overall",
				color=discord.Color.green()
			)

			embed.set_author(
				name='{}#{}'.format(ctx.author.name, ctx.author.discriminator),
				url=ctx.message.jump_url,
				icon_url=ctx.author.avatar_url
			)

			embed.set_thumbnail(url="https://i.imgur.com/6kEeyHg.png")

			embed.add_field(
				name="Characters",
				value="".join(output),
				inline=False
			)

			embed.add_field(
				name="Rank",
				value=str(char_info[0]),
			)

			embed.add_field(
				name="Link Levels",
				value=str(get_links(ign)),
			)

			embed.add_field(
				name="Nirvana",
				value=str(char_info[-1]),
			)

			await ctx.channel.send(embed=embed)
		except:
			embed = discord.Embed(
				title="StoryMaple Rankings",
				url="https://storymaple.com/rankings-overall",
				color=discord.Color.red()
			)

			embed.set_author(
				name='{}#{}'.format(ctx.author.name, ctx.author.discriminator),
				url=ctx.message.jump_url,
				icon_url=ctx.author.avatar_url
			)

			embed.set_thumbnail(url="https://pngimage.net/wp-content/uploads/2018/06/maplestory-mushroom-png-1.png")

			embed.add_field(
				name="Invalid Player Information",
				value="Could not retrieve data for **{}**".format(ign)
			)

			await ctx.channel.send(embed=embed)

@bot.command(aliases=["guild", "g"])
async def get_guild(ctx, guild):
	try:
		guild_members, guild_count = get_guild_members(guild)

		output = ["**{} Guild Members in {}**\n```".format(guild_count, guild.title())]

		for guild_member in guild_members[:-1]:
			output.append(guild_member)
			output.append(" ")

		output.append("{}```".format(guild_members[-1]))

		await ctx.channel.send(''.join(output))
	except:
		await ctx.channel.send("{} is an invalid guild.".format(guild.title()))

@bot.command(aliases=["risinglevel", "rl"])
async def get_rising_level_stars(ctx):
	rl_stars = get_rising_level()

	embed = discord.Embed(
		title="StoryMaple",
		url="https://storymaple.com/rankings",
		color=discord.Color.gold()
	)

	embed.set_author(
		name='{}#{}'.format(ctx.author.name, ctx.author.discriminator),
		url=ctx.message.jump_url,
		icon_url=ctx.author.avatar_url
	)

	rising_stars = ["```\n"]

	for rl_star in rl_stars:
		if rl_star[2]:
			rising_stars.append("{:<2} {:<15} Lvl {:<5} {:<13}\n".format(rl_star[0], rl_star[1], rl_star[4], rl_star[2]))
		else:
			rising_stars.append("{:<2} {:<15} Lvl {:<5}\n".format(rl_star[0], rl_star[1], rl_star[4]))

	rising_stars.append("```")

	embed.add_field(
		name="Rising Stars (Levels)",
		value="".join(rising_stars)
	)

	await ctx.channel.send(embed=embed)

@bot.command(aliases=["risingquest", "rq"])
async def get_rising_quest_stars(ctx):
	rq_stars = get_rising_quest()

	embed = discord.Embed(
		title="StoryMaple",
		url="https://storymaple.com/rankings-rising-quest",
		color=discord.Color.gold()
	)

	embed.set_author(
		name='{}#{}'.format(ctx.author.name, ctx.author.discriminator),
		url=ctx.message.jump_url,
		icon_url=ctx.author.avatar_url
	)

	rising_stars = ["```\n"]

	for rq_star in rq_stars:
		if rq_star[2]:
			rising_stars.append("{:<2} {:<15} Quests {:<5} {:<13}\n".format(rq_star[0], rq_star[1], rq_star[5], rq_star[2]))
		else:
			rising_stars.append("{:<2} {:<15} Quests {:<5}\n".format(rq_star[0], rq_star[1], rq_star[5]))

	rising_stars.append("```")

	embed.add_field(
		name="Rising Stars (Quests)",
		value="".join(rising_stars)
	)

	await ctx.channel.send(embed=embed)

@bot.command(aliases=["whatdropsfrom", "wdf"])
async def get_what_drops_from(ctx, *monster):
	monster = ' '.join(monster)

	monster, drops = what_drops_from(monster)

	if not drops:
		await ctx.channel.send("**{}** does not exist in the game.".format(monster))
	else:
		output = ["**{}** drops these items:```".format(monster)]

		for drop in drops:
			output.append(drop)

		output.append("```")

		await ctx.channel.send('\n'.join(output))

@bot.command(aliases=["whodrops", "wd"])
async def get_who_drops(ctx, *item):
	item = ' '.join(item)

	if item.title() == "Chaos Scroll 60%" or item.title() == "White Scroll":
		await ctx.channel.send("All monsters from levels 1 through 79 and Nintos drop **{}**.".format(item.title()))
	else:
		item, monsters = who_drops(item)

		if not monsters:
			await ctx.channel.send("**{}** does not exist in the game.".format(item))
		else:
			output = ["These monster(s) drop **{}**```".format(item)]

			for monster in monsters:
				output.append(monster)

			output.append("```")

			await ctx.channel.send('\n'.join(output))

@bot.command(aliases=["soulscroll", "ss"])
async def simulate_ss(ctx, *args):
	try:
		amount, stat = int(args[0]), args[1]

		if amount <= 0:
			await ctx.channel.send("The amount of the stat must be greater than 0.")
		else:
			gain, max_gain, avg_gain = simulate_soul_scroll(amount, stat)

			embed = discord.Embed(
				title="Soul Scroll",
				color=discord.Color.blurple()
			)

			embed.set_author(
				name='{}#{}'.format(ctx.author.name, ctx.author.discriminator),
				url=ctx.message.jump_url,
				icon_url=ctx.author.avatar_url
			)

			embed.set_thumbnail(url="https://media.discordapp.net/attachments/851690942716313630/860108903841136660/scrollss.png")

			embed.add_field(
				name="Before",
				value="**{}** {}".format(str(amount), args[1].upper())
			)

			embed.add_field(
				name="After",
				value="**{}** {}".format(str(amount + gain), args[1].upper())
			)

			embed.add_field(
				name="Gain",
				value="**+{}** {}".format(str(gain), args[1].upper()),
				inline=False
			)

			embed.add_field(
				name="Statistics",
				value="Max Gain: **+{}**\nAvg Gain: **+{}**".format(str(max_gain), str(avg_gain))
			)

			await ctx.channel.send(embed=embed)

	except ValueError:
		await ctx.channel.send("Please follow the syntax for this command: ```!soulscroll <amount> <stat>```")

@bot.command(name="bbb")
async def bbb_search(ctx, *args):
	if not args:
		await ctx.channel.send("Please provide an input for what to search.")

	search_array = ["https://bbb.hidden-street.net/search_finder/"]

	if len(args) > 1:
		search_array.append("%20".join(args))
	else:
		search_array.append(args[0])

	await ctx.channel.send("".join(search_array))

@bot.command(name="love")
async def love_at(ctx, *name):
	full_name = ' '.join(name)

	love_messages = [
		"i luv u, {}! :heart:".format(full_name), 
		"{}, will u be my valentine?".format(full_name),
		"hugs and kisses for {}! :hugging: :kissing:".format(full_name)
	]
	rand = random.randint(0, len(love_messages) - 1)

	love_message = love_messages[rand]

	msg = await ctx.channel.send(love_message)

	await msg.add_reaction("🇱")
	await msg.add_reaction("🇴")
	await msg.add_reaction("🇻")
	await msg.add_reaction("🇪")
	await msg.add_reaction("❤️")

@bot.command(name="scold")
async def scold_at(ctx, *name):
	full_name = ' '.join(name)
	scold_messages = [
		":middle_finger: Fuck {}! :middle_finger:".format(full_name),
		"{}, you're a piece of shit! :poop:".format(full_name),
		"{} you son of a bitch! :service_dog:".format(full_name)
	]

	rand = random.randint(0, len(scold_messages) - 1)

	scold_message = scold_messages[rand]

	msg = await ctx.channel.send(scold_message)

	await msg.add_reaction("🇫")
	await msg.add_reaction("🇺")
	await msg.add_reaction("🇨")
	await msg.add_reaction("🇰")
	await msg.add_reaction("🖕")


bot.run(TOKEN)

