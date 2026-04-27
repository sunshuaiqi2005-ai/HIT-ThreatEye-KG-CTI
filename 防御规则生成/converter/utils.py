from dataclasses import dataclass

@dataclass
class IndexInfo:
    id: int
    type: str
    subtype: str
    value: str
    level: int = 3
    confidence: float = 0.9
    description: str = ""

def print_indexlist(indexlist: list[IndexInfo]):
    result = {"ip": [], "domain": [], "hash": [], "hex": [], "email": []}
    for index in indexlist:
        match index.type:
            case "ip":
                result["ip"].append(index)
            case "domain":
                result["domain"].append(index)
            case "hash":
                result["hash"].append(index)
            case "email":
                result["email"].append(index)
            case "hex":
                result["hex"].append(index)
    for key, value_list in result.items():
        print(f"\n {key.upper()} 类别下的值:")
        
        if value_list:
            for value in value_list:
                print(f"  - {value}")