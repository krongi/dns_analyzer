# import os


# import json
# from datetime import datetime
# import sys
# import re

# date_reg = re.compile(r'([A-z]{3} \d{2} \d{2}:\d{2}:\d{2})') # Run on each line of log first
# host_reg = re.compile(r'(?!\s){1}\w+(?=\s){1}') # Run this on the second half of the split line
# log_source_reg = re.compile(r'(?!\s){1}(\w+|\d+)(?=\[){1}')
# index_reg = re.compile(r'(?!\[){1}(\d+)(?=\]){1}')

# with open(position + 'testlog.log', 'r') as logie:
#     for line in logie.readlines():

#         line_date = date_reg.findall(line)
#         chunks = line.split(line_date[0])
#         new_chunk = ""
#         for chunk in chunks:
#             new_chunk += chunk
#         print(new_chunk)


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
index_reg = re.compiler(r'(?!\[){1}(\d+)(?=\]){1}')

log_file = sys.argv[1] if len(sys.argv) > 1 else "log.txt"
progress_file = "progress.json"

def update_progress(status, progress, message):
    with open(progress_file, "w") as f:
        json.dump({"status": status, "progress": progress, "message": message}, f)

log_filename = os.path.splitext(os.path.basename(log_file))[0]
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
result_filename = f"{log_filename}_{timestamp}.json"
result_path = os.path.join(RESULT_FOLDER, result_filename)

with open(log_file, 'r', encoding="utf-8") as log:
    for line in log.readlines():
        split_lines = re.split(date_reg, line)
        line_date, rest = split_lines[0], split_lines[1]
