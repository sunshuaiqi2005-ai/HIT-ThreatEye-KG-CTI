import api
import preprocessor
import openai
network = [3,4,5,6,7,8,9,10,21,22,23,24,25,26,27,28,29,30]

for i in network:
    querylist = preprocessor.GetPDFContent(f"40\{i}.pdf", 16384)
    print(f"{i}.pdf已经处理完毕,分割为{len(querylist)}份")
    relationship = ''
    a = 0
    for query in querylist:
        a += 1
        try:
            relationship += api.API2('qwen', query, 'text', api.default_prompt)
        except openai.BadRequestError as e:
            if e.message == 'Output data may contain inappropriate content.':
                continue
        print(f"第{a}份处理完成")
    f = open(f"outputDir/test/{i}.txt", "w+", encoding="utf-8")
    f.write(relationship)
    print("写入完成")
    f.close()