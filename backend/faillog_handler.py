import os
import json
from datetime import datetime
import sys
import re

UPLOAD_FOLDER = "/app/uploads"
RESULT_FOLDER = "/app/results"

date_reg = re.compile(r'[A-z]{3} \d{2} \d{2}:\d{2}:\d{2}') # Run on each line of log first
host_reg = re.compile(r'(?!\s){1}\w+(?=\s){1}') # Run this on the second half of the split line
log_source_reg = re.compile(r'(?!\s){1}(\w+|\d+)(?=\[){1}')
index_reg = re.compile(r'(?!\[){1}(\d+)(?=\]){1}')
message_reg = re.compile(r'  \[\]\: ')
position = os.getcwd()

log_file = sys.argv[1] if len(sys.argv) > 1 else "log.txt"
progress_file = "progress.json"

log_file_name = os.path.splitext(os.path.basename(log_file))[0]
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
result_filename = f"{log_file_name}_{timestamp}.json"
result_path = os.path.join(RESULT_FOLDER, result_filename)

with open(log_file_name, 'r') as lf:
    for line in lf.readlines():
        print(line)

        line_date = date_reg.findall(line)[0]
        chunks = date_reg.split(line)
        new_chunk = ""
        for chunk in chunks:
            new_chunk += chunk

        line_host = host_reg.findall(new_chunk)[0]
        chunks = new_chunk.split(line_host)
        new_chunk = ""
        for chunk in chunks:
            new_chunk += chunk

        line_source = log_source_reg.findall(new_chunk)[0]
        chunks = new_chunk .split(line_source)
        new_chunk = ""
        for chunk in chunks:
            new_chunk += chunk

        line_index = index_reg.findall(new_chunk)[0]
        chunks = new_chunk.split(line_index)
        new_chunk = ""
        for chunk in chunks:
            new_chunk += chunk

        line_message = message_reg.split(new_chunk)[1]
