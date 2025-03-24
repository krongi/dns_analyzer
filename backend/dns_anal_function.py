import re
import subprocess
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import sys
from datetime import datetime
import os

UPLOAD_FOLDER = "/app/uploads"
RESULT_FOLDER = "/app/results"

log_file = sys.argv[1] if len(sys.argv) > 1 else "log.txt"
# log_file = "failog"
progress_file = "progress.json"

def update_progress(status, progress, message):
    with open(progress_file, "w") as f:
        json.dump({"status": status, "progress": progress, "message": message}, f)

# Extract filename without extension for JSON naming
log_filename = os.path.splitext(os.path.basename(log_file))[0]
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
result_filename = f"{log_filename}_{timestamp}.json"
result_path = os.path.join(RESULT_FOLDER, result_filename)

# Start processing
update_progress("processing", 0, "Initializing processing...")

# Regex patterns
date_reg = re.compile(r'[A-z]{3} \d{2} \d{2}:\d{2}:\d{2}') # Run on each line of log first
# host_reg = re.compile(r'(?<=\d+ )\w+(?= \S+\:)') # Run this on the second half of the split line
host_reg = re.compile(r'(?<=\w{3} \d\d \d\d:\d\d:\d\d )\w+(?= \S+\:)')
# source_reg = re.compile(r'(?<=[A-z]{3} \d{2} \d{2}:\d{2}:\d{2} \S+ )\S+(?=\:)')
source_reg = re.compile(r'(?<=\w{3} \d\d \d\d\:\d\d\:\d\d )\w+(?= \S+\:)')
# pid_reg = re.compile(r'(?<=\[)\d+(?=\])')
pid_reg = re.compile(r'(?!\[)\d+(?=\])')

split_to_source_reg = re.compile(r'\w+ \d\d \d\d:\d\d:\d\d \w+ ') #grabs everything up to the source column
split_out_source_reg = re.compile(r'\S+(?=:)')

message_split_reg = re.compile(r'[A-z]{3} \d\d \d\d:\d\d:\d\d \S+ \S+ ')

ip_regex = re.compile(r'(\d{1,3}\.){3}\d{1,3}$')
sld_regex = re.compile(r'([^.]+\.[^.]+)$')

def get_log_date(log_line):
    return date_reg.findall(log_line)[0]

def get_log_host(log_line):
    return host_reg.findall(log_line)[0]

def get_log_source_and_pid(log_line):
    split_to = split_to_source_reg.split(log_line)
    split_out = split_out_source_reg.findall(split_to[1])[0]
    if split_out.endswith("]"):
        pid = split_out.split("[")[1]
        pid = pid.split("]")[0]
        split_out = split_out.split("[")[0]
        return split_out, pid
    else:
        pid = None
        return split_out, pid
    # return split_out_source_reg.split(split_to_source_reg.split(log_line)[1])[0]

# def get_log_pid(log_line):
#     if not pid_reg.findall(log_line):
#         print("No PID for this entry\n")
#     else:
#         return pid_reg.findall(log_line)

def get_log_message(log_line):
    if len(message_split_reg.split(log_line)) == 2:
        return message_split_reg.split(log_line)[1]
    elif message_split_reg.split(log_line) > 2:
        message_string = ""
        for item in message_split_reg.split(log_line)[1:]:
            message_string += item
        return message_string
ips = set()
domains = set()

def parse_log(source=log_file):
    with open(os.path.join(os.getcwd(), source), 'r') as lf:
        data_list = []
        for line in lf.readlines():
            print(line)
            if source_reg.findall(line) == "dnsmasq":
                print("dnsmasq log detected, changing functions")
                dnsmasq_parse()
                break
            # line_date = date_reg.findall(line)[0]
            # chunks = date_reg.split(line)
            # new_chunk = ""
            # for chunk in chunks:
            #     new_chunk += chunk

            # if not host_reg.findall(new_chunk):
            #     line_host = "Null"
            # else:
            #     line_host = host_reg.findall(new_chunk)[0]
            #     chunks = new_chunk.split(line_host)
            #     new_chunk = ""
            #     for chunk in chunks:
            #         new_chunk += chunk

            # if not source_reg.findall(new_chunk):
            #     line_source = "Null"
            # else:
            #     line_source = source_reg.findall(new_chunk)[0]
            #     chunks = new_chunk .split(line_source)
            #     new_chunk = ""
            #     for chunk in chunks:
            #         new_chunk += chunk

            # if not pid_reg.findall(new_chunk):
            #     line_index = "Null"
            # else:
            #     line_index = pid_reg.findall(new_chunk)[0]
            #     chunks = new_chunk.split(line_index)
            #     new_chunk = ""
            #     for chunk in chunks:
            #         new_chunk += chunk

            # line_message = message_reg.split(new_chunk)[1]

            line_date = get_log_date(line)
            line_host = get_log_host(line)
            line_source, line_pid = get_log_source_and_pid(line)
            line_message = get_log_message(line)
            
            data = {"Date": line_date, "Host": line_host, "Source": line_source, "Message": line_message, "PID": line_pid}
            data_list.append(data)
    with open(os.path.join((RESULT_FOLDER),"fail.json"), 'w') as oj:
        json.dump(data_list, oj, indent=4)

def is_private_ip(ip):  
    private_patterns = [
        re.compile(r'^10\.'),
        re.compile(r'^192\.168\.'),
        re.compile(r'^172\.(1[6-9]|2[0-9]|3[0-1])\.')
    ]
    return any(p.match(ip) for p in private_patterns)

def run_dig(domain):
    result = subprocess.run(['dig', '+short', domain], capture_output=True, text=True)
    domain_ips = set()
    for line in result.stdout.strip().split('\n'):
        if ip_regex.match(line) and not is_private_ip(line):
            domain_ips.add(line)
    return domain, domain_ips

def run_whois(sld):
    result = subprocess.run(['whois', sld], capture_output=True)
    output = result.stdout.decode('utf-8', errors='ignore').splitlines()
    cleaned_output = []
    for line in output:
        if 'Inaccuracy complaint form' in line:
            break
        cleaned_output.append(line.strip())
    return sld, cleaned_output

parse_log()

def dnsmasq_parse():
    # ips = set()
    # domains = set()

    update_progress("processing", 10, "Reading log file...")

    with open(log_file, 'r') as file:
        for line in file:
            parts = line.strip().split(': ', 1)
            if len(parts) < 2 or 'DHCP' in line:
                continue
            message = parts[1]
            first_word = message.split(' ', 1)[0]

            if first_word.startswith(('query', 'forwarded')):
                potential_ip = message.rsplit(' ', 1)[-1]
                if ip_regex.match(potential_ip) and not is_private_ip(potential_ip):
                    ips.add(potential_ip)

            elif first_word.startswith(('cached', 'reply')):
                if any(keyword in message for keyword in ['NODATA', '<CNAME>', '<HTTPS>']):
                    domain = message.split(' ')[1]
                    domains.add(domain)

            elif first_word == 'gravity':
                action, domain, _, ip = message.split(' ', 3)
                domains.add(domain)
                if ip_regex.match(ip) and not is_private_ip(ip):
                    ips.add(ip)
    # return ips, domains

    update_progress("processing", 30, "Running dig queries...")


    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_dig, domain) for domain in domains]
        domain_ip_map = defaultdict(set)
        for i, future in enumerate(futures):
            domain, domain_ips = future.result()
            ips.update(domain_ips)
            domain_ip_map[domain] = domain_ips
            if i % 10 == 0:
                update_progress("processing", 50, f"Processed {i}/{len(domains)} domains...")

    update_progress("processing", 70, "Running WHOIS queries...")

    unique_slds = {sld_regex.search(domain).group(1) for domain in domains if sld_regex.search(domain)}

    with ThreadPoolExecutor(max_workers=10) as executor:
        whois_futures = [executor.submit(run_whois, sld) for sld in unique_slds]
        whois_info = {sld: info for sld, info in (f.result() for f in whois_futures)}

    update_progress("processing", 90, "Compiling results...")

    structured_data = defaultdict(lambda: {"whois": [], "domains": defaultdict(list)})
    for domain, ips in domain_ip_map.items():
        sld_match = sld_regex.search(domain)
        if sld_match:
            sld = sld_match.group(1)
            structured_data[sld]["domains"][domain].extend(sorted(ips))
            structured_data[sld]["whois"] = whois_info.get(sld, [])

    with open(RESULT_FOLDER + '/' + result_filename, 'w') as f:
        json.dump(structured_data, f, indent=4)

# os.remove(log_file)

    update_progress("complete", 100, "Processing complete.")
