#==================================================================================================================================
# prepare.py - Copyright Vess 2023
# Scrape, parse, and prepare a workable dataset to use for machine learning from the Pathfinder 2e Dashboard website.
#==================================================================================================================================
# Known Bugs, Issues, and Limitations
# 1. Read and write from files multiple times for an easily resumable / debuggable process.
# 2. Expects that the target website doesn't change formatting... Which it certainly might.
#==================================================================================================================================

# Imports.
import csv
import pprint
import os
import re
import requests
import sys
import warnings

#==================================================================================================================================

# Take a string and add a few decorations to it before printing it to the terminal.
# Pre: Takes a string, and a bool for ellipses.
# Post: Returns none.
def debug_out(input_string, input_elip=False):
	# One trigger for adding ellipses since it reads nicer.
	if not input_elip:
		print("Debug: " + input_string + ".")
	elif input_elip:
		print("Debug: " + input_string + "...")
	return

#==================================================================================================================================

# Scrape a domain of a given name and output into a text file of a given name.
# Pre: Takes a domain name, and a file name.
# Post: Returns none.
def setup_scrape(input_domain, input_file):
	# We turn off SSL verification because the website let their SSL cert lapse.
	handle_web = requests.get(input_domain, verify=False)
	handle_file = open(input_file, "w")
	handle_file.write(handle_web.content.decode("UTF-8"))
	handle_file.close()
	return

#==================================================================================================================================

# Parse out web links from a text file into another file of a given name.
# Pre: Takes a input file name, and an output file name.
# Post: Returns none.
def setup_parse(input_scrape, input_parse):
	# Load in our scraped HTML code.
	handle_scrape = open(input_scrape, "r")
	data_html = handle_scrape.read()
	handle_scrape.close()
	# Target a specific link regex.
	data_mask = "Creatures\/.*.html"
	data_match = re.findall(data_mask, data_html)
	data_match.sort()
	# Write the link matches to the file.
	data_pretty = pprint.pformat(data_match)
	handle_parse = open(input_parse, "w")
	handle_parse.write(data_pretty)
	handle_parse.close()
	return

#==================================================================================================================================

# Remove a certain set of links that hit a match and output.
# Pre: Takes a input file name, and an output file name.
# Post: Returns none.
def setup_clean(input_link, output_clean, output_exclude):
	# Load in our unfiltered links.
	handle_link = open(input_link, "r")
	data_match = eval(handle_link.read())
	handle_link.close()
	# Define the outliers we wish to remove.
	data_remove = ["AV", " BB", "Class", "Elite", "Improvised", "Generic", "Level", "Petitioner", "PFS", "Spellcaster", "Soulbound Doll", "("]
	# Also remove statblocks that are level variations.
	for temp_num in range(10):
		data_remove.append(str(temp_num))
	# Remove the outliers from our matches.
	data_clean = []
	data_exclude = []
	for temp_match in data_match:
		check_remove = all(temp_check not in temp_match for temp_check in data_remove)
		if check_remove:
			data_clean.append(temp_match)
		elif not check_remove:
			data_exclude.append(temp_match)
	# Dedup and sort the clean and excluded links.
	data_clean = list(set(data_clean))
	data_clean.sort()
	data_exclude = list(set(data_exclude))
	data_exclude.sort()
	# Prettify the clean links and write to the output file.
	pretty_clean = pprint.pformat(data_clean)
	handle_clean = open(output_clean, "w")
	handle_clean.write(pretty_clean)
	handle_clean.close()
	# Prettify the excluded links and write to the output file.
	pretty_exclude = pprint.pformat(data_exclude)
	handle_exclude = open(output_exclude, "w")
	handle_exclude.write(pretty_exclude)
	handle_exclude.close()
	return

#==================================================================================================================================

# Inhale and scrape all of the links found in an input file, then write out.
# Pre: Takes an input base website, output directory, and an input web target.
# Post: Returns none.
def setup_crawl(input_prepend, input_dir, input_parse):
	# Load in our list of links.
	handle_parse = open(input_parse, "r")
	data_parse = eval(handle_parse.read())
	handle_parse.close()
	# Begin the crawling and scraping! Sorry Ashley! This only happens once.
	for temp_link in data_parse:
		# Build the output file path.
		name_out = input_dir + temp_link
		name_out = name_out.replace("Creatures/", "")
		# Check for its existance.
		check_path = os.path.exists(name_out)
		if not check_path:
			# Build the URL to scrape.
			name_full = input_prepend + temp_link
			handle_web = requests.get(name_full, verify=False)
			# Scrape it to the out file!
			handle_out = open(name_out, "w")
			handle_out.write(handle_web.content.decode("UTF-8"))
			handle_out.close()
			debug_out("Scraped to this file: " + name_out, True)
		elif check_path:
			debug_out("SKIPPED scraping this file: " + name_out, True)
	return

#==================================================================================================================================

# Inhale files found in the input directory, then copy the ones we want to the output directory.
# Pre: Takes an input directory, an output directory, and a file for keeping track of filtered files.
# Post: Returns none.
def setup_filter(input_dir, input_out, input_filter):
	# Grab a list of files in the rough directory.
	list_file = os.listdir(input_dir)
	list_remove = []
	# Iterate through them...
	for temp_link in list_file:
		# Grab their data...
		link_full = input_dir + temp_link
		handle_link = open(link_full, "r")
		data_link = handle_link.read()
		handle_link.close()
		# Then filter them out based on hits in that data.
		link_remove = [temp_bind + "</div>" for temp_bind in ["environmental", "hazard", "trap"]]
		link_remove.append("404")
		check_remove = all(temp_check not in data_link for temp_check in link_remove)
		if check_remove:
			# And then basically copy them back out to the filtered directory.
			link_new = input_out + temp_link
			handle_copy = open(link_new, "w")
			handle_copy.write(data_link)
			handle_copy.close()
		elif not check_remove:
			# Keep track of the files we've filtered out.
			list_remove.append(link_full)
	# Write the list of filtered files out.
	list_remove.sort()
	pretty_filter = pprint.pformat(list_remove)
	handle_filter = open(input_filter, "w")
	handle_filter.write(pretty_filter)
	handle_filter.close()
	return

#==================================================================================================================================

# Takes in a statblock of creature HTML data, finds what we want out of it, and returns that.
# Pre: Takes a chunk of input HTML data.
# Post: Returns a list of relevant data.
def pull_data(input_data):
	# A quick hack fix for malformed data.
	input_data = input_data.replace("+-", "-")
	# Data format: name, level, size, law, moral, ac, hp, perception, fort, ref, will, str, dex, con, int, wis, cha, skills
	search_capture = [
		["name'>", "<"], # Name.
		["lvNum'>", "<"], # Level.
		["AC</b> <span class='dc'>", "<"], # AC of the creature.
		["hp'>", "<"], # HP of the creature.
		["Perception</b> <span class='bns'>", "<"], # Perception bonus.
		["Fort</b> <span class='bns'>", "<"], # Fortitude bonus.
		["Ref</b> <span class='bns'>", "<"], # Reflex bonus.
		["Will</b> <span class='bns'>", "<"], # Willpower bonus.
		["Str</b> ", ","], # Strength bonus.
		["Dex</b> ", ","], # Dexterity bonus.
		["Con</b> ", ","], # Constitution bonus.
		["Int</b> ", ","], # Intelligence bonus.
		["Wis</b> ", ","], # Wisdom bonus.
		["Cha</b> ", " \n"], # Charisma bonus.
	]
	# Not all monsters have bonuses to all skills so we separate it out.
	search_skill = [
		["Acrobatics <span class='bns'>", "<"], # Acrobatics bonus.
		["Arcana <span class='bns'>", "<"], # Arcana bonus.
		["Athletics <span class='bns'>", "<"], # Athletics bonus.
		["Crafting <span class='bns'>", "<"], # Crafting bonus.
		["Deception <span class='bns'>", "<"], # Deception bonus.
		["Diplomacy <span class='bns'>", "<"], # Diplomacy bonus.
		["Intimidation <span class='bns'>", "<"], # Intimidation bonus.
		["Medicine <span class='bns'>", "<"], # Medicine bonus.
		["Nature <span class='bns'>", "<"], # Nature bonus.
		["Occultism <span class='bns'>", "<"], # Occultism bonus.
		["Performance <span class='bns'>", "<"], # Performance bonus.
		["Religion <span class='bns'>", "<"], # Religion bonus.
		["Society <span class='bns'>", "<"], # Society bonus.
		["Stealth <span class='bns'>", "<"], # Stealth bonus.
		["Survival <span class='bns'>", "<"], # Survival bonus.
		["Thievery <span class='bns'>", "<"], # Thievery bonus.
	]
	# Finding size and alignment are done on straightforward subset tests.
	search_size = [ # Sizes, make it ordinal.
		[">tiny<", 1], # 1 = Tiny.
		[">Small<", 2], # 2 = Small.
		[">Medium<", 3], # 3 = Medium.
		[">Large<", 4], # 4 = Large.
		[">huge<", 5], # 5 = Huge.
		[">Gargantuan<", 6], # 6 = Gargantuan.
	]
	search_align = [ # Alignments, make it ordinal.
		["> CE <", 1, 1], # 1 Chaotic, 2 Netural, 3 Lawful, 1 Evil, 2 Neutral, 3 Good.
		["> NE <", 2, 1], 
		["> LE <", 3, 1], 
		["> CN <", 1, 2],
		["> N <", 2, 2],
		["> LN <", 3, 2],
		["> CG <", 1, 3],
		["> NG <", 2, 3],
		["> LG <", 3, 3],
	]
	data_statblock = []
	# Capture the main capture group of stats.
	for temp_capture in search_capture:
		capture_search = temp_capture[0] + "(.*?)" + temp_capture[1]
		capture_chunk = re.search(capture_search, input_data).group(1)
		# I'm lazy.
		if temp_capture[0] != "name'>":
			data_statblock.append(int(capture_chunk))
		else:
			data_statblock.append(capture_chunk)
	# Capture the skill capture group.
	for temp_skill in search_skill:
		if temp_skill[0] in input_data:
			capture_search = temp_skill[0] + "(.*?)" + temp_skill[1]
			capture_chunk = re.search(capture_search, input_data).group(1)
			data_statblock.append(int(capture_chunk))
		else:
			data_statblock.append(0)
	# Finally, capture and insert the size and alignment.
	for temp_size in search_size:
		if temp_size[0] in input_data:
			data_statblock.insert(2, temp_size[1])
			break
	for temp_align in search_align:
		if temp_align[0] in input_data:
			data_statblock.insert(3, temp_align[1])
			data_statblock.insert(4, temp_align[2])
			break
	return data_statblock

#==================================================================================================================================

# Inhale files found in the input directory, then copy the data we want to the output file.
# Pre: Takes an input directory, and a file to output the parsed data to.
# Post: Returns none.
def setup_search(input_dir, input_csv):
	# The header for the CSV file.
	data_header = ["name", "level", "size", "law", "moral", "ac", "hp", "perception", "fortitude", "reflex", "willpower", "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma", "acrobatics", "arcana", "athletics", "crafting", "deception", "diplomacy", "intimidation", "medicine", "nature", "occultism", "performance", "religion", "society", "stealth", "survival", "thievery"]
	# Create the CSV file.
	handle_csv = open(input_csv, "w")
	handle_writer = csv.writer(handle_csv)
	handle_writer.writerow(data_header)
	# Grab a list of files in the filtered directory.
	list_file = os.listdir(input_dir)
	# Iterate through and pull the statblock out of each file.
	for temp_file in list_file:
		handle_file = open(input_dir + temp_file)
		data_file = handle_file.read()
		handle_file.close()
		data_statblock = pull_data(data_file)
		handle_writer.writerow(data_statblock)
	handle_csv.close()
	return

#==================================================================================================================================

if __name__ == "__main__":
	# Suppress the warnings whining about SSL certifs.
	warnings.filterwarnings("ignore")
	# 0. The default variables to use and pass around.
	name_web = "http://pathfinderdashboard.com/"
	name_scrape = "./website-scrape.html" # To hold our scraped HTML code.
	name_parse = "./website-link.txt" # To hold all of the links found in said HTML.
	name_clean = "./website-clean.txt" # To hold all of the preferred links found in said HTML.
	name_exclude = "./website-exclude.txt" # To hold all of the excluded links found in said HTML.
	name_rough = "./statblock-rough/" # To hold the scraped Pathfinder 2e statblocks.
	name_filter = "./statblock-filter/" # To hold the final Pathfinder 2e statblocks.
	name_other = "./statblock-exclude.txt" # To hold the filtered statblock names.
	name_csv = "./statblock-data.csv" # To hold the statblock data in CSV format.
	debug_out("Starting to prepare the data", True)
	# 1. Scrape the website to an output file.
	if not os.path.exists(name_scrape):
		debug_out("Scraping the website: " + name_web, True)
		setup_scrape(name_web, name_scrape)
		debug_out("Website scraped to file: " + name_scrape)
	# 2. Find the creature URLs in the scraped website.
	if not os.path.exists(name_parse):
		debug_out("Parsing for URLs from: " + name_scrape, True)
		setup_parse(name_scrape, name_parse)
		debug_out("URLs parsed to file: " + name_parse)
	# 3. Filter out certain name_clean ULRs we don't want.
	if not os.path.exists(name_clean):
		debug_out("Loading links from: " + name_parse, True)
		setup_clean(name_parse, name_clean, name_exclude)
		debug_out("Wrote clean links to: " + name_clean)
		debug_out("Wrote excluded links to: " + name_exclude)
	# 4. Setup for our statblock scraping, then do it.
	if not os.path.exists(name_rough):
		os.mkdir(name_rough)
		debug_out("Created directory for rough statblocks")
		debug_out("Loading links from: " + name_clean, True)
		setup_crawl(name_web, name_rough, name_clean)
		debug_out("Finished crawling links from: " + name_clean)
	# 5. Filter out certain statblocks based on keywords.
	if not os.path.exists(name_filter):
		os.mkdir(name_filter)
		debug_out("Created directory for filtered statblocks")
		setup_filter(name_rough, name_filter, name_other)
		debug_out("Filtered statblocks to: " + name_filter)
	# 6. Pull out the relevant data we want from the statblocks.
	if not os.path.exists(name_csv):
		debug_out("Starting to parse the data out", True)
		setup_search(name_filter, name_csv)
		debug_out("Output the parsed data to: " + name_csv)
	debug_out("Finished preparing the data")
	sys.exit()

#==================================================================================================================================