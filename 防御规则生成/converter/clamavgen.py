from utils import IndexInfo
import os
import datetime

def gen_CLAM_ruleset_for_hash(hash: IndexInfo) -> list[str]:
    match hash.subtype:
        case "md5":
            return [f"{hash.value}:100:MD5Hash\n"]
        case "sha1":
            return [f"{hash.value}:100:SHA1Hash\n"]
        case "sha256":
            return [f"{hash.value}:100:SHA256Hash\n"]
        case "sha512":
            return [f"{hash.value}:100:SHA512Hash\n"]
        case _:
            return []

def gen_CLAM_ruleset_for_hex(hex: IndexInfo) -> list[str]:
    return [f"MyRule:*:*:{hex.value.hex().upper()}\n"]

def gen_CLAM_ruleset(indexlist: list[IndexInfo]) -> list[str]:
    hash_rules = []
    string_rules = []
    for index in indexlist:
        match index.type:
            case "hash":
                hash_rules += gen_CLAM_ruleset_for_hash(index)
            case "hex":
                string_rules += gen_CLAM_ruleset_for_hex(index)
    return hash_rules, string_rules

def save_rule_file(rules, output_filename, types):
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    if types == "hash":
        filename = f"{output_filename}-clamav-{current_date}.hdb"
    if types == "hex":
        filename = f"{output_filename}-clamav-{current_date}.ndb"
    
    output_folder = "CREATED_IOCs"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    file_path = os.path.join(output_folder, filename)
    with open(file_path, "w") as file:
        file.writelines(rules)
    
    print(f"ClamAV rules saved to: {file_path}")
