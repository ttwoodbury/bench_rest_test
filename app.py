import requests
import pandas as pd
import numpy as np
import json
import unicodedata
import re


def get_data():
	"""Grabs all the data and loads it into a Pandas dataframe.
	converts all the data to the proper format, and cleans the Company
	Names.  Returns the dataframe."""


	transactions = []

	#Check if there is actually data to grab
	r = requests.get('http://resttest.bench.co/transactions/1.json')
	code = r.status_code
	if code != 200:
	    return

	#Convvert request object to json, and find number of transaction
	info = r.json()
	num_transactions = info['totalCount']

	transactions.extend(info['transactions'])

	page_num = 2
	while len(transactions) < num_transactions:
	    r = requests.get('http://resttest.bench.co/transactions/%d.json'%page_num)
	    info = r.json()
	    transactions.extend(info['transactions'])
	    page_num +=1

	output = pd.DataFrame(transactions)

		#Names an empty ledger as 'Payments'
	output['Ledger'] = output.Ledger.apply(lambda x: 'Payments' if x =="" else x)

	#Convert the transaction amounts from strings to floats
	output['Amount'] = output.Amount.apply(lambda x: float(x))

	#Convert the date to a pandas datetime object
	output['Date'] = output.Date.apply(lambda x: pd.to_datetime(x))

	#Use clean_name function to remove garbage
	output['Company'] = output.Company.apply(lambda x: clean_names(x))

	output.drop_duplicates(inplace = True)

	return output.sort('Date')


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
	running_total = []
	total = 0
	for amount in out.Amount.values:
		total+= amount
		running_total.append(total)
	out['Cumulative_Amount'] = running_total

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
			user_input= 0
		else:
			user_input = int(user_input)
		run = user_input

		if user_input == 1:
			print "The balance is: ${0:.2f}".format(round(get_balance(data),2))

		elif user_input ==2:
			print expenses_by_cat.to_string()

		elif user_input ==3:
			print running_balance.to_string()

		elif user_input == 4:
			print data.to_string()
		else:
			break








