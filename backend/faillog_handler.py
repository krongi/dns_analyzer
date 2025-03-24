import os
import json
from datetime import datetime
import sys
import re

# UPLOAD_FOLDER = "/app/uploads"
# RESULT_FOLDER = "/app/results"
RESULT_FOLDER = "results"
UPLOAD_FOLDER = "uploads"
JSON_OUTPUT = "fail.json"

if not os.path.exists(os.path.join(os.getcwd(), RESULT_FOLDER)):
    os.mkdir(RESULT_FOLDER)

if not os.path.exists(os.path.join(os.getcwd(), UPLOAD_FOLDER)):
    os.mkdir(UPLOAD_FOLDER)

if not os.path.exists(os.path.join(os.getcwd(), JSON_OUTPUT)):
    with open(os.path.join(os.getcwd(), JSON_OUTPUT), 'w') as json_create:
        json_create.writable()

date_reg = re.compile(r'[A-z]{3} \d{2} \d{2}:\d{2}:\d{2}') # Run on each line of log first
host_reg = re.compile(r'(?!\s){1}\w+(?=\s){1}') # Run this on the second half of the split line
source_reg = re.compile(r'(?!\s){1}(\w+|\d+)(?=\[){1}')
pid_reg = re.compile(r'(?!\[){1}(\d+)(?=\]){1}')
message_reg = re.compile(r'  \[\]\: |\: ')
position = os.getcwd()


def parse_log():

    with open(os.path.join(os.getcwd(), "backend\\failog"), 'r') as lf:
        data_list = []
        for line in lf.readlines():
            print(line)

            line_date = date_reg.findall(line)[0]
            chunks = date_reg.split(line)
            new_chunk = ""
            for chunk in chunks:
                new_chunk += chunk

            if not host_reg.findall(new_chunk):
                line_host = "Null"
            else:
                line_host = host_reg.findall(new_chunk)[0]
                chunks = new_chunk.split(line_host)
                new_chunk = ""
                for chunk in chunks:
                    new_chunk += chunk

            if not source_reg.findall(new_chunk):
                line_source = "Null"
            else:
                line_source = source_reg.findall(new_chunk)[0]
                chunks = new_chunk .split(line_source)
                new_chunk = ""
                for chunk in chunks:
                    new_chunk += chunk

            if not pid_reg.findall(new_chunk):
                line_index = "Null"
            else:
                line_index = pid_reg.findall(new_chunk)[0]
                chunks = new_chunk.split(line_index)
                new_chunk = ""
                for chunk in chunks:
                    new_chunk += chunk

            line_message = message_reg.split(new_chunk)[1]
            
            data = {"Date": line_date, "Host": line_host, "Source": line_source, "Message": line_message}
            data_list.append(data)
    with open("fail.json", 'w') as oj:
        json.dump(data_list, oj, indent=4)

parse_log()