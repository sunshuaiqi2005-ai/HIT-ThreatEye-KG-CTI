import json

with open('data.json','r',encoding='utf-8') as file:
    data = json.load(file)

rate_list = [0 for i in range(10)]
for key,value in data.items():
    val = []
    for _key,_value in value.items():
        val.append(_value) 
    for i in range(0,len(rate_list)):
        rate_list[i] += val[i]

print(rate_list)