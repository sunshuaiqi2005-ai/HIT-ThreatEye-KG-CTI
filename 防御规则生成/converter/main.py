import os
import datetime
from suricatagen import gen_SRCT_ruleset
from clamavgen import gen_CLAM_ruleset
from parser import parse_doc_for_index_set
from utils import print_indexlist

def save_rule_file(rules, output_filename, types):
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    if types == "hash":
        filename = f"{output_filename}-clamav-{current_date}.hdb"
    if types == "hex":
        filename = f"{output_filename}-clamav-{current_date}.ndb"
    if types == "suricata":
        filename = f"{output_filename}-suricata-{current_date}.rules"
    
    output_folder = "CREATED_IOCs"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    file_path = os.path.join(output_folder, filename)
    with open(file_path, "w") as file:
        file.writelines(rules)
    
    print(f"rules saved to: {file_path}")

def gen_rulefile_from_indexfile(input_file: str, output_file: str):
    indexlist = parse_doc_for_index_set(input_file)
    print_indexlist(indexlist)
    rules = gen_SRCT_ruleset(indexlist)
    save_rule_file(rules, output_file, "suricata")
    hash_rules, string_rules = gen_CLAM_ruleset(indexlist)
    save_rule_file(hash_rules, output_file, "hash")
    save_rule_file(string_rules, output_file, "hex")

if __name__ == "__main__":
    input_file = "test.txt"
    output_file = "test"

    gen_rulefile_from_indexfile(input_file, output_file)

