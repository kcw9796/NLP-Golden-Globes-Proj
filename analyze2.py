import json
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
import spacy
from spacy import displacy
import re

# Motion Picture Awards
mAwards = ['Best Motion Picture - Drama','Best Motion Picture - Musical or Comedy','Best Director','Best Actor - Motion Picture Drama','Best Actor - Motion Picture Musical or Comedy',
'Best Actress - Motion Picture Drama','Best Actress - Motion Picture Musical or Comedy','Best Supporting Actor - Motion Picture','Best Supporting Actress - Motion Picture',
'Best Screenplay','Best Original Score','Best Foreign Language Film','Best Animated Feature Film','Cecil B. DeMille Award for Lifetime Achievement in Motion Pictures']

# Television Awards
tAwards = ['Best Drama Series','Best Comedy Series','Best Actor in a Television Drama Series','Best Actor in a Television Comedy Series','Best Actress in a Television Drama Series',
'Best Actress in a Television Comedy Series','Best Limited Series or Motion Picture made for Television','Best Actor in a Limited Series or Motion Picture made for Television',
'Best Actress in a Limited Series or Motion Picture made for Television','Best Supporting Actor in a Series, Limited Series or Motion Picture made for Television',
'Best Supporting Actress in a Series, Limited Series or Motion Picture made for Television']

Award_list = []

class Award:

	def __init__(self,name,presenter,nominees,winner,winner_votes,filtered_sentence):
		self.name = name
		self.presenter = presenter
		self.nominees = nominees
		self.winner = winner
		self.winner_votes = winner_votes
		self.filtered_sentence = []

	def print_award(self):
		print('Award: {}'.format(self.name))
		print('Presented By: {}'.format(self.presenter))
		print('Nominees: {}'.format(', '.join(self.nominees)))
		print('Winner: {}\n'.format(self.winner))


def init_awards():
	for mAward in mAwards:
		award_obj = Award(mAward,'',[],'',{},[])
		Award_list.append(award_obj)
	for tAward in tAwards:
		award_obj = Award(tAward,'',[],'',{},[])
		Award_list.append(award_obj)


def readtweets():
	tweets_list = []
	with open('gg2018.json') as data_file:
		tweets = json.load(data_file)
		for i in range(400000,401000):
			tweets_list.append(tweets[i]['text'])
			# print(tweets[i]['text'])
			# print('\n')
		# for tweet in tweets:
		# 	tweets_list.append(tweet['text'])
	return tweets_list


def analyze(tweets):

	stop_words = stopwords.words('english')
	stop_words_custom = ['-']
	nlp = spacy.load('en')


	for award in Award_list:
		filtered_sentence = []
		words = word_tokenize(award.name)
		for word in words:
			if(word not in stop_words and word not in stop_words_custom):
				filtered_sentence.append(word)
		award.filtered_sentence = filtered_sentence

	for tweet in tweets:
		for award in Award_list:
			check = True
			for word in award.filtered_sentence:
				if word not in tweet:
					check = False

			if(check):
				if('win' in tweet or 'Congratulations' in tweet):
					words = word_tokenize(tweet)
					filtered_sentence = []
					for word in words:
						if word == 'https':
							break
						filtered_sentence.append(word)
					filtered_sentence = pos_tag(filtered_sentence)
					chunked = nltk.ne_chunk(filtered_sentence)
					chunked.draw()
					
					winner = ""
					for chunk in chunked.subtrees(filter=lambda t: t.label()=='PERSON'):
						for item in chunk.subtrees():
							for word in item.leaves():
								winner += word[0] + ' '
							break

					print(winner)
					print('{} \n'.format(tweet))

					# if(winner not in award.winner_votes):
					# 	award.winner_votes[winner] = 1
					# else:
					# 	award.winner_votes[winner] += 1


	# for award in Award_list:
	# 	max_votes = 0
	# 	for person,val in award.winner_votes.items():
	# 		if(val>max_votes):
	# 			award.winner = person

	# 	award.print_award()


	# stop_words = stopwords.words('english')
	# stop_words = ['-',':']
	# stop_words = []
	# chunk = r"""Award: {<Category><Subcategory>*}
	# 			Category: {<:>*<JJS><NN.?>+}
	# 			Subcategory: {<:>*<IN><DT><JJ>*<NN.?>+(<CC><DT>*<JJ>*<NN.?>+)*}
	# 			Subsubcategory: {(<:>*<JJ.?><CC><DT>*<JJ>*<NN.?>+)}"""
				

	# chunk_parser = nltk.RegexpParser(chunk)
	# nlp = spacy.load('en')
	# for tweet in tweets:
	# 	if('win' in tweet or 'Congratulations' in tweet):
		# if('Sterling' in tweet):
		# if(award in tweet and subcategory in tweet):
		# if(True):
			# doc = nlp(tweet)


			# for ent in doc.ents:
			# 	print('{}: {}: {}'.format(ent,ent.label,ent.label_))

			# doc_comp = nlp(u"Kirk Willens wins the Golden Globe for Best Actor in a TV series")
			# award_comp1 = nlp(u"Best Actor in a TV series")

			# if(doc.similarity(doc_comp)>0.75):
				# print(doc)
				# print('ENTS:')
				# for ent in doc.ents:
				# 	print('{}: {}'.format(ent.text,ent.label_))
				# print('NOUNS:')
			# for noun in doc.noun_chunks:
			# 	print('{}: {}: {}'.format(noun.text,noun.root.head.text,noun.root.text))
			# print('\n')

			# # if(doc.similarity(doc_comp)>0.75):

			# people = []
			# for ent in doc.ents:
			# 	if(ent.label_ == 'PERSON'):
			# 		people.append(ent.text)
			

			# winner = 'None'
			# award = 'None'
			# category = 'None'
			# subcategory = 'None'
			# for index,noun in enumerate(doc.noun_chunks):
			# 	dep_word = noun.root.head.text
			# 	if('win' in dep_word):
			# 		if(noun.text in people):
			# 			winner = noun.text
			# 		else:
			# 			award = noun.text
			# 	elif('to' in dep_word):
			# 		if(noun.text in people):
			# 			winner = noun.text
			# 	elif('for' in dep_word and award=='None'):
			# 		award = noun.text
			# 	elif('by' in dep_word):
			# 		category = noun.text
			# 		if(award=='None'):
			# 			try:
			# 				award = noun[index-1].text
			# 			except:
			# 				award = 'None'
			# 	elif('in' in noun.root.head.text):
			# 		subcategory = noun.text

			# if(winner == 'None'):
			# 	try:
			# 		winner = people[0]
			# 	except:
			# 		winner = 'None'

			# if(winner != 'None' and award != 'None'):
			# 	award_name = award
			# 	if(category != 'None'):
			# 		award_name += ' by ' + category
			# 	if(subcategory != 'None'):
			# 		award_name += ' in ' + subcategory

			# 	max_sim = 0
			# 	award_guess = ''
			# 	# award_doc = nlp(award_name)
			# 	# for mAward in mAwards:
			# 	# 	sim = award_doc.similarity(nlp(mAward))
			# 	# 	if(sim>max_sim):
			# 	# 		max_sim = sim
			# 	# 		award_guess = mAward
			# 	# for tAward in tAwards:
			# 	# 	sim = award_doc.similarity(nlp(tAward))
			# 	# 	if(sim>max_sim):
			# 	# 		max_sim = sim
			# 	# 		award_guess = tAward
				

			# 	# if(max_sim>0):
			# 	if(1):
			# 		print('PERSON: {}'.format(winner))
			# 		# print('AWARD GUESS: {} '.format(award_guess))
			# 		print('AWARD: {}'.format(award_name))
			# 		# print('SUBCATEGORY: {}'.format(subcategory))
			# 		print(doc)
			# 		print('\n')
			



			# filtered_sentence = []
			# words = word_tokenize(tweet)
			# for word in words:
			# 	if word == 'https':
			# 		break
			# 	if word not in stop_words:
			# 		filtered_sentence.append(word)
			# filtered_sentence = pos_tag(filtered_sentence)
			# chunked = chunk_parser.parse(filtered_sentence)
			# for chunk in chunked:
			# 	print(chunk)
			# chunked.draw()
			# chunked = nltk.ne_chunk(filtered_sentence)
			# for chunk in chunked:
			# 	print(chunk)
			# chunked.draw()
			# print('{}\n'.format(chunked))
			# break;


def main():
	init_awards()
	tweets = readtweets()
	analyze(tweets)


if __name__ == "__main__":
	main()



