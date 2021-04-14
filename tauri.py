#main bot
import os
import re
import git
import sys
import json
import aiohttp
import asyncio
import hashlib
import importlib
from twitchio.ext import commands
from urllib.parse import urlparse, parse_qs
import mysql.connector

ootr_repo_path = os.path.join(os.path.join(os.getcwd(), "ootr"))
if not ootr_repo_path in sys.path:
	sys.path.append(ootr_repo_path)
from ootr.Main import main
from ootr.Settings import Settings


rom_path = "N:\Games\OoT Randomizer\Legend of Zelda, The - Ocarina of Time (USA)1.0.n64"
start_dir = os.getcwd()
all_presets = {}

AUTH_BASE = "https://id.twitch.tv/oauth2/authorize?response_type=code"
VALID_BASE = "https://id.twitch.tv/oauth2/validate"



default_settings = {
	"create_spoiler": True,
	"world_count": 1,
	"randomize_settings": False,
	"logic_rules": "glitchless",
	"open_forest": "closed",
	"open_kakariko": "open",
	"open_door_of_time": True,
	"zora_fountain": "closed",
	"gerudo_fortress": "fast",
	"bridge": "medallions",
	"bridge_medallions": 6,
	"triforce_hunt": False,
	"trials_random": False,
	"trials": 0,
	"starting_age": "child",
	"shuffle_interior_entrances": "off",
	"shuffle_grotto_entrances": False,
	"shuffle_dungeon_entrances": False,
	"shuffle_overworld_entrances": False,
	"owl_drops": False,
	"warp_songs": False,
	"spawn_positions": False,
	"bombchus_in_logic": False,
	"one_item_per_dungeon": False,
	"mq_dungeons_random": False,
	"mq_dungeons": 0,
	"shuffle_song_items": "song",
	"shopsanity": "off",
	"tokensanity": "off",
	"shuffle_scrubs": "off",
	"shuffle_cows": False,
	"shuffle_kokiri_sword": False,
	"shuffle_ocarinas": False,
	"shuffle_weird_egg": False,
	"shuffle_gerudo_card": False,
	"shuffle_beans": False,
	"shuffle_medigoron_carpet_salesman": False,
	"shuffle_mapcompass": "startwith",
	"shuffle_smallkeys": "dungeon",
	"shuffle_bosskeys": "dungeon",
	"shuffle_ganon_bosskey": "remove",
	"enhance_map_compass": False,
	"all_reachable": True,
	"logic_no_night_tokens_without_suns_song": True,
	"disabled_locations": [
		"Deku Theater Mask of Truth",
		"Kak 40 Gold Skulltula Reward",
		"Kak 50 Gold Skulltula Reward",
		"GF HBA 1500 Points"
	],
	"allowed_tricks": [],
	"skip_child_zelda": True,
	"no_escape_sequence": True,
	"no_guard_stealth": True,
	"no_epona_race": True,
	"skip_some_minigame_phases": True,
	"useful_cutscenes": False,
	"complete_mask_quest": False,
	"fast_chests": True,
	"free_scarecrow": True,
	"fast_bunny_hood": True,
	"starting_equipment": [],
	"starting_items": [],
	"starting_songs": [],
	"start_with_rupees": True,
	"start_with_consumables": True,
	"starting_hearts": 3,
	"chicken_count_random": False,
	"chicken_count": 1,
	"big_poe_count_random": False,
	"big_poe_count": 1,
	"ocarina_songs": False,
	"correct_chest_sizes": False,
	"clearer_hints": True,
	"hints": "always",
	"hint_dist": "very_strong",
	"text_shuffle": "none",
	"damage_multiplier": "normal",
	"starting_tod": "default",
	"item_pool_value": "balanced",
	"ice_trap_appearance": "junk_only",
	"junk_ice_traps": "normal",
	"logic_earliest_adult_trade": "prescription",
	"logic_latest_adult_trade": "claim_check"
}

additional_settings_string = {
	"blitz": 
		{
			"string":"AJTEGYASKJA9EFSDEAAJACBBLMDDAKAAJAEAC2AJSDGBLADLED7JKQUXEAU3BAJAAWBCLAC",
			"fork": "https://github.com/mracsys/OoT-Randomizer.git",
			"fork_user": "mracsys",
			"branch":"goal-hints",
			"hint_dist":"blitz-goal-plando.json"
		},
	"multi":
		{
			"base" : "S4 Tournament",
			"extra": {"world_count":1}
		}
}


class Bot(commands.Bot):
		
	def __init__(self):
		super().__init__(
		irc_token=os.environ['TMI_TOKEN'],
		client_id=os.environ['CLIENT_ID'],
		client_secret=os.environ['CLIENT_SECRET'],
		nick=os.environ['BOT_NICK'],
		prefix=os.environ['BOT_PREFIX'],
		initial_channels=os.environ['CHANNELS'].split(","),
		scopes=["channel:read:redemptions"],
		webhook_server=False,
		local_host="localhost",
		port=8012,
		external_host="wss://pubsub-edge.twitch.tv"
		)
	async def update(self):
		while True:
			print("Updating...")
			needed_channels = await get_channels_to_attach(self)
			current_channels = self.bot_channels
			
			current_channel_names = []
			for channel_info in current_channels:
				current_channel_names.append(channel_info["name"])
			
			for channel_info in needed_channels:
				if channel_info["name"] not in current_channel_names:
					print("Joining Channel (new) : {}".format(channel_info["name"]))
					await self._ws.join_channels(channel_info["name"].lower())
					
					twitch_channel_info = await self.get_users(channel_info["name"].lower())
					twitch_channel_id = twitch_channel_info[0].id
					channel_info['twitch_id'] = twitch_channel_id			
					self.bot_channels.append(channel_info)
					print("channel info print {}".format(channel_info))
					print("PUBSUB SUB : {} -- {}".format(channel_info['twitch_id'], channel_info["token"]))
					await self.pubsub_subscribe(channel_info["token"], "channel-points-channel-v1.{}".format(channel_info['twitch_id']))
			await asyncio.sleep(120)
			
		
	
	async def event_ready(self):
		print(f"{os.environ['BOT_NICK']} is online!")
		print(self.initial_channels)
		self.bot_channels = []
		await self.update()
		##self.bot_channels = await get_channels_to_attach(self)
		##print(self.bot_channels)
		##new_bot_channels = []
		##for channel_info in self.bot_channels:
			##print("Joining Channel : {}".format(channel_info["name"]))
			##await self._ws.join_channels(channel_info["name"].lower())
			
			# twitch_channel = self._ws._channel_cache.get(channel_info["name"].lower())
			##twitch_channel_info = await self.get_users(channel_info["name"].lower())
			##twitch_channel_id = twitch_channel_info[0].id
			##channel_info['twitch_id'] = twitch_channel_id			
			##new_bot_channels.append(channel_info)
			##print("channel info print {}".format(channel_info))
			# if channel_twitch_id == None:
				# print("Joining Channel (from SQL): {}".format(channel_info["name"].lower()))
				# await self._ws.join_channels(channel)
				# auth_channel_twitch_id = self._ws._channel_cache.get(auth_channel_name.lower())
			##print("PUBSUB SUB : {} -- {}".format(channel_info['twitch_id'], channel_info["token"]))
			##await self.pubsub_subscribe(channel_info["token"], "channel-points-channel-v1.{}".format(channel_info['twitch_id']))
		##self.bot_channels = new_bot_channels
			#ws = self._ws
			#await ws.send_privmsg(auth_channel_name, "/me has landed")
			
			
		# await self._ws.join_channels(self.initial_channels[0])
		
		# print(self.get_channel(re.sub('[#\s]', '', self.initial_channels[0]).lower()))
		# print(self.get_users)
		# user = await bot.get_users(re.sub('[#\s]', '', self.initial_channels[0]).lower())
		# curr_channel = self._ws._channel_cache.get(re.sub('[#\s]', '', self.initial_channels[0]).lower())
		# print(curr_channel)
		# print(f"User ID : {user[0].id}")
		# await curr_channel['channel'].get_custom_rewards(os.environ['TMI_TOKEN'], user[0].id)
		# async with self.http._session.get("{}&client_id={}&redirect_uri={}&scope=channel:read:redemptions".format(AUTH_BASE, self.client_id, os.environ['REDIRECT_URI']), allow_redirects=False) as response:
			# print(response.url, response.real_url, 'location' in str(response).lower(), str(response))
		# auth_token_resp = await self.http._session.get("{}&client_id={}&redirect_uri={}&scope=channel:read:redemptions".format(AUTH_BASE, self.client_id, os.environ['REDIRECT_URI']))
		# auth_token_url = auth_token_resp.url
		# print("auth token URL {}".format(auth_token_url))
		# auth_token_query = auth_token_url.query_string
		# auth_token_params = parse_qs(auth_token_query)
		# print(auth_token_params)
		# await self.pubsub_subscribe(os.environ['TMI_TOKEN'], re.sub('[#\s]', '', self.initial_channels[0]).lower())
		### await self.pubsub_subscribe(os.environ['ENHANCED_PERMISSION_TOKEN'], f"channel-points-channel-v1.{user[0].id}")
		# ws = bot._ws
		# await ws.send_privmsg(self.initial_channels[0], f"/me has landed")
	async def event_message(self, message):
		#bot ignores itself
		if message.author.name.lower() == self.nick.lower():
			return
		print(f"Message from {message.author.name} on {message.channel.name} at {message.timestamp} : {message.content} -- {message.raw_data}")
		await bot.handle_commands(message)
	async def event_raw_pubsub(self, data):
		reward_name = ""
		redemption_channel = ""
		redemption_channel_name = ""
		if data['type'] == 'MESSAGE':
			print(data['data'])
			message_data = data['data']
			topic = message_data['topic'].split('.')
			topic_type = topic[0]
			channel = topic[1]
			message = json.loads(message_data['message'])
			if topic_type == 'channel-points-channel-v1':
				print("Message : {}".format(type(message)))
				print("Message Data : {}".format(message['data']))
				print("Message Redemption: {}".format(message['data']['redemption']))
				print("Message Reward: {}".format(message['data']['redemption']['reward']))
				print("Message Reward Title: {}".format(message['data']['redemption']['reward']['title']))
				reward_name = message['data']['redemption']['reward']['title']
				redemption_channel = message['data']['redemption']['reward']['channel_id']
				
		
		#find channel name
			redemption_channel_name = redemption_channel
			print(self.bot_channels)
			for channel_info in self.bot_channels:
				if channel_info['twitch_id'] == redemption_channel:
					redemption_channel_name = channel_info['name']
		
		# if (reward_name == 'Roll me a Seed' or reward_name == 'F') and redemption_channel_name != "":
		if (re.match(r"roll.*seed",reward_name,re.IGNORECASE) != None) and redemption_channel_name != "":
			channel_dir = "C:\\xampp\\htdocs\\generated\\{}".format(redemption_channel_name)
			ws = bot._ws
			spoiler = gen_seed("S4 Tournament",output_dir=channel_dir)
			settings_string_hash = hashlib.sha1(spoiler.settings.settings_string.encode('utf-8')).hexdigest().upper()[:5]
			await ws.send_privmsg(redemption_channel_name, "/me generated seed : {2} -- https://tauribot.zapto.org/generated/{0}/OoT_{1}_{2}.zpf".format(redemption_channel_name, settings_string_hash, spoiler.settings.seed))
			# ws = bot._ws
			# await ws.send_privmsg(self.initial_channels[0], "reward detected : {}".format(reward_name))
	@commands.command(name='tauri')
	async def tauri(self, ctx, *args):
		# ws = 
		channel_name = ctx.channel.name
		print(args)
		
		if len(args) < 1:
			await ctx.send("Available sub-commands: add")
		
		if args[0] == "add" and len(args) > 1:
			print("adding command")
			print(ctx.author.tags)
			print(ctx.author.is_mod)
			await ctx.send("Add command {} from {}".format(args[1], ctx.author.name))
			# @commands.command(name=arg[1])
			# async def arg[1](self, ctx):
				# print("this is a new command named {}".format())
		else:
			await ctx.send("Available sub-commands: add")
		
		await ctx.send("1, 2, 3")
		
	@commands.command(name='coms')
	async def coms(self, ctx):
		print(ctx.command.params)
		
	@commands.command(name='seed')
	async def seed(self, ctx, *args):
		multi = False
		world_count=1
		if ctx.author.is_mod:
			if len(args) > 0:
				settings_string=args[0]
				if args[0] == "multi" and len(args) > 1:
					try:
						world_count = int(args[1])
						multi = True
						if world_count > 5 :
							world_count = 5
					except:
						world_count = 1
					additional_settings_string["multi"]["extra"]["world_count"] = world_count
					if len(args) > 2:
						if len(args[2]) == 71:
							additional_settings_string["multi"]["string"] = args[2]
							print("Multi string : {}".format(additional_settings_string["multi"]["string"]))
			else:
				settings_string ="S4 Tournament"
			
			if len(settings_string) != 71 and settings_string not in additional_settings_string:
				print("DEFAULTING")
				settings_string = "S4 Tournament"
			
			channel_name = ctx.channel.name
			channel_dir = "C:\\xampp\\htdocs\\generated\\{}".format(channel_name)
			spoiler = gen_seed(settings_string, output_dir=channel_dir)
			settings_string_hash = hashlib.sha1(spoiler.settings.settings_string.encode('utf-8')).hexdigest().upper()[:5]
			await ctx.send("/me generated seed : {2} -- https://tauribot.zapto.org/generated/{0}/OoT_{1}_{2}{4}.zpf{3}".format(channel_name, settings_string_hash, spoiler.settings.seed, ("z" if multi else ""), ("_W{}".format(world_count) if multi else "")))
			# ws = bot._ws
			# print(channel_name)
			# await ws.send_privmsg(ctx.channel.name, "/me generated seed : {2} -- https://tauribot.zapto.org/generated/{0}/OoT_{1}_{2}.zpf".format(channel_name, settings_string_hash, spoiler.settings.seed))
			# await ws.send_privmsg(ctx.channel.name, "https://tauribot.zapto.org/generated/{}/OoT_{}_{}.zpf".format(ctx.channel.name, settings_string_hash, spoiler.settings.seed))


def check_sql_table_exist(db, tbl):
	db_cur = db.cursor()
	db_cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{0}'".format(tbl.replace('\'','\'\'')))
	if db_cur.fetchone()[0] == 1:
		db_cur.close()
		return True
	db_cur.close()
	return False

async def get_channels_to_attach(bot):
	channels_to_join = []
	initial_channel_names = initial_channels=os.environ['CHANNELS'].split(",")
	#database set up via web page to track user access tokens (needed for pubsubs)
	
	twitch_db = mysql.connector.connect(
		host="localhost",
		user="root",
		password="",
		database="twitch"
	)
	auth_channels_cursor = twitch_db.cursor()
	auth_channels_cursor.execute("SELECT * FROM authorized_channels")
	auth_channels_result = auth_channels_cursor.fetchall()
	for auth_channel in auth_channels_result:
		auth_channel_id = auth_channel[0]
		auth_channel_name = auth_channel[1]
		auth_channel_token = auth_channel[2]
		# auth_channel_twitch_id = self._ws._channel_cache.get(auth_channel_name.lower())
		
		# if auth_channel_twitch_id == None:
			# print("Joining Channel (from SQL): {}".format(auth_channel_name.lower()))
			# await self._ws.join_channels(channel)
			# auth_channel_twitch_id = self._ws._channel_cache.get(auth_channel_name.lower())
			
		
		if auth_channel_name == '' and auth_channel_token != '':
			print(auth_channel_token)
			validate_session = aiohttp.ClientSession(loop=bot.loop)
			validate_headers = {'Authorization' : 'OAuth {}'.format(auth_channel_token)}
			async with validate_session.get(VALID_BASE, headers=validate_headers) as resp:
				if 300 < resp.status or resp.status < 200:
					raise HTTPException("Unable to generate a token: " + resp.text())
				data = await resp.json()
				print("VALIDATE DATA : {}".format(data))
				print(data['login'])
			await validate_session.close()
			auth_channel_name = data['login']
			update_string = "UPDATE `authorized_channels` SET user ='{}' WHERE `authorized_channels`.`id`={}".format(auth_channel_name,auth_channel_id)
			auth_channels_cursor.execute(update_string)
			twitch_db.commit()
			
		channels_to_join.append({
			"name" : auth_channel_name,
			"id" : auth_channel_id,
			"token" : auth_channel_token})
		if not check_sql_table_exist(twitch_db,auth_channel_name):
			auth_channels_cursor.execute("CREATE TABLE {} (seed VARCHAR(255), path VARCHAR(255))".format(auth_channel_name))
			twitch_db.commit()
			
		print('Internal Channel ID: {}\nChannel Name: {}\nTwitch Token: {}'.format(auth_channel_id, auth_channel_name, auth_channel_token))
	auth_channels_cursor.close()
	twitch_db.close()
	return channels_to_join

def gen_seed(setting_str, presets=all_presets, output_dir='generation_output'):

	ootr_repo = git.Repo(ootr_repo_path)
	ootr_repo.heads["release"].checkout()
	settings = Settings(default_settings)
	importlib.reload(sys.modules['ootr'])
	if setting_str in presets:
		print("is a preset")
		if "rom" not in presets[setting_str]:
			presets[setting_str]["rom"] = rom_path
		if "output_dir" not in presets[setting_str]:
			if not (os.path.isdir(output_dir)):
				os.mkdir(output_dir)
			presets[setting_str]["output_dir"] = output_dir
		else:
			print(presets[setting_str]["output_dir"])
		if "compress_rom" not in presets[setting_str]:
			presets[setting_str]["compress_rom"] = "Patch"
		settings = Settings(presets[setting_str])
	else:
		print("not a preset : {}".format(setting_str))
		if len(setting_str) == 71:
			settings.update_with_settings_string(setting_str)
		elif setting_str in additional_settings_string:
			if "fork" in additional_settings_string[setting_str]:
				#check if git branch exists		
				settings.update_with_settings_string(additional_settings_string[setting_str]["string"])
				settings_branch = "{}_{}".format(additional_settings_string[setting_str]["fork_user"], additional_settings_string[setting_str]["branch"])
				print("checking for {}".format(settings_branch))
				if settings_branch in ootr_repo.branches:
					#checkout the desired branch
					print("branch exists")
				else:
					#git remote add <fork_user> <fork>
					ootr_repo.create_remote(additional_settings_string[setting_str]["fork_user"], additional_settings_string[setting_str]["fork"])
					#git fetch <fork_user>
					new_remote = ootr_repo.remote(name=additional_settings_string[setting_str]["fork_user"])
					new_remote.fetch()
					ootr_repo.create_head(settings_branch, new_remote.refs[additional_settings_string[setting_str]["branch"]])
					ootr_repo.heads[settings_branch].set_tracking_branch(new_remote.refs[additional_settings_string[setting_str]["branch"]])
					print(new_remote.refs)
					#git checkout -b <settings_branch> <fork_user>/<branch>
				ootr_repo.heads[settings_branch].checkout()
				ootr_repo.remotes[additional_settings_string[setting_str]["fork_user"]].pull()
				importlib.reload(sys.modules['ootr'])
			else:
				settings = Settings(presets[additional_settings_string[setting_str]["base"]])
				if "string" in additional_settings_string[setting_str] and len(additional_settings_string[setting_str]["string"]) == 71:
					print("Updating with {}".format(additional_settings_string[setting_str]["string"]))
					settings.update_with_settings_string(additional_settings_string[setting_str]["string"])
				for extra_setting in additional_settings_string[setting_str]["extra"]:
					settings.__dict__[extra_setting] = additional_settings_string[setting_str]["extra"][extra_setting]
			
			if "hint_dist" in additional_settings_string[setting_str]:
				print("custom hint distribution")
				dist_file = open(os.path.join(os.path.join(os.getcwd(), "ootr", additional_settings_string[setting_str]["hint_dist"])), "r")
				settings.__dict__["hint_dist_user"] = json.load(dist_file)["settings"]["hint_dist_user"]
		settings.__dict__["rom"] = rom_path
		settings.__dict__["output_dir"] = output_dir
		settings.__dict__["compress_rom"] = "Patch"
	print(settings.__dict__["hint_dist"])
	print(settings.__dict__["hint_dist_user"])
	print(settings.get_settings_display())
	gen_spoiler = main(settings)
	
	os.chdir(start_dir)
	return gen_spoiler


# @bot.event
# async def event_ready():
	# 'Called once when the bot goes online.'
	# print(f"{os.environ['BOT_NICK']} is online!")
	# ws = bot._ws
	# await ws.send_privmsg(os.environ['CHANNEL'], f"/me has landed!")
	
# @bot.event
# async def event_message(ctx):
	# 'Runs every time a message is sent in chat.'
	
	## make sure the bot ignore itself + streamer
	# if ctx.author.name.lower() == os.environ['BOT_NICK'].lower():
		# return
	# print(f"Message from {ctx.author.name} on {ctx.channel.name} at {ctx.timestamp} : {ctx.content} -- {ctx.raw_data}")
	# await ctx.channel.send(ctx.content.upper())


if __name__ == "__main__":

	#check if OoT Randomizer directory exits
	#if not, grab from github	
	ootr_repo_path = os.path.join(os.path.join(os.getcwd(), "ootr"))
	if (os.path.isdir(ootr_repo_path)):
		print("ootr exists")
		ootr_repo = git.Repo(ootr_repo_path)
		assert not ootr_repo.bare
	else:
		print("ootr not exists")
		ootr_repo = git.Repo.clone_from("https://github.com/TestRunnerSRL/OoT-Randomizer.git", ootr_repo_path)
		ootr = ootr_repo.git
		ootr.checkout("release")
		print(ootr.status)
	
	#check if there is an __init__.py file in the project (no by default when cloning)
	if (os.path.isfile(os.path.join(ootr_repo_path, "__init__.py"))):
		print("ootr init exists")
	else:
		print("ootr init not exists")
		o_ini = open(os.path.join(ootr_repo_path, "__init__.py"), "w")
		o_ini.close()
	#need to add OOTR repo path to sys.path in order for its imports to work correctly

	
	#load presets from default presets (updated with git)
	default_presets_path = os.path.join(ootr_repo_path,"data","presets_default.json")
	last_settings_path = os.path.join(ootr_repo_path,"settings.sav")
	custom_presets_path = os.path.join(ootr_repo_path,"presets.sav")
	if (os.path.isfile(default_presets_path)):	
		preset_file = open(default_presets_path, "r")
		default_presets = json.load(preset_file)
		all_presets.update(default_presets)
	if (os.path.isfile(last_settings_path)):
		last_settings_file = open(last_settings_path, 'r')
		last_settings = json.load(last_settings_file)
		all_presets["Last"] = last_settings
	if (os.path.isfile(custom_presets_path)):
		custom_presets_file = open(custom_presets_path, 'r')
		custom_presets_settings = json.load(custom_presets_file)
		all_presets.update(custom_presets_settings)
	
	for preset, settings in all_presets.items():
		print(preset)
		
	# gen_seed("S4 Tournament",all_presets)
	bot = Bot()
	bot.run()