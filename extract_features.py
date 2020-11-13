import re
import os
import json
from tld import get_fld
from collections import Counter
import math
import copy
import numpy as np
import pandas as pd

# added arguments, fld as features

if not os.path.isdir("./features"):
    os.mkdir("./features")
output_file = open("features/features_new.json", 'a', encoding="utf-8")
feature_df_file = "features/dataset_df.csv"


class FEATURE:

    def __init__(self, log_file):
        self.log = []
        self.output = []
        self.script = {}
        self.js = {}
        print(log_file)
        with open(log_file, 'r') as f:
            self.log = f.readlines()
        self.domain = file.replace('http___', '').replace('_', '')
        self.identify_script()
        self.split_log()

        self.fpjs2_keys = []

    # ---------------------------------------
    # collect script id, url
    # ---------------------------------------
    def identify_script(self):
        for line in self.log:
            line = line.rstrip()
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
                    if not url.startswith("http"):
                        print("invalid url: ", url)
                        continue
                    self.script[id] = url
                if child_id_found:
                    self.script[id] = self.script[child_id_found.group(2)]

    def split_log(self):
        id = 0
        id_pa = re.compile(r'(?<=!)\d+')
        for line in self.log:
            line = line.rstrip()
            if line.startswith('!'):
                id_found = re.search(id_pa, line)
                if id_found:
                    id = id_found.group(0)
                    if id not in self.js.keys():
                        self.js[id] = []
            if id and not line.startswith('!') and not line.startswith('$'):
                self.js[id].append(line)

    def similarityToFpjs2(self):
        g_pat = re.compile(r'(?<=:){.*?}:.*')
        c_pat = re.compile(r'(?<=:).*')
        c_pat_first = re.compile(r'(.*?:.*?)(:)(.*)')
        id = 0
        id_pa = re.compile(r'(?<=!)\d+')
        fpjs2 = {}
        fpjs2['fpjs2'] = []
        with open('fpjs2.log', 'r') as f:
            fp_log = f.readlines()
        for line in fp_log:
            if line.startswith('!'):
                id_found = re.search(id_pa, line)
                if id_found:
                    id = id_found.group(0)
            if id == '13' and not line.startswith('!') and not line.startswith('$'):
                fpjs2['fpjs2'].append(line)
        fpjs2_features = {}
        for key, value in fpjs2.items():
            for each in value:
                if each.startswith('g'):
                    # print('g--', each)
                    # print(call)
                    call = re.search(g_pat, each).group(0)
                    if call in fpjs2_features.keys():
                        fpjs2_features[call] += 1
                    else:
                        fpjs2_features[call] = 1
                if each.startswith('c'):
                    access = re.search(c_pat, each).group(0)
                    if access.count(':') > 1:
                        c_access = re.search(c_pat_first, access)
                        call = c_access.group(1)
                        argu = c_access.group(3)
                        if call in fpjs2_features.keys() and argu == fpjs2_features[call]:
                            continue
                        else:
                            fpjs2_features[call] = argu

    def counter_cosine_similarity(self, c1, c2):
        terms = set(c1).union(c2)
        try:
            dotprod = 0.0
            magA = 0.0
            magB = 0.0
            for k in terms:
                if k in c1 and k in c2:
                    if type(c1[k]) == str or ":" in k:
                        if c1[k] == c2[k]:
                            dotprod += 1.0
                        magB += 1.0
                        magA += 1.0
                    else:
                        dotprod += float(c1.get(k, 0)) * float(c2.get(k, 0))
                        magA += float(c1.get(k, 0)) ** 2
                        magB += float(c2.get(k, 0)) ** 2
                else:
                    if k in c1:
                        if type(c1[k]) == str:
                            magA += 1.0
                        else:
                            magA += float(c1.get(k, 0)) ** 2
                    else:
                        if type(c2[k]) == str:
                            magB += 1.0
                        else:
                            magB += float(c2.get(k, 0)) ** 2
            # dotprod = sum(float(c1.get(k, 0)) * float(c2.get(k, 0)) for k in terms)
            # magA = math.sqrt(sum(float(c1.get(k, 0)) ** 2 for k in terms))
            # magB = math.sqrt(sum(float(c2.get(k, 0)) ** 2 for k in terms))
            return dotprod / (math.sqrt(magA) * math.sqrt(magB))
        except Exception as e:
            print(e, c2)
            pass

    def extract_features(self):
        g_pat = re.compile(r'(?<=:){.*?}:.*')
        c_pat = re.compile(r'(?<=:).*')
        c_pat_first = re.compile(r'(.*?:.*?)(:)(.*)')
        for key, value in self.js.items():
            features = dict()
            features['domain'] = self.domain
            if key not in self.script:
                continue
            features['url'] = self.script[key]
            try:
                features['fld'] = get_fld(features['url'], fix_protocol=True)
            except Exception as e:
                print(e)
                pass
            if 'fingerprint' in self.script[key]:
                features['fpurl'] = 1
            # print(self.script[key], value)
            for each in value:
                if each.startswith('g'):
                    # print('g--', each)
                    # print(call)
                    call = re.search(g_pat, each).group(0)
                    if call in features.keys():
                        features[call] += 1
                    else:
                        features[call] = 1
                if each.startswith('c'):
                    access = re.search(c_pat, each).group(0)
                    if access.count(':') > 1:
                        c_access = re.search(c_pat_first, access)
                        call = c_access.group(1)
                        argu = c_access.group(3)
                        if call in features.keys() and argu == features[call]:
                            continue
                        else:
                            features[call] = argu
            # compare = copy.deepcopy(features)
            # del compare['domain']
            # del compare['url']
            # del compare['fld']
            # new_compare = {}
            # for key, value in compare.items():
            #     if type(value) == int:
            #         new_compare[key] = value
            #     else:
            #         print(key, value)
            # print("new_compare", new_compare)
            # sim = self.counter_cosine_similarity(fpjs2, compare)
            # print("sim", sim)
            # assert sim <= 1.0
            output_file.write(json.dumps(features) + '\n')
            return features


class DataSet:

    def __init__(self, features):
        self.raw_features = features
        self.feature_withtype = self.get_feature_dict()
        self.padded_features = self.pad_raw_features()

    def get_feature_dict(self):
        feature_withtype = dict()
        for feat_dict in self.raw_features:
            features = list(feat_dict.keys())
            for feat in features:
                if feat in feature_withtype:
                    continue
                feature_withtype[feat] = type(feat_dict[feat])

        return feature_withtype

    def pad_raw_features(self):
        # pad the missing features so that each features will have same set of keys
        padded_features = dict()
        all_feat_keys = set(list(self.feature_withtype.keys()))
        for each_key in all_feat_keys:
            padded_features[each_key] = []
        for each_feat_dict in self.raw_features:
            padded_one_feat_dict = copy.deepcopy(each_feat_dict)
            feat_keys = set(list(padded_one_feat_dict.keys()))
            for one_missed_key in all_feat_keys - feat_keys:
                if self.feature_withtype[one_missed_key] == str:
                    padded_one_feat_dict[one_missed_key] = "NaN"
                else:
                    padded_one_feat_dict[one_missed_key] = np.nan

            for key, value in padded_one_feat_dict.items():
                padded_features[key].append(value)

        feat_num_values = [len(value) for _, value in padded_features.items()]
        assert max(feat_num_values) == min(feat_num_values)
        return padded_features

    def to_df(self):
        return pd.DataFrame.from_dict(self.padded_features)



with open('fpjs2.json', 'r') as f:
    for line in f:
        fpjs2 = json.loads(line)
        for k, v in fpjs2.items():
            try:
                fpjs2[k] = float(v)
            except Exception as e:
                pass
    # print(fpjs2)

all_features = []
for sub_dir in os.listdir('logs'):
    result = {}
    if not sub_dir.startswith('.'):
        for file in os.listdir('logs/' + sub_dir):
            try:
                if not file.startswith('.'):
                    print('logs/'+sub_dir+'/'+file)
                    label = FEATURE('logs/'+sub_dir+'/'+file)

                    features = label.extract_features()
                    all_features.append(features)
            except Exception as e:
                print(file)
                print('error--', e)
                continue
dataset = DataSet(all_features)
dataset_df = dataset.to_df()
dataset_df = dataset_df.set_index(["url", "domain", "fld"])
dataset_df_dummy = pd.get_dummies(dataset_df)
dataset_df_dummy = dataset_df_dummy.fillna(0)
print(dataset_df.shape)
print(list(dataset_df.columns))
print(dataset_df.dtypes)

print("dummy: ", dataset_df_dummy.shape)
print(list(dataset_df_dummy.columns))

dataset_df_dummy.to_csv(feature_df_file)
