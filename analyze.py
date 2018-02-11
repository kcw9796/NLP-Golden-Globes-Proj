import json
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
import time


# Motion Picture Awards
mAwards = ['Best Motion Picture - Drama','Best Motion Picture - Musical or Comedy','Best Director','Best Actor - Motion Picture Drama','Best Actor - Motion Picture Musical or Comedy',
'Best Actress - Motion Picture Drama','Best Actress - Motion Picture Musical or Comedy','Best Supporting Actor - Motion Picture','Best Supporting Actress - Motion Picture',
'Best Screenplay','Best Original Score','Best Foreign Language Film','Best Animated Feature Film','Cecil B. DeMille Lifetime Achievement Award']

# Television Awards
tAwards = ['Best Drama Series','Best Comedy Series','Best Actor in a Television Drama Series','Best Actor in a Television Comedy Series','Best Actress in a Television Drama Series',
'Best Actress in a Television Comedy Series','Best Limited Series or Motion Picture made for Television','Best Actor in a Limited Series or Motion Picture made for Television',
'Best Actress in a Limited Series or Motion Picture made for Television','Best Supporting Actor in a Series made for Television',
'Best Supporting Actress in a Series made for Television']

abbreviations = {'television':'tv'}

# List of Award objects that hold information about each award
Award_list = []

# set of keywords relating to the awards
Award_words = set()

class Award:

	def __init__(self,name,presenter,nominees,winner,winner_votes,filtered_sentence):
		self.name = name
		self.presenter = presenter
		self.nominees = nominees
		self.winner = winner
		self.winner_votes = winner_votes
		self.filtered_sentence = filtered_sentence

	def print_award(self):
		print('Award: {}'.format(self.name))
		print('Presented By: {}'.format(self.presenter))
		print('Nominees: {}'.format(', '.join(self.nominees)))
		print('Winner votes: {}'.format(self.winner_votes))
		print('Winner: {}\n'.format(self.winner))


# Initialize awards function that loops through the list of TV and Movie awards and creates Award objects with those names and adds it to Award_list 
# The Function then loops through the award name and creates a list called filtered_sentence which only keeps key words in the award name
def init_awards():

	# Create award objects and add to Award_list
	for mAward in mAwards:
		award_obj = Award(mAward,'',[],'',{},[])
		Award_list.append(award_obj)
	for tAward in tAwards:
		award_obj = Award(tAward,'',[],'',{},[])
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


# Opens json file with ~800,000 tweets and returns a list of the tweets
def analyze_tweets(filename):

	# stop_words = ['Best','Golden','Globes','Actor','Actress']
	with open(filename) as data_file:
		tweets = json.load(data_file)

		# for i in range(700000,710000):
		# 	analyze(tweets[i]['text'])


		for tweet in tweets:
			analyze(tweet['text'])


# Analyze algorithm that first finds which award it matches if any
def analyze(tweet):

	tweet_lowercase = tweet.lower()

	# Looking for the winner so filters tweets by 'win' or 'congratulations'
	if('win' in tweet_lowercase or 'congratulations' in tweet_lowercase):

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

		if(award_guess != None):
			words = word_tokenize(tweet)
			filtered_sentence = []
			for word in words:
				if word == 'https':
					break
				filtered_sentence.append(word)
			filtered_sentence_pos = pos_tag(filtered_sentence)
			chunked = nltk.ne_chunk(filtered_sentence_pos)
			
			winner = ""
			check = True
			for chunk in chunked.subtrees(filter=lambda t: t.label()=='PERSON'):
				for item in chunk.subtrees():
					for word in item.leaves():
						if(word[0].lower() in Award_words):
							check = False
							break
						winner += word[0] + ' '
				break
			winner = winner.strip()
			print('First Guess: {}'.format(winner))


			if(check == False or winner == ''):
				winner = ''
				i = None
				print(filtered_sentence)
				for index,word in enumerate(filtered_sentence):
					if(word == 'to'):
						i = index + 1
						break
				if(i != None):
					check = True
					while(i<len(filtered_sentence) and filtered_sentence[i][0].isupper()):
						if(filtered_sentence[i].lower() in Award_words):
							check = False
							break
						winner += filtered_sentence[i] + ' '
						i += 1
					winner = winner.strip()
					print('First Guess: {}'.format(winner))		

			print(award_guess.name)
			print(winner)
			print(tweet)
			print('\n')


			if(check and winner != ""):
				if(winner in award_guess.winner_votes):
					award_guess.winner_votes[winner] += 1
				else:
					award_guess.winner_votes[winner] = 1


# Loops through award objects and looks at the voting lists for each award and picks the appropriate winner with most votes
# Then prints results for each award
def get_results():

	for award in Award_list:
		new_winner_votes = dict(award.winner_votes)
		for person,val in award.winner_votes.items():
			for person2,val2 in award.winner_votes.items():
				if(person != person2 and (person.replace(' ','').lower() == person2.lower() or person.lower() == person2)):
					new_winner_votes[person] += val2
					del new_winner_votes[person2]
		award.winner_votes = new_winner_votes

	for award in Award_list:
		max_votes = 0
		for person,val in award.winner_votes.items():
			if(val>max_votes):
				award.winner = person
				max_votes = val

		award.print_award()



def main():
	t0 = time.time()
	init_awards()
	analyze_tweets('gg2018.json')
	get_results()
	t1 = time.time()
	print("\nTotal Running Time: {}".format(t1-t0))


if __name__ == "__main__":
	main()
