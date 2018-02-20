import json
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
import time
from difflib import SequenceMatcher
from collections import Counter
import os.path
import pandas as pd
import numpy as np


stop = stopwords.words('english')
pd.options.display.max_colwidth = 400


# Motion Picture Awards
mAwards = ['Best Motion Picture - Drama','Best Motion Picture - Musical or Comedy','Best Director','Best Actor - Motion Picture Drama','Best Actor - Motion Picture Musical or Comedy',
'Best Actress - Motion Picture Drama','Best Actress - Motion Picture Musical or Comedy','Best Supporting Actor - Motion Picture','Best Supporting Actress - Motion Picture',
'Best Screenplay','Best Original Score','Best Foreign Language Film','Best Animated Feature Film','Cecil B. DeMille Lifetime Achievement Award', 'Best Original Song']

# Television Awards
tAwards = ['Best Drama Series','Best Comedy Series','Best Actor in a Television Drama Series','Best Actor in a Television Comedy Series','Best Actress in a Television Drama Series',
'Best Actress in a Television Comedy Series','Best Limited Series or Motion Picture made for Television','Best Actor in a Limited Series or Motion Picture made for Television',
'Best Actress in a Limited Series or Motion Picture made for Television','Best Supporting Actor in a Limited Series or Motion Picture made for Television',
'Best Supporting Actress in a Limited Series or Motion Picture made for Television']


abbreviations = {'television':'tv','film':'movie','motion':'movie','picture':'movie'}


# Dictionary of keywords and what category they correspond to
keywords_dict = {' not win':3, ' win':1,'congratulation':1,' present':2,' announc':2,'nominee':3,'nominated':3,'nomin':3, 'best speech':4,'best dress':5,'best look':5,'worst dress':6,'worst look':6}


# Dictionary of categories and the title they refer to
category_dict = {1:'Winner',2:'Presenters',3:'Nominees',4:'Best Speech',5:'Best Dressed',6:'Worst Dressed'}


# # Dictionary of keywords and what category they correspond to
keywords_dict = {' not win:':3,' win':1,'congratulation':1,' present':2,' announc':2,' gave; award':2,'giv; award':2,' won from':2,'nominee':3,'nominated':3,'nomin':3, 'best speech':4,'best dress':5,
					'best look':5,'worst dress':6,'worst look':6}

# List of Award objects that hold information about each award
Award_list = []

# set of keywords relating to the awards
Award_words = set()

# A list of voting dictionaries for info that does not relate to a an award (Example: Best Dressed)
Bonus_Info = {4:{},5:{},6:{}}

stop_words = stopwords.words('english')
stop_words_custom = ['-','made']

class Award:

	def __init__(self,name,presenters,nominees,winner,voting_dict,filtered_sentence):
		self.name = name
		self.presenters = presenters
		self.nominees = nominees
		self.winner = winner
		self.voting_dict = voting_dict
		self.filtered_sentence = filtered_sentence

	def print_award(self):
		print('Award: {}'.format(self.name))
		print('Presented By: {}'.format(', '.join(self.presenters)))
		print('Nominees: {}'.format(', '.join(self.nominees)))
		# print('Winner votes: {}'.format(self.voting_dict[1]))
		# print('Presenter votes: {}'.format(self.voting_dict[2]))
		# print('Nominee votes: {}'.format(self.voting_dict[3]))
		print('Winner: {}\n'.format(self.winner))


def keywordFilter(df, keywordList, selectionList=[] ,excludeList = []):
	# KeywordFilter takes in keywordList that the tweet mush have all of them,
	# selectionList that the tweet mush have one of them,
	# and excludeList that the tweer can't have any of them

	df_useful = df.copy()
	for keyword in keywordList:
		df_useful = df_useful.loc[df_useful['text'].str.contains(keyword, case = False)]

	if (len(selectionList) != 0):
		df_useful['helper'] = df_useful['text'].apply(lambda x: np.NaN if (sum([word.lower() in x.lower() for word in selectionList])==0) else 1)
		df_useful = df_useful.dropna()

	for keyword in excludeList:
		df_useful['helper'] = df_useful['text'].apply(lambda x: np.NaN if keyword.lower() in x.lower() else 1)
		df_useful = df_useful.dropna()

	return df_useful

# Initialize awards function that loops through the list of TV and Movie awards and creates Award objects with those names and adds it to Award_list 
# The Function then loops through the award name and creates a list called filtered_sentence which only keeps key words in the award name
def init_awards():

	# Create award objects and add to Award_list
	for mAward in mAwards:
		award_obj = Award(mAward,[],[],'',{1:{},2:{},3:{}},[])
		Award_list.append(award_obj)
	for tAward in tAwards:
		award_obj = Award(tAward,[],[],'',{1:{},2:{},3:{}},[])
		Award_list.append(award_obj)

	# Make a filtered_sentence of key words for each object using stop_words
	for award in Award_list:
		filtered_sentence = []
		words = word_tokenize(award.name)
		for word in words:
			if(word not in stop_words and word not in stop_words_custom):
				filtered_sentence.append(word.strip(','))
				Award_words.add(word.strip(',').lower())
		award.filtered_sentence = filtered_sentence
	Award_words.add('golden')
	Award_words.add('globe')
	for key,val in category_dict.items():
		words = val.split(' ')
		for word in words:
			Award_words.add(word.lower())


# # Main function for analyzing the tweets
# # Opens json file with ~800,000 tweets and calls helper functions to filter results
def analyze_tweets(tweets):
		
	for tweet in tweets:
		full_tweet = str(tweet['text'])
		tweet_lowercase = full_tweet.lower()
		keyword,category = find_tweet_category(tweet_lowercase)
		# Only execute if the tweet relates to a category
		if (category != None): # nominee category is determined at the end 
			award_guess = None
			if(category <= 3): # winner presenter 		
				award_guess = find_tweet_award(tweet_lowercase)
			# Only execute if the tweet relates to an award or its a category unrelated to an award
			if(category > 3 or award_guess != None): # bonus (speech,dress,looking) or related to a award
				tweet_text = full_tweet
				if(category > 3):
					tweet_text = tweet_text.split(keyword)[0]
				skip_nltk = False
				if(category == 3):
					skip_nltk = True
				entity_list = find_named_entities(tweet_text, category, skip_nltk)
				if(entity_list != []):
					print('Tweet Category Guess: {}'.format(category))
					print('Final Entity Guess: {}'.format(entity_list))
					count = tweet['id_str']
					if(category > 3):
						submit_vote_bonus_info(category,entity_list,count)
					else:
						submit_vote(category,award_guess,entity_list,count)
						print('Tweet Award Guess: {}'.format(award_guess.name))
						
					print('Tweet: {}'.format(full_tweet))
					print('\n')
						

def find_tweet_category(tweet_lowercase):
	# Looking for the winner so filters tweets by 'win' or 'congratulations'
	# for key,val in keywords_dict.items():
	# 	if(key in tweet_lowercase):
	# 		return key,val
	# return None,None

	for key,val in keywords_dict.items():
		check = True
		for word in key.split(';'):
			if(word not in tweet_lowercase):
				check = False
		if(check == True):
			return key,val
	return None,None

def find_tweet_award(tweet_lowercase):
	# We made the assumption that each tweet references at most 1 award (could reference 0)
	# This loop goes through each word of the award name after it was filtered for key words
	# and counts the number of words that match in the tweet
	# We only consider awards where all the keywords are in the tweet
	# Since it is possible that multiple award names could have all its keywords in the tweet,
	# we decided to take the longest award name that has all its keywords in the tweet
	# For instance, the tweet could reference the award name 'Best Actress - Motion Picture Drama'
	# However, both that award and the award 'Best Motion Picture - Drama' would be a match
	# So pick the longer one ('Best Actress - Motion Picture Drama') which is the correct one 
	max_count = 0
	award_guess = None
	for award in Award_list:
		count = 0
		check = True
		for word in award.filtered_sentence:
			word_lowercase = word.lower()
			if(word_lowercase == 'best'):
				continue
			if word_lowercase not in tweet_lowercase and (word_lowercase not in abbreviations or abbreviations[word_lowercase] not in tweet_lowercase):
				check = False
			else:
				count += 1
		if(count>max_count and check):
			award_guess = award
			max_count = count
	return award_guess


# # Analyze algorithm that finds named entities in the tweets text
def find_named_entities(tweet, category, skip_nltk = False):

	# Tokenize the words in the tweet and put in list of filtered_sentence
	# Get part of speech tags for each word
	# Find noun chunks for the tweet
	filtered_sentence = word_tokenize(tweet)
	filtered_sentence_pos = pos_tag(filtered_sentence)
	chunked = nltk.ne_chunk(filtered_sentence_pos)
	
	# Named Entity Recognition:
	# Traverse chunk subtrees and search for a noun chunk with the label 'PERSON' and set it equal to winner
	# For our algorithm, we take the first person that shows up in the tweet
	entity_list = []
	if(skip_nltk == False):
		entity = ''
		for chunk in chunked.subtrees(filter=lambda t: t.label()=='PERSON'):
			entity = ''
			try:
				for item in chunk.subtrees():
					for word in item.leaves():
						# If the algorithm is confused and things the award is a persons name then forget it
						for award_word in Award_words:
							if(award_word in word[0].lower()): 
								raise Exception
						entity += word[0] + ' '
			except:
				entity = ''
			else:
				entity_list.append(entity.strip())
				if(category==1):
					break

	# If the Named Entity Recognition from NLTK doesn't work then find next best possible name
	# Assuming an award is given 'to' someone, then concatenate all captialized words after 'to' if in the tweet
	# If not, then move on to another tweet and ignore this one
	# REGEX: <'to' (A-Z)*>
	if(category==1 and entity_list == []):
		entity = ''
		i = None
		for index,word in enumerate(filtered_sentence):
			if(word == 'to'):
				i = index + 1
				break
		if(i != None):
			check = True
			while(i<len(filtered_sentence) and (filtered_sentence[i][0].isupper() or filtered_sentence[i][0] == "'")):
				# If the algorithm is confused and things the award is a persons name then forget it
				for award_word in Award_words:
					if(award_word in filtered_sentence[i].lower()):
						check = False
						break
				entity += filtered_sentence[i] + ' '
				i += 1
			entity = entity.strip()
			if(check == True and entity != ''):
				entity_list.append(entity.replace(" '","'")) # to resolve join issue

	if (category == 2 and entity_list == []):
		entity = ''
		i = None
		for index,word in enumerate(filtered_sentence):
			if (word == '@' and filtered_sentence[index-1] != 'RT' and index != 0):
				i = index + 1 
				break
			if (word == '#'):
				i = index + 1
				break

		if (i != None):
			check = True
			for award_word in Award_words:
				if(award_word in filtered_sentence[i].lower()):
					check = False
					break
			if (check == True):
				entity = filtered_sentence[i]
				entity = entity.strip()
				if (entity != '' and entity.lower() not in stop_words):
					entity_list.append(entity.replace(" '","'")) # to resolve join issue

	# REGEX: <'over'|':'|'are' (A-Z)*>
	if(category == 3):
		entity = ''
		i = 0
		for index in range(0,len(filtered_sentence)):
			word = filtered_sentence[index]
			if(word == ':' or word == 'over' or word == 'are' or word == 'beat'):
				i = index + 1
				break
		if(i != 0):
			check = True
			if (filtered_sentence[i]=='"'):
				i += 1
			while(i<len(filtered_sentence) and (filtered_sentence[i][0].isupper() or filtered_sentence[i][0] == "'" or 
					filtered_sentence[i] == 'of' or filtered_sentence[i][0] == '"')):
				# If the algorithm is confused and things the award is a persons name then forget it
				if(filtered_sentence[i] == '"'):
					i += 1
					continue
				for award_word in Award_words:
					if(award_word in filtered_sentence[i].lower()):
						check = False
						break
				entity += filtered_sentence[i] + ' '
				i += 1
				if(i<len(filtered_sentence) and (filtered_sentence[i] == ',' or filtered_sentence[i].lower() == 'or' or filtered_sentence[i].lower() == 'and')):
					entity_list.append(entity.strip(' ').replace(" '","'")) # to resolve join issue
					entity = ''
					i += 1
			entity = entity.strip()
			if(check == True and entity != '' and entity.lower() not in stop_words):
				entity_list.append(entity.replace(" '","'"))  # to resolve join issue
	return entity_list

	

# If we found a potential winner, then add 1 to the awards winner dictionary with the person's name as the key
# If that person's name is not in the dictionary yet then initialize it with a count of 1
def submit_vote(category,award,entity_list,count):	
	for entity in entity_list:
		if(entity in award.voting_dict[category]):
			award.voting_dict[category][entity] += count
		else:
			award.voting_dict[category][entity] = count


# For categories that do not relate to awards, submit votes to the bonus info dictionary
def submit_vote_bonus_info(category,entity_list,count):
	for entity in entity_list:
		if(entity in Bonus_Info[category]):
			Bonus_Info[category][entity] += count
		else:
			Bonus_Info[category][entity] = count

# Takes in a voting dictionary and attempts to find repeat keys that are just slight variations and merges them
# Sometimes people tweet in all lower case or all upper case, so if a key matches another one in an upper or lower case then add it its value to that one
# and remove it from the dictionary
def resolve_voting_dict(voting_dict):
	new_votes_dict = dict(voting_dict)
	for person,val in voting_dict.items():
		for person2,val2 in voting_dict.items():
			if(person in new_votes_dict and person2 in new_votes_dict and person != person2):
				if(person.lower() == person2 or person.upper() == person2 or 
					(val>=val2 and (person.lower() in person2.lower() or person2.lower() in person.lower() or
						SequenceMatcher(None,person.lower().replace(' ',''),person2.lower().replace(' ','')).ratio()>=0.9))):
					new_votes_dict[person] += val2
					del new_votes_dict[person2]
	return dict(new_votes_dict)

# Loops through award objects and looks at the voting lists for each award and picks the appropriate winner with most votes
# Then prints results for each award
def get_results():
	
	for award in Award_list:
		for category,voting_dict in award.voting_dict.items():
			award.voting_dict[category] = resolve_voting_dict(voting_dict)

	# Finds the person who got the most votes in the winner votes dictionary and sets the award winner to be that person
	for award in Award_list:
		if(award.voting_dict[1]!= {}):
			[(award.winner,max_votes)] = dict(Counter(award.voting_dict[1]).most_common(1)).items()

def print_bonus_info():
	print("Bonus Information:\n")

	for category,bonus_dict in Bonus_Info.items():
		Bonus_Info[category] = resolve_voting_dict(bonus_dict)

	for category,bonus_dict in Bonus_Info.items():
		if(bonus_dict != {}):
			[(entity,max_votes)] = dict(Counter(bonus_dict).most_common(1)).items()
			print('{}: {}'.format(category_dict[category],entity))

def findNominee(dataframe):

	df = keywordFilter(dataframe, [], ['win over','won over','not win', "didn't win", 'lost','beat','beating out',
				'lose to','lost to','lose an award','lost an award','should have won','same category'])

	for award in Award_list:
		winner = award.winner
		if(winner != ''):
			tweetsList = keywordFilter(df,[winner]).to_dict('records')
			award.voting_dict[3][winner] = 100
			for tweet in tweetsList:
				print ('tweets are ', tweet)
				for entity in find_named_entities(tweet['text'], 3, False):
					entity = entity.split('/')[0]
					if entity in award.voting_dict[3]:
						award.voting_dict[3][entity] += tweet['id_str']
					else:
						award.voting_dict[3][entity] = tweet['id_str']
					print('votes for ', entity, ' are ', award.voting_dict[3][entity])
		award.voting_dict[3] = resolve_voting_dict(award.voting_dict[3])
		d = Counter(award.voting_dict[3])
		for k,v in d.most_common(5):
			award.nominees.append(k)


def findPresenter(df):
	for award in Award_list:
		winner = award.winner
		if(winner != ''):
			tweetsList = keywordFilter(df,[winner],[' announc',' present','gave the award','give the award','giving the award','gave an award','give an award','giving an award']).to_dict('records')
			for tweet in tweetsList:
				print (tweet)
				for entity in find_named_entities(tweet['text'].split('award')[0], 2, False):
					entity = entity.split('/')[0]
					if entity in award.voting_dict[2]:
						award.voting_dict[2][entity] += tweet['id_str']
					else:
						award.voting_dict[2][entity] = tweet['id_str']
					print('votes for ', entity, ' are ', award.voting_dict[2][entity])
					print('\n')
		new_votes_dict = dict(award.voting_dict[2])
		for person,count in award.voting_dict[2].items():
			if(person in winner):
				del new_votes_dict[person]
		award.voting_dict[2] = resolve_voting_dict(new_votes_dict)
		d = Counter(award.voting_dict[2])
		for k,v in d.most_common(4):
			award.presenters.append(k)

def findHost(dataframe):

	tweetsList = keywordFilter(dataframe,['host', 'golden', 'globe']).to_dict('records')
	voting_dict = {}
	for tweet in tweetsList:
		for entity in find_named_entities(tweet['text'], 6, False):
			entity = entity.split('/')[0]
			if entity in voting_dict:
				voting_dict[entity] += tweet['id_str']
			else:
				voting_dict[entity] = tweet['id_str']
	voting_dict = resolve_voting_dict(voting_dict)
	host_name = max(voting_dict, key=lambda key: voting_dict[key])
	print("\nThe host of Golden Globe is: {}".format(host_name))


def print_results():
	print("\nPrinting Final Results \n")
	for award in Award_list:
		award.print_award()



def initializeJSONfile(path):
	# Check whether the simplified JSON files exist, if not, generate it
	if not os.path.exists('simplified_data.json'):
		df = pd.DataFrame(columns = ['text', 'id_str'])
		df = pd.read_json(path)
		df = df.groupby('text').count()
		df = df.reset_index()
		data = df.to_dict('records')
		with open('simplified_data.json', 'w') as outfile:  
			json.dump(data, outfile)
		return df,data	
	else:
		df = pd.DataFrame(columns = ['text', 'id_str'])
		df = pd.read_json('simplified_data.json')
		data = df.to_dict('records')
		return df, data



def main():
	t0 = time.time()
	dataframe, data = initializeJSONfile('gg2018.json')
	init_awards()
	analyze_tweets(data)
	get_results()
	findNominee(dataframe)
	findPresenter(dataframe)
	findHost(dataframe)
	print_results()
	print_bonus_info()
	t1 = time.time()
	print("\nTotal Running Time: {}".format(t1-t0))


if __name__ == "__main__":
	main()



