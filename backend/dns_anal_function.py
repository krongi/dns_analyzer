# import re
# import subprocess
# import json
# from collections import defaultdict
# from concurrent.futures import ThreadPoolExecutor
# import sys

# log_file = sys.argv[1] if len(sys.argv) > 1 else "log.txt"

# # Regex patterns
# ip_regex = re.compile(r'(\d{1,3}\.){3}\d{1,3}$')
# sld_regex = re.compile(r'([^.]+\.[^.]+)$')

# # Check if IP is private
# def is_private_ip(ip):
#     private_patterns = [
#         re.compile(r'^10\.'),
#         re.compile(r'^192\.168\.'),
#         re.compile(r'^172\.(1[6-9]|2[0-9]|3[0-1])\.')
#     ]
#     return any(p.match(ip) for p in private_patterns)

# ips = set()
# domains = set()

# # Process the log file
# with open(log_file, 'r') as file:
#     for line in file:
#         parts = line.strip().split(': ', 1)
#         if len(parts) < 2 or 'DHCP' in line:
#             continue
        
#         message = parts[1]
#         first_word = message.split(' ', 1)[0]

#         if first_word.startswith(('query', 'forwarded')):
#             potential_ip = message.rsplit(' ', 1)[-1]
#             if ip_regex.match(potential_ip) and not is_private_ip(potential_ip):
#                 ips.add(potential_ip)

#         elif first_word.startswith(('cached', 'reply')):
#             if any(keyword in message for keyword in ['NODATA', '<CNAME>', '<HTTPS>']):
#                 domain = message.split(' ')[1]
#                 domains.add(domain)

#         elif first_word == 'gravity':
#             action, domain, _, ip = message.split(' ', 3)
#             domains.add(domain)
#             if ip_regex.match(ip) and not is_private_ip(ip):
#                 ips.add(ip)

# # Function to run dig on a domain
# def run_dig(domain):
#     result = subprocess.run(['dig', '+short', domain], capture_output=True, text=True)
#     domain_ips = set()
#     for line in result.stdout.strip().split('\n'):
#         if ip_regex.match(line) and not is_private_ip(line):
#             domain_ips.add(line)
#     return domain, domain_ips

# # Run dig concurrently
# with ThreadPoolExecutor(max_workers=10) as executor:
#     futures = [executor.submit(run_dig, domain) for domain in domains]
#     domain_ip_map = defaultdict(set)
#     for future in futures:
#         domain, domain_ips = future.result()
#         ips.update(domain_ips)
#         domain_ip_map[domain] = domain_ips

# # Extract unique second-level domains
# unique_slds = {sld_regex.search(domain).group(1) for domain in domains if sld_regex.search(domain)}

# # Function to run whois on SLD
# def run_whois(sld):
#     result = subprocess.run(['whois', sld], capture_output=True)
#     output = result.stdout.decode('utf-8', errors='ignore').splitlines()
#     cleaned_output = []
#     for line in output:
#         if 'Inaccuracy complaint form' in line:
#             break
#         cleaned_output.append(line.strip())
#     return sld, cleaned_output

# # Run whois concurrently
# with ThreadPoolExecutor(max_workers=10) as executor:
#     whois_futures = [executor.submit(run_whois, sld) for sld in unique_slds]
#     whois_info = {sld: info for sld, info in (f.result() for f in whois_futures)}

# # Organize data into structured JSON with whois lines as children
# structured_data = defaultdict(lambda: {"whois": [], "domains": defaultdict(list)})
# for domain, ips in domain_ip_map.items():
#     sld_match = sld_regex.search(domain)
#     if sld_match:
#         sld = sld_match.group(1)
#         structured_data[sld]["domains"][domain].extend(sorted(ips))
#         structured_data[sld]["whois"] = whois_info.get(sld, [])

# # Save structured domains, IPs, and whois as JSON
# with open('domains_with_ips.json', 'w') as f:
#     json.dump(structured_data, f, indent=4)

import re
import subprocess
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import sys
from datetime import datetime
import os

log_file = sys.argv[1] if len(sys.argv) > 1 else "log.txt"
progress_file = "progress.json"

def update_progress(status, progress, message):
    with open(progress_file, "w") as f:
        json.dump({"status": status, "progress": progress, "message": message}, f)

# Extract filename without extension for JSON naming
log_filename = os.path.splitext(os.path.basename(log_file))[0]
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
result_filename = f"{log_filename}_{timestamp}.json"
result_path = os.path.join("results", result_filename)

# Start processing
update_progress("processing", 0, "Initializing processing...")

# Regex patterns
ip_regex = re.compile(r'(\d{1,3}\.){3}\d{1,3}$')
sld_regex = re.compile(r'([^.]+\.[^.]+)$')

def is_private_ip(ip):
    private_patterns = [
        re.compile(r'^10\.'),
        re.compile(r'^192\.168\.'),
        re.compile(r'^172\.(1[6-9]|2[0-9]|3[0-1])\.')
    ]
    return any(p.match(ip) for p in private_patterns)

ips = set()
domains = set()

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

update_progress("processing", 30, "Running dig queries...")

def run_dig(domain):
    result = subprocess.run(['dig', '+short', domain], capture_output=True, text=True)
    domain_ips = set()
    for line in result.stdout.strip().split('\n'):
        if ip_regex.match(line) and not is_private_ip(line):
            domain_ips.add(line)
    return domain, domain_ips

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

def run_whois(sld):
    result = subprocess.run(['whois', sld], capture_output=True)
    output = result.stdout.decode('utf-8', errors='ignore').splitlines()
    cleaned_output = []
    for line in output:
        if 'Inaccuracy complaint form' in line:
            break
        cleaned_output.append(line.strip())
    return sld, cleaned_output

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

with open('results/'+result_filename, 'w') as f:
    json.dump(structured_data, f, indent=4)

update_progress("complete", 100, "Processing complete.")
