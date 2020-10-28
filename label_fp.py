import labeling_heuristics as lb
import os
import json

output_file = open("result_fp.json", 'a', encoding="utf-8")

for sub_dir in os.listdir('logs'):
    result = {}
    if not sub_dir.startswith('.'):
        for file in os.listdir('logs/' + sub_dir):
            try:
                if not file.startswith('.'):
                    print('logs/'+sub_dir+'/'+file)
                    label = lb.Labeling('logs/'+sub_dir+'/'+file)
                    if sub_dir not in result.keys():
                        result[sub_dir] = label.if_fp()
                    else:
                        result[sub_dir].extend(label.if_fp())
            except Exception as e:
                print(file)
                print('error--', e)
                continue
    output_file.write(json.dumps(result) + '\n')

