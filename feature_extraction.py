import re
import string
import os
import json


class FeatureExtraction:

    def __init__(self, file):
        self.log = []
        self.output = []
        self.script = {}
        self.js = {}
        with open(file, 'r') as f:
            self.log = f.readlines()

    def identify_script(self):
        for line in self.log:
            id_pa = re.compile('(?<=^\$)\d+')
            url_pa = re.compile('(^\$\d+:")(.*?(?="))')
            child_id_pa = re.compile('(^\$\d+:)(\d+(?=:))')
            id_found = re.search(id_pa, line)
            if id_found:
                id = id_found.group(0)
                url_found = re.search(url_pa, line)
                child_id_found = re.search(child_id_pa, line)
                if url_found:
                    url = url_found.group(2).replace('https\\', 'https')
                    url = url.replace('http\\', 'http')
                    self.script[id] = url
                if child_id_found:
                    child_id = id
                    self.script[id] = self.script[child_id_found.group(2)]

    def split_log(self):
        id = 0
        id_pa = re.compile(r'(?<=!)\d+')
        for line in self.log:
            if line.startswith('!'):
                id_found = re.search(id_pa, line)
                if id_found:
                    id = id_found.group(0)
                    if id not in self.js.keys():
                        self.js[id] = []
            if id:
                self.js[id].append(line)

    def collect_feature(self):
        self.identify_script()
        self.split_log()
        for key, value in self.js.items():
            features = {}
            features['url'] = self.script[key]
            features['contain_fingerprint_keyword'] = True if ('fingerprint' in self.script[key]) else False
            for line in value:
                if line.startswith('$'):
                  continue 
                if line.startswith('c'):
                   substrings = re.split(":",line[1:])
                   for p in string.punctuation:
                       substrings[1] = substrings[1].replace(p, '')
                       substrings[2] = substrings[2].replace(p, '')
                   feature = re.sub('\n', '', substrings[2])
                   if(substrings[1]):
                       feature = feature + "." + substrings[1]
                   if(len(substrings) < 4):
                       features[feature] = True
                   else:
                       length = 0
                       for argument in substrings[3:]:
                           if '<anonymous>' not in argument:
                               length += len(argument)
                       if(length):
                            features[feature] = length
                       else:
                            features[feature] = True
                if line.startswith('n'):
                   substrings = re.split(":",line[1:])
                   for p in string.punctuation:
                       substrings[1] = substrings[1].replace(p, '')
                   feature = re.sub('\n', '', substrings[1])
                   if (len(substrings) < 3):
                       features[feature] = True
                   else:
                       length = 0
                       for argument in substrings[2:]:
                           if '<anonymous>' not in argument:
                               length += len(argument)
                       if(length):
                            features[feature] = length
                       else:
                            features[feature] = True
                if line.startswith('g'):
                   substrings = re.split(":",line[1:])
                   for p in string.punctuation:
                       substrings[1] = substrings[1].replace(p, '')
                       substrings[2] = substrings[2].replace(p, '')
                   features[substrings[1] + "." + re.sub('\n', '', substrings[2])] = True
                if line.startswith('s'):
                   substrings = re.split(":",line[1:])
                   for p in string.punctuation:
                       substrings[1] = substrings[1].replace(p, '')
                       substrings[2] = substrings[2].replace(p, '')
                   features[substrings[1] + "." + re.sub('\n', '', substrings[2])] = len(substrings[3])            
            self.output.append(features)
        return self.output


output_file = open("features.json", 'a', encoding="utf-8")
base_path = "C:\CS568\Projects\Fingerprint"
result = []
all_features = {}
total=0
for sub_dir in os.listdir(base_path):
    if not sub_dir.startswith('.'):
        for file in os.listdir(base_path + "\\" + sub_dir):
            try:
                if not file.startswith('.'):
                    print(base_path + "\\"+sub_dir+'\\'+file)
                    feature = FeatureExtraction(base_path + "\\"+sub_dir+'\\'+file)
                    result.extend(feature.collect_feature())
            except Exception as e:
                print('error--', e)
                continue
for dic in result:
    all_features.update(dic)
    total+= len(dic)
feature_information = {}
feature_information['total_scripts'] = len(result)
feature_information['total_features'] = len(all_features)
feature_information['unique_features'] = total
output_file.write(json.dumps([feature_information]) + '\n')
print("Total number of scripts : {}".format(len(result)))
print("Total features recorded : {}".format(len(all_features)))
print("Total number of unique features : {}".format(total))
output_file.write(json.dumps(result) + '\n')

