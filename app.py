import requests
import pandas as pd
import numpy as np
import json
import threading
import unicodedata
import re
from math import ceil


def get_data():
	"""Grabs all the data and loads it into a Pandas dataframe.
	converts all the data to the proper format, and cleans the Company
	Names.  Returns the dataframe."""


	transactions = []

	url = 'http://resttest.bench.co/transactions/%d.json'

	# Check if there is actually data to grab
	r = requests.get(url%1)
	code = r.status_code
	if code != 200:
	    return

	# Convvert request object to json, and find number of transaction
	info = r.json()
	num_transactions = info['totalCount']

	first_transactions = info['transactions']
	transactions.extend(info['transactions'])

	transactions_per_page = len(first_transactions)
	num_pages = int(ceil(num_transactions*1./transactions_per_page))


	threads = []
	for page in xrange(2,num_pages+1,1):
		t = threading.Thread(target = load_data, args = (url%page,transactions))
		t.start()
		threads.append(t)

	for t in threads: t.join()


	output = pd.DataFrame(transactions)

	# Names an empty ledger as 'Payments'
	output['Ledger'] = output.Ledger.apply(lambda x: 'Payments' if x =="" else x)

	# Convert the transaction amounts from strings to floats
	output['Amount'] = output.Amount.apply(lambda x: float(x))

	# Convert the date to a pandas datetime object
	output['Date'] = output.Date.apply(lambda x: pd.to_datetime(x))

	# Use clean_name function to remove garbage
	output['Company'] = output.Company.apply(lambda x: clean_names(x))

	output.drop_duplicates(inplace = True)

	return output.sort('Date')


def load_data(url,lst):
	"""A helper function to download the data through
	multi-threading"""

	r = requests.get(url)
	if r.status_code != 200:
		return

	info = r.json()
	lst.extend(info['transactions'])


def clean_names(name):
	"""Takes a string, and removes the garbage.  Returns cleaned string"""


	PLACES = ['vancouver','calgary','toronto','mississauga', 'bc','on','ab']

	name = name.lower()
	name = unicodedata.normalize('NFKD', name).encode('ascii','ignore')
	name = name.replace(' usd ', " ")
	name_list = [word.capitalize() for word in name.split() if word not in PLACES]
	name = " ".join(name_list)

	name = re.sub(r'[0-9a-z]*xx+[0-9a-z]*', '', name)
	name = name.replace("  "," ")
	name = re.sub(r'[0-9a-z\#]*[0-9]+[0-9a-z\#]*', '', name)
	name = name.replace("  "," ")
	name = name.replace(" X", "")
	name = name.replace(" @", "")
	name = name.replace(".","")

	return name


def get_balance(data):
	return data.Amount.sum()


def expenses_by_cat(data):
 	return data.groupby('Ledger')['Amount'].sum()


def running_balance(data):
	"""Takes in a dataframe with transaction data,
	and returns a new dataframe with daily transaction totals
	and the cumulative total up to that data"""

	out = data.groupby('Date', as_index = True).sum()
	out['Cumulative Balance'] = out['Amount'].cumsum()

	return out

if __name__=="__main__":

	data = get_data()
	balance = get_balance(data)
	expenses_by_cat = expenses_by_cat(data)
	running_balance = running_balance(data)

	run = True
	display = """\n-------------------------
				\n What would you like to do?
				\n 1 - Get balance
				\n 2 - Get expense by category
				\n 3 - Get a running balance
				\n 4 - Print all transactions
				\n 0 - Quit
				\n-------------------------\n"""

	while run:

		user_input = raw_input(display)

		if not user_input:
			user_input = 0
		else:
			user_input = int(user_input)

		run = user_input


		if user_input == 1:
			print "The balance is: ${0:.2f}".format(round(get_balance(data),2))

		elif user_input == 2:
			print expenses_by_cat.to_string()

		elif user_input == 3:
			print running_balance.to_string()

		elif user_input == 4:
			print data.to_string()

		else:
			break








