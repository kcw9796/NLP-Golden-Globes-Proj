import json
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
import time
from difflib import SequenceMatcher
from collections import Counter


# Motion Picture Awards
mAwards = ['Best Motion Picture - Drama','Best Motion Picture - Musical or Comedy','Best Director','Best Actor - Motion Picture Drama','Best Actor - Motion Picture Musical or Comedy',
'Best Actress - Motion Picture Drama','Best Actress - Motion Picture Musical or Comedy','Best Supporting Actor - Motion Picture','Best Supporting Actress - Motion Picture',
'Best Screenplay','Best Original Score','Best Foreign Language Film','Best Animated Feature Film','Cecil B. DeMille Lifetime Achievement Award']

# Television Awards
tAwards = ['Best Drama Series','Best Comedy Series','Best Actor in a Television Drama Series','Best Actor in a Television Comedy Series','Best Actress in a Television Drama Series',
'Best Actress in a Television Comedy Series','Best Limited Series or Motion Picture made for Television','Best Actor in a Limited Series made for Television',
'Best Actress in a Limited Series made for Television','Best Supporting Actor in a Limited Series made for Television',
'Best Supporting Actress in a Limited Series made for Television']

abbreviations = {'television':'tv'}

# Dictionary of keywords and what category they correspond to
keywords_dict = {' win':1,'congratulation':1,' present':2,' announc':2,' introduc':2,'best speech':3,'best dress':4,'best look':4,'worst dress':5,'worst look':5}
# keywords_dict = {'best speech':3,'best dress':4,'best look':4,'worst dress':5,'worst look':5}


# Dictionary of categories and the title they refer to
category_dict = {1:'Winner',2:'Presenters',3:'Best Speech',4:'Best Dressed',5:'Worst Dressed'}

# List of Award objects that hold information about each award
Award_list = []

# set of keywords relating to the awards
Award_words = set()

# A list of voting dictionaries for info that does not relate to a an award (Example: Best Dressed)
Bonus_Info = {3:{},4:{},5:{}}

class Award:

	def __init__(self,name,presenter,nominees,winner,voting_dict,filtered_sentence):
		self.name = name
		self.presenter = presenter
		self.nominees = nominees
		self.winner = winner
		self.voting_dict = voting_dict
		self.filtered_sentence = filtered_sentence

	def print_award(self):
		print('Award: {}'.format(self.name))
		print('Presented By: {}'.format(self.presenter))
		print('Nominees: {}'.format(', '.join(self.nominees)))
		# print('Winner votes: {}'.format(self.voting_dict[1]))
		print('Presenter votes: {}'.format(self.voting_dict[2]))
		# print('Nominee votes: {}'.format(self.voting_dict[3]))
		print('Winner: {}\n'.format(self.winner))


# Initialize awards function that loops through the list of TV and Movie awards and creates Award objects with those names and adds it to Award_list 
# The Function then loops through the award name and creates a list called filtered_sentence which only keeps key words in the award name
def init_awards():

	# Create award objects and add to Award_list
	for mAward in mAwards:
		award_obj = Award(mAward,'',[],'',{1:{},2:{}},[])
		Award_list.append(award_obj)
	for tAward in tAwards:
		award_obj = Award(tAward,'',[],'',{1:{},2:{}},[])
		Award_list.append(award_obj)

	# Make a filtered_sentence of key words for each object using stop_words
	stop_words = stopwords.words('english')
	stop_words_custom = ['-','made']
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


# Main function for analyzing the tweets
# Opens json file with ~800,000 tweets and calls helper functions to filter results
def analyze_tweets(filename):

	with open(filename) as data_file:
		tweets = json.load(data_file)

		for tweet in tweets:
			full_tweet = tweet['text']
			tweet_lowercase = full_tweet.lower()
			keyword,category = find_tweet_category(tweet_lowercase)
			# Only execute if the tweet relates to a category
			if (category > 0):
				award_guess = None
				if(category < 3):			
					award_guess = find_tweet_award(tweet_lowercase)
				else:
					for word in category_dict[category].split(' '):
						Award_words.add(word.lower())
				# Only execute if the tweet relates to an award
				if(category > 2 or award_guess != None):
					tweet = full_tweet
					if(category > 0):
						tweet = full_tweet.split(keyword)[0]
					entity_list = find_named_entities(tweet, category)
					if(entity_list != []):
						print('Tweet Category Guess: {}'.format(category))
						print('Final Entity Guess: {}'.format(entity_list))
						if(award_guess == None and category > 2):
							submit_vote_bonus_info(category,entity_list)
						else:
							submit_vote(category,award_guess,entity_list)
							print('Tweet Award Guess: {}'.format(award_guess.name))
							
						print('Tweet: {}'.format(full_tweet))
						print('\n')
						


def find_tweet_category(tweet_lowercase):
	# Looking for the winner so filters tweets by 'win' or 'congratulations'
	for key,val in keywords_dict.items():
		if(key in tweet_lowercase):
			return key,val
	return None,0

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
			if word_lowercase not in tweet_lowercase and (word_lowercase not in abbreviations or abbreviations[word_lowercase] not in tweet_lowercase):
				check = False
			else:
				count += 1
		if(count>max_count and check):
			award_guess = award
			max_count = count
	return award_guess



# Analyze algorithm that finds named entities in the tweets text
def find_named_entities(tweet, category):

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
	entity = ''
	for chunk in chunked.subtrees(filter=lambda t: t.label()=='PERSON'):
		entity = ''
		for item in chunk.subtrees():
			for word in item.leaves():
				# If the algorithm is confused and things the award is a persons name then forget it
				if(word[0].lower() in Award_words): 
					entity = ''
					break
				entity += word[0] + ' '
		if(entity != ''):
			entity_list.append(entity.strip())
			if(category==1):
				break

	# If the Named Entity Recognition from NLTK doesn't work then find next best possible name
	# Assuming an award is given 'to' someone, then concatenate all captialized words after 'to' if in the tweet
	# If not, then move on to another tweet and ignore this one
	if(category == 1 and entity_list == []):
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
				if(filtered_sentence[i].lower() in Award_words):
					check = False
					break
				entity += filtered_sentence[i] + ' '
				i += 1
			entity = entity.strip()
			if(check == True and entity != ''):
				entity_list.append(entity)

	return entity_list

	

# If we found a potential winner, then add 1 to the awards winner dictionary with the person's name as the key
# If that person's name is not in the dictionary yet then initialize it with a count of 1
def submit_vote(category,award,entity_list):	
	for entity in entity_list:
		if(entity in award.voting_dict[category]):
			award.voting_dict[category][entity] += 1
		else:
			award.voting_dict[category][entity] = 1


# For categories that do not relate to awards, submit votes to the bonus info dictionary
def submit_vote_bonus_info(category,entity_list):
	for entity in entity_list:
		if(entity in Bonus_Info[category]):
			Bonus_Info[category][entity] += 1
		else:
			Bonus_Info[category][entity] = 1

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

		award.print_award()

	print("Bonus Information:\n")

	for category,bonus_dict in Bonus_Info.items():
		Bonus_Info[category] = resolve_voting_dict(bonus_dict)

	for category,bonus_dict in Bonus_Info.items():
		if(bonus_dict != {}):
			[(entity,max_votes)] = dict(Counter(bonus_dict).most_common(1)).items()

		print('{}: {}'.format(category_dict[category],entity))


def main():
	t0 = time.time()
	init_awards()
	analyze_tweets('gg2018.json')
	get_results()
	t1 = time.time()
	print("\nTotal Running Time: {}".format(t1-t0))


if __name__ == "__main__":
	main()



