import re, csv

def get_first_level_column_label(start, end, table_head):
	rows = table_head.split('\n')
	rows_of_header_text_in_range_of_this_column = [row[start:end] for row in rows]
	header_text_in_range_of_this_column = ''.join(rows_of_header_text_in_range_of_this_column)
	header = re.split(r'[=]+', header_text_in_range_of_this_column)[-1]
	return header.strip()

def get_second_level_column_label(first_level_start, first_level_end, table_head):
	rows = table_head.split('\n')
	length_of_longest_row = max([len(row) for row in rows])
	rows = [ row.ljust(length_of_longest_row) for row in rows ]

	# get locations of header
	separator = ""
	for index in range(length_of_longest_row):
		separator += "=" if "=" in [row[index] for row in rows] else " "
	second_level_header_locations = [(m.start(0), m.end(0)) for m in re.finditer(r'[=]+', separator)]

	possible_second_level_header_locations = filter(lambda loc: first_level_start >= loc[0] and first_level_end <= loc[1] ,second_level_header_locations)
	if len(possible_second_level_header_locations) == 0: return ""
	if len(possible_second_level_header_locations) > 1: raise Exception('Unexpected Syntax. More than one possible second level header.')
	second_level_header_location = possible_second_level_header_locations[0]
	second_level_start = second_level_header_location[0]
	second_level_end = second_level_header_location[1]

	# select text in header locations that is above the '='
	rows_of_header_text_in_range_of_this_column = [row[second_level_start:second_level_end] for row in rows]
	header_text = ''.join(rows_of_header_text_in_range_of_this_column)
	header = re.split(r'[=]+', header_text)[0]
	return header.strip()

def extract_table(table_text):
	'''Parse the table_text and retun a "melted" version of the table'''
	try:
		head, body = re.split(r'\n[-\s]+\n', table_text)
	except:
		import pdb; pdb.set_trace()
	separator = re.search(r'\n+([- ]+)\n+', table_text).group(1)

	# get cell_locations array of [start, end] indexes based on separator location
	data_cell_locations = [(m.start(0), m.end(0)) for m in re.finditer(r'[-]+', separator)]
	row_label_cell_location = (0, data_cell_locations[0][0] - 1)

	rows = body.split('\n\n')
	data = []
	for row in rows:
		parts = row.split('\n')
		# if len(parts) > 2: import pdb; pdb.set_trace()#raise Exception("Unexpected Syntax. Expected each row in table to have either two parts (n,%) or just one parts (n). Found more than two parts in this item.")

		# Extract row label
		row_label = " ".join([r[row_label_cell_location[0]:row_label_cell_location[1]].strip() for r in row.split('\n')])
		if len(parts) == 1:
			n_row_text = parts[0]
			n_row = [n_row_text[location[0]:location[1]].strip() for location in data_cell_locations]
			pct_row = [''] * len(n_row)
		elif len(parts) > 1:
			n_row_text = parts[-2]
			n_row = [n_row_text[location[0]:location[1]].strip() for location in data_cell_locations]
			pct_row_text = parts[-1]
			pct_row = [pct_row_text[location[0]:location[1]].strip() for location in data_cell_locations]
		else:
			raise Exception('Unexpected Syntax. Less than one part.')

		first_level_labels = [get_first_level_column_label(location[0], location[1], head) for location in data_cell_locations]
		second_level_labels = [get_second_level_column_label(location[0], location[1], head) for location in data_cell_locations]
		row_labels = [row_label] * len(first_level_labels)

		data_matrix = zip(row_labels,second_level_labels,first_level_labels, n_row, pct_row)
		data += data_matrix
	return data


# Open file and collect data
with open('crosstabs.rtf') as file:
	data = file.read()
	pages = data.replace('\line','').split('\page')

csv_data = []
headers = ['table_number', 'table', 'question_text', 'row_label', 'toplevel_y_label', 'y_label', 'n', 'pct']
csv_data.append(headers)
for page in pages:
	page = re.sub(r'\n+$', '', page)
	page = re.sub(r' \(continued\)', '', page)

	# Get Metadata from each page
	regex = re.compile(r'(TABLE \d+)\n(.*)\n{3,} (.*)', re.DOTALL)
	table_match = re.search(regex, page)
	if not table_match: import pdb; pdb.set_trace()#raise Exception('Table not found on this page.')

	table_number_string = table_match.group(1)
	print "Extracting %s" % table_number_string
	table_number = re.search(r'\d+', table_number_string).group(0)
	question_text = table_match.group(2) # EXTRACT QUESTION TEXT

	# Get the table text from the page
	body = table_match.group(3)
	split_body = re.split(r'\n{3,}', body)
	if len(split_body) == 1:
		table_text = body
	elif len(split_body) > 1:
		table_text = split_body[0]
		note = split_body[1]
	else:
		raise Exception('Unexpected Syntax.')

	table_csv_data = [ (table_number, table_number_string, question_text) + row for row in extract_table(table_text)]
	csv_data += table_csv_data

# Write csv_data to file
with open('crosstabs.csv', 'wb') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(csv_data)