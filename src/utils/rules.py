import os
import re
import math
import json
import nltk 
import joblib
import pandas as pd
from nltk import pos_tag
from pathlib import Path
from rake_nltk import Rake
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from collections import defaultdict
from nltk.corpus import wordnet as wn
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from src.utils.GenHTMLOutput import generate_HTML
from sklearn.feature_extraction.text import TfidfVectorizer

class rules:
    def __init__(self, 
                 JSON_DIR,
                 HTML_DIR, 
                 MODEL_NAME,
                 COURSE_NAME,
                 NLTK_CORPUS_NAME="Corpus.csv",
                 OBJ_CORPUS_NAME="Objective_corpus.json",
                 TIME_CORPUS_NAME="Time_corpus.json"
                 ):
        self.data = None
        self.tokenizer_eval = None
        self.analyzed_pages = []
        self.JSON_DIR = JSON_DIR
        self.HTML_DIR = HTML_DIR
        self.RESULTS = {}
        self.course_name = COURSE_NAME
        
        # data = DATA
        self.tag_map = defaultdict(lambda : wn.NOUN)
        self.tag_map['J'] = wn.ADJ
        self.tag_map['V'] = wn.VERB
        self.tag_map['R'] = wn.ADV
        self.word_Lemmatized = WordNetLemmatizer()

        self.base_dir = Path(__file__).parents[2]
        self.corpus_path = os.path.join(self.base_dir, "corpus", NLTK_CORPUS_NAME)
        self.model_path = os.path.join(self.base_dir, "model", MODEL_NAME)
        self.corpus_path_obj = os.path.join(self.base_dir, "corpus", OBJ_CORPUS_NAME)
        self.corpus_path_time = os.path.join(self.base_dir, "corpus", TIME_CORPUS_NAME)
        
        self.obj_corpus = json.load(open(self.corpus_path_obj))["objectives"]
        self.obj_corpus = [x. lower() for x in self.obj_corpus]
        self.time_corpus = json.load(open(self.corpus_path_time))["time_mentions"]
        self.time_corpus = [x. lower() for x in self.time_corpus]
                
        self.Corpus = pd.read_csv(self.corpus_path)
        self.model_eval = joblib.load(self.model_path)
        self.Tfidf_vect = TfidfVectorizer(max_features=5000)

    ###################################################
    ########### Helper functions for Rule 1 ###########
    ###################################################

    def prediction(self, text):
        text = str(text).lower()
        text = word_tokenize(text)

        Final_words = []
        for word, tag in pos_tag(text):
            if word not in stopwords.words('english') and word.isalpha():
                    word_Final = self.word_Lemmatized.lemmatize(word, self.tag_map[tag[0]])
                    Final_words.append(word_Final)

        temp = ""
        Final_sent = []
        for word in Final_words:
            temp = temp + word + " "
        temp = temp.strip()
        Final_sent.append(temp)


        self.Tfidf_vect.fit(self.Corpus['text_final'])
        text_test_Tfidf = self.Tfidf_vect.transform(Final_sent)

        pred = self.model_eval.predict(text_test_Tfidf)
        return pred
    
    def make_classifications(self, result_page_name, lines, links, key):
        violation_idx = -1
        instruction_count = 0
        instruction_sents = None
        islink = False
        for sentence in lines:
            if len(sentence.strip()) > 1:
                pred = self.prediction(sentence)[0]
                if pred == 1:
                    instruction_count = instruction_count + 1
                    instruction_sents = sentence
                
        if instruction_count == 1:
            if key in links.keys():
                if 0 in links[key]:
                    islink = True
            if islink == False:
                for idx, sentence in enumerate(lines):
                    if len(sentence.strip()) > 1 and sentence == instruction_sents:
                        violation_idx = idx
                print(f"Rule 1 violation. ==> {instruction_sents}")
                self.RESULTS[result_page_name]["rule1"] = True
            else: 
               violation_idx = 1 
        return violation_idx
    
    def analyze_para_and_li(self, result_page_name, para_data, li_data, links):
        para_violation_idx = -1
        li_violation_idx = -1
        violations = []
        islink = False

        if bool(para_data):
            for para_key, para_value in para_data.items():
                para_lines = para_value.split(".")

                if len(para_lines) <= 1 and len(para_lines[0].strip()) > 1:
                    pred = self.prediction(para_lines[0])[0]
                    if pred == 1:
                        if para_key in links.keys():
                            if 0 in links[para_key]:
                                islink = True

                        if islink == False:        
                            print(f"Rule 1 violation. ==> {para_lines[0]}")
                            violations.append({"type": "para", "para_key":para_key, "line_num":0})
                            self.RESULTS[result_page_name]["rule1"] = True

                else:
                    para_violation_idx = self.make_classifications(result_page_name, para_lines, links, para_key)
                    if para_violation_idx != -1:
                    #     if para_key in links.keys():
                    #         if 0 in links[para_key]:
                    #             islink = True
                    #     if islink == False: 
                        violations.append({"type": "para", "para_key":para_key, "line_num":para_violation_idx})
        islink = False
        if bool(li_data):
            for list_type_idx, li_lines in li_data.items():
                if len(li_lines) <= 1 and len(li_lines[0].strip()) > 1:
                    pred = self.prediction(li_lines[0])[0]
                    if pred == 1:
                        if list_type_idx in links.keys():
                            if 0 in links[list_type_idx]:
                                islink = True
                        if islink == False: 
                            print(f"Rule 1 violation. ==> {li_lines[0]}")
                            violations.append({"type": "li", "list_idx":list_type_idx, "line_num":0})
                            self.RESULTS[result_page_name]["rule1"] = True

                else:
                    li_violation_idx = self.make_classifications(result_page_name, li_lines, links, list_type_idx)
                    if li_violation_idx != -1:
                        violations.append({"type": "li", "list_idx":list_type_idx, "line_num":li_violation_idx})
                    #     if list_type_idx in links.keys():
                    #         if 0 in links[list_type_idx]:
                    #             islink = True
                    #     if islink == False: 
                    # violations.append({"type": "li", "list_idx":list_type_idx, "line_num":li_violation_idx})
        
        return violations
    
    def analyze_modules(self, page_path, page_list):
        all_page_violations = {}

        for page_name in page_list:
            result_page_name = page_name.replace(".json", "")
            all_violations = {}
            violations_content = {}
            violations_pre_h2 = []
            preh2_links = {}
            content_links = {}


            print("*"*20)
            print(page_name.replace(".json", ""))
            print("*"*20)

            if page_name in self.analyzed_pages:
                continue

            self.analyzed_pages.append(page_name)

            data = json.load(open(os.path.join(page_path, page_name)))
            content = data['content']
            pre_h2_content = data['__pre_h2__']
            if "preh2_links" in data.keys():
                preh2_links = data["preh2_links"]
            if "content_links" in data.keys():
                content_links = data["content_links"]

            if bool(content):
                for heading, values in content.items():
                    para_data = values['para_sentences']
                    li_data = values['li_sentences']
                    temp_violations = self.analyze_para_and_li(result_page_name, para_data, li_data, content_links)
                    if bool(temp_violations):
                        violations_content[heading] = temp_violations
            all_violations["content"] = violations_content
            
            if bool(pre_h2_content):
                pre_h2_para_data = pre_h2_content['pre_h2_para_sentences']
                pre_h2_li_data = pre_h2_content['pre_h2_li_sentences']
                temp_violations = self.analyze_para_and_li(result_page_name, pre_h2_para_data, pre_h2_li_data, preh2_links)
                if len(temp_violations) > 0:
                    violations_pre_h2 = temp_violations
            
            all_violations["__pre_h2__"] = violations_pre_h2
            all_page_violations[page_name] = all_violations
        return all_page_violations

    ###################################################
    ########### Helper functions for Rule 2 ###########
    ################################################### 
    def get_all_words(self, data):
        content = data['content']
        pre_h2_content = data['__pre_h2__']
        all_texts = []

        if bool(content):
                for heading, values in content.items():
                    para_data = values['para_sentences']
                    li_data = values['li_sentences']


                    if bool(para_data):
                        for para in para_data.values():
                            para = re.sub('[^A-Za-z0-9.]+', ' ', para)
                            all_texts.append(para)

                    if bool(li_data):
                        for li in li_data.values():
                            text = ""
                            for item in li:
                                item = re.sub('[^A-Za-z0-9.]+', ' ', item)
                                text = text + " " + item
                            all_texts.append(text)

        if bool(pre_h2_content):
            pre_h2_para_data = pre_h2_content['pre_h2_para_sentences']
            pre_h2_li_data = pre_h2_content['pre_h2_li_sentences']

            if bool(pre_h2_para_data):
                for para in pre_h2_para_data.values():
                    para = re.sub('[^A-Za-z0-9]+', ' ', para)
                    all_texts.extend(para.split(" "))

            if bool(pre_h2_li_data):
                for li in pre_h2_li_data.values():
                    text = ""
                    for item in li:
                        item = re.sub('[^A-Za-z0-9]+', ' ', item)
                        text = text + " " + item

                    all_texts.extend(text.split(" "))
        
        temp = []
        for text in all_texts:
            temp.extend(text.split(" "))
        all_texts = temp
        return all_texts

    def check_future_need(self, idx, modules, asg_name, asg_path):
        future_need_present = False
        curr_page_keywords = self.get_pages_keywords([asg_name], asg_path)[asg_name]
        for i in range(idx+1, len(modules)):
            all_keywords_next = []
            all_page_keywords_next = {}
            all_asg_keywords_next = {}
            module_name = modules[i]

            asg_path_next = os.path.join(self.JSON_DIR, module_name, "Assignments")
            page_path_next = os.path.join(self.JSON_DIR, module_name, "Pages")
            asg_list_next = os.listdir(asg_path_next)
            page_list_next = os.listdir(page_path_next)
            
            if len(page_list_next) > 0:
                all_page_keywords_next = self.get_pages_keywords(page_list_next, page_path_next)
            if len(asg_list_next) > 0:
                all_asg_keywords_next = self.get_pages_keywords(asg_list_next, asg_path_next)

            if bool(all_page_keywords_next):
                temp_keywords = []
                for keywords in all_page_keywords_next.values():
                    temp_keywords.extend(keywords)
                all_keywords_next.extend(temp_keywords)

            if bool(all_asg_keywords_next):
                temp_keywords = []
                for keywords in all_asg_keywords_next.values():
                    temp_keywords.extend(keywords)
                all_keywords_next.extend(temp_keywords)                    

            count = 0
            for keyword in curr_page_keywords:
                if keyword in all_keywords_next:
                    count = count + 1

            keyword_match_fraction = 0.5         
            num_req_matches = math.floor(len(curr_page_keywords) * keyword_match_fraction)
            if count >= num_req_matches:
                future_need_present = True
        return future_need_present
    
    def get_time_keyword_present(self, data):
        time_keyword_present = False
        all_texts = self.get_all_words(data)
        for time_keyword in self.time_corpus:
            if time_keyword in all_texts:
                time_keyword_present = True
                break
        return time_keyword_present
    
    def get_learning_outcome_present(self, data):
        learning_outcome_present =False
        all_texts = self.get_all_words(data)
        for obj_keyword in self.obj_corpus:
            if obj_keyword in all_texts:
                learning_outcome_present = True
                break
        return learning_outcome_present
    
    def check_cost_value_basis(self, idx, page_list, page_path, modules):
        for page_name in page_list:
            result_page_name = page_name.replace(".json", "")
            if page_name in self.analyzed_pages:
                continue
            self.analyzed_pages.append(page_name)
            
            points = None
            due_date = None
            cost_basis = False
            value_basis = False
            time_keyword_present = False
            learning_outcome_present = False
            future_need_present = False
            data = json.load(open(os.path.join(page_path, page_name)))

            asg_overview = {}
            if "__asg_overview__" in list(data.keys()):
                asg_overview = data["__asg_overview__"]
            
                if bool(asg_overview):
                    keys = list(asg_overview.keys())

                    if "Points" in keys:
                        points = int(asg_overview["Points"])
                    if "Due" in keys:
                        due_date = asg_overview["Due"]
                    
                    if points != None and points > 0:
                        print(f"{page_name} ==> Rule 2 not violated.")
                        self.RESULTS[result_page_name]["rule2"] = False
                        continue
                
            # COST BASIS
            time_keyword_present = self.get_time_keyword_present(data)
            if due_date != None or time_keyword_present == True:
                cost_basis = True
            
            # VALUE BASIS
            learning_outcome_present = self.get_learning_outcome_present(data)
            if idx <= len(modules) - 2:
                future_need_present = self.check_future_need(idx, modules, page_name, page_path)

            if learning_outcome_present == True or future_need_present == True:
                value_basis = True

            # FINAL CONDITION
            if value_basis == True or cost_basis == True:
                print(f"{page_name} ==> Rule 2 not violated.")
                self.RESULTS[result_page_name]["rule2"] = False
            else:
                print(f"{page_name} ==> Rule 2 violated.")
                self.RESULTS[result_page_name]["rule2"] = True

    ###################################################
    ########### Helper functions for Rule 3 ###########
    ###################################################

    def get_module_names(self):
        # parent_dir = Path(__file__).parents[2]
        # json_dir = os.path.join(parent_dir, "HTML_extracted_lines")

        list_to_remove = ["HomePageData.json", "violations.json"]
        modules = os.listdir(self.JSON_DIR)
        modules = list(set(modules) - set(list_to_remove))

        temp_folders = []
        for module in modules:
            temp_folders.append((int(module[module.index("_")+1:]), module))
        temp_folders = sorted(temp_folders)

        modules = []
        for temp in temp_folders:
            modules.append(temp[1])

        return modules
    
    def letters(self, input):
        return ''.join(filter(str.isalpha, input))
    
    def get_keywords(self, text, word_count=10):
        sentences = text.split(".")
        out_keywords = []
        for sentence in sentences:
            stop_words = set(stopwords.words('english'))
            word_tokens = word_tokenize(sentence)
            filtered_sentence = [w for w in word_tokens if not w.lower() in stop_words]
            filtered_sentence = ""

            for w in word_tokens:
                if w not in stop_words:
                    filtered_sentence = filtered_sentence + " " + w

            rake = Rake()
            rake.extract_keywords_from_text(filtered_sentence)
            keywords = rake.get_ranked_phrases_with_scores()

            temp = []
            for score, keyword in keywords:
                    temp.append(keyword)
            keywords = temp[:word_count]
            # out_keywords.extend(temp[:word_count])
            # nlp = spacy.load("en_core_web_sm")
            # doc = nlp(sentence)
            # spacy_nouns = [token.lemma_ for token in doc if token.pos_ == "NOUN"]
            # out_keywords.extend(spacy_nouns[:word_count])

        return out_keywords
    
    def get_all_keywords(self, page_list, page_path):
        all_pages_keywords = {}
        for page_name in page_list:
            # temp_data = []
            data = json.load(open(os.path.join(page_path, page_name)))
            content = data['content']
            pre_h2_content = data['__pre_h2__']
            page_keywords = []
            all_texts = []
            all_texts_keywords = []

            if bool(content):
                for heading, values in content.items():
                    para_data = values['para_sentences']
                    li_data = values['li_sentences']


                    if bool(para_data):
                        for para in para_data.values():
                            para = re.sub('[^A-Za-z0-9.]+', ' ', para)
                            all_texts.append(para)
                            keywords = self.get_keywords(para, word_count=3)
                            page_keywords.extend(keywords)

                    if bool(li_data):
                        for li in li_data.values():
                            text = ""
                            for item in li:
                                item = re.sub('[^A-Za-z0-9.]+', ' ', item)
                                text = text + " " + item

                            all_texts.append(text)
                            keywords = self.get_keywords(text, word_count=3)
                            page_keywords.extend(keywords)

            if bool(pre_h2_content):
                pre_h2_para_data = pre_h2_content['pre_h2_para_sentences']
                pre_h2_li_data = pre_h2_content['pre_h2_li_sentences']

                if bool(pre_h2_para_data):
                    for para in pre_h2_para_data.values():
                        para = re.sub('[^A-Za-z0-9.]+', ' ', para)
                        all_texts.append(para)
                        keywords = self.get_keywords(para, word_count=3)
                        page_keywords.extend(keywords)

                if bool(pre_h2_li_data):
                    for li in pre_h2_li_data.values():
                        text = ""
                        for item in li:
                            item = re.sub('[^A-Za-z0-9.]+', ' ', item)
                            text = text + " " + item

                        all_texts.append(text)
                        keywords = self.get_keywords(text, word_count=3)
                        page_keywords.extend(keywords)   

            # print(all_texts)
            for text in all_texts:
                keywords = self.get_keywords(text, word_count=3)
                all_texts_keywords.extend(keywords)

            all_pages_keywords[page_name] = {
                                                "page_keywords": page_keywords,
                                                "all_texts_keywords": all_texts_keywords
                                            }
        return all_pages_keywords

    def nounExtractor(self, text):
        noun = []
        sentences = nltk.sent_tokenize(text)
        for sentence in sentences:
            words = nltk.word_tokenize(sentence)
            words = [word for word in words if word not in set(stopwords.words('english'))]
            tagged = nltk.pos_tag(words)
            for (word, tag) in tagged:
                if tag == 'NN':
                    noun.append(word)
            
        return noun
    
    def get_pages_keywords(self, page_list, page_path):
        all_pages_keywords = self.get_all_keywords(page_list, page_path)
        page_keywords_nouns = []
        all_texts_keywords_nouns = []
        all_keywords = {}

        for page_name, keywords in all_pages_keywords.items():
            page_keywords = keywords["page_keywords"]
            all_texts_keywords = keywords["all_texts_keywords"]

            for page_keyword in page_keywords:
                nouns = self.nounExtractor(page_keyword)
                page_keywords_nouns.extend(nouns)

            for all_texts_keyword in all_texts_keywords:
                nouns = self.nounExtractor(all_texts_keyword)
                all_texts_keywords_nouns.extend(nouns)
            
            page_keywords_nouns = [*set(page_keywords_nouns)]
            all_texts_keywords_nouns = [*set(all_texts_keywords_nouns)]

            intersec_keywords = list(set(page_keywords_nouns).intersection(all_texts_keywords_nouns))
            all_keywords[page_name] = intersec_keywords

        return all_keywords
    
    def check_keyword_match(self, page_list, asg_list, page_path, asg_path, keyword_match_fraction = 1.0):
        all_page_keywords = self.get_pages_keywords(page_list, page_path) 
        all_asg_keywords = self.get_pages_keywords(asg_list, asg_path)

        temp_keywords = []
        for keywords in all_page_keywords.values():
            temp_keywords.extend(keywords)
        all_page_keywords = temp_keywords

        for asg_name, asg_keywords in all_asg_keywords.items():
            result_asg_name = asg_name.replace(".json", "")
            matched_keywords = []
            count = 0
            for keyword in asg_keywords:
                if keyword in all_page_keywords:
                    matched_keywords.append(keyword)
                    count = count + 1
            
            num_req_matches = math.floor(len(asg_keywords) * keyword_match_fraction)

            if count >= num_req_matches:
                print(f"{asg_name} ==> Rule 3 not violated ; Keyword len ==> {len(asg_keywords)}; Count ==> {count}")
                self.RESULTS[result_asg_name]['rule3'] = False
            else:
                print(f"{asg_name} ==> Rule 3 violated ; Keyword len ==> {len(asg_keywords)}; Count ==> {count}")
                self.RESULTS[result_asg_name]['rule3'] = True

            self.RESULTS[result_asg_name]['keywords'] = all_page_keywords
            print(f"Matched Keywords: {matched_keywords}")

    ###################################################
    ########### Helper functions for Rule 4 ###########
    ###################################################
    def check_link_title(self, html_dir, name):
        with open(os.path.join(html_dir, name), "r", encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')

        if len(soup.findAll('a')) != len(soup.find_all('a', attrs={'title': True})):
            print(f"{name} ==> Rule 4 violated")
            self.RESULTS[name]['rule4'] = True 

    ########################################
    ########### Driver functions ###########
    ########################################
    def check_rule_1(self):
        modules = self.get_module_names()
        self.analyzed_pages = []
        all_module_violations = {}
        for module in modules:
            print("*"*20)
            print(module)
            print("*"*20)
            asg_path = os.path.join(self.JSON_DIR, module, "Assignments")
            page_path = os.path.join(self.JSON_DIR, module, "Pages")
            asg_list = os.listdir(asg_path)
            page_list = os.listdir(page_path)
            
            all_page_violations = self.analyze_modules(page_path, page_list)
            all_asg_violations = self.analyze_modules(asg_path, asg_list)

            all_module_violations[module] = {
                "Pages": all_page_violations,
                "Assignments": all_asg_violations
            }
        
        json.dump(all_module_violations, 
                  open(os.path.join(self.JSON_DIR, "violations.json"), "w"))
        
        HTML_gen_dir = os.path.join(self.base_dir, "static", "OUT_HTML")
        isExist = os.path.exists(HTML_gen_dir)
        if not isExist:
            os.mkdir(HTML_gen_dir)
        for module in modules:
            module_dir = os.path.join(HTML_gen_dir, module)
            isExist = os.path.exists(module_dir)
            if not isExist:
                os.mkdir(module_dir)
        
        generate_HTML(self.course_name)
    
    def check_rule_2(self):
        modules = self.get_module_names()
        self.analyzed_pages = []
        for idx, module in enumerate(modules):
            print("*"*20)
            print(module)
            print("*"*20)

            asg_path = os.path.join(self.JSON_DIR, module, "Assignments")
            page_path = os.path.join(self.JSON_DIR, module, "Pages")
            asg_list = os.listdir(asg_path)
            page_list = os.listdir(page_path)

            
            if len(page_list) > 0:
                self.check_cost_value_basis(idx, page_list, page_path, modules)
            
            if len(asg_list) > 0:
                self.check_cost_value_basis(idx, asg_list, asg_path, modules)

    def check_rule_3(self):
        modules = self.get_module_names()
        self.analyzed_pages = []
        for module in modules:
            print("*"*20)
            print(module)
            print("*"*20)

            asg_path = os.path.join(self.JSON_DIR, module, "Assignments")
            page_path = os.path.join(self.JSON_DIR, module, "Pages")
            asg_list = os.listdir(asg_path)
            page_list = os.listdir(page_path)

            if len(asg_list) == 0:
                continue

            self.check_keyword_match(page_list, 
                                     asg_list, 
                                     page_path, 
                                     asg_path, 
                                     keyword_match_fraction = 1.0)
    def check_rule_4(self):
        modules = self.get_module_names()
        self.analyzed_pages = []
        for module in modules:
            print("*"*20)
            print(module)
            print("*"*20)

            asg_path = os.path.join(self.HTML_DIR, module, "Assignments")
            page_path = os.path.join(self.HTML_DIR, module, "Pages")
            asg_list = os.listdir(asg_path)
            page_list = os.listdir(page_path)

            for asg in asg_list:
                self.check_link_title(asg_path, asg)
            
            for page in page_list:
                self.check_link_title(page_path, page)

    def check_all_rules(self):
        modules = self.get_module_names()
        print(modules)
        for module in modules:
            asg_path = os.path.join(self.JSON_DIR, module, "Assignments")
            page_path = os.path.join(self.JSON_DIR, module, "Pages")
            asg_list = os.listdir(asg_path)
            page_list = os.listdir(page_path)

            if len(asg_list) > 0:
                for asg_name in asg_list:
                    asg_name = asg_name.replace(".json", "")
                    self.RESULTS[asg_name] = {"rule1":False, "rule2":False, "rule3":False, "rule4":False}

            if len(page_list) > 0:
                for page_name in page_list:
                    page_name = page_name.replace(".json", "")
                    self.RESULTS[page_name] = {"rule1":False, "rule2":False, "rule3":False, "rule4":False}

        self.check_rule_1()
        self.check_rule_2()
        self.check_rule_3()
        self.check_rule_4()

        temp_dict = {}
        for key, data in self.RESULTS.items():
            if data["rule1"] == False and data["rule2"] == False and data["rule3"] == False and data["rule4"] == False:
                continue
            else:
                temp_dict[key] = data

        self.RESULTS = temp_dict