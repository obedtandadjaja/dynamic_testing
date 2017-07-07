import json
from pprint import pprint

with open("tree_test_cases/test3.json") as data_file:
	data = json.load(data_file)

pprint(data)