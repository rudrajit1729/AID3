import os
import json
from pathlib import Path
from src.utils.DownloadWebpages import download_all_webpages
from src.utils.DownloadWebpages import download_all_webpages
from src.utils.PageToJSON import page_to_json
from src.utils.ScrapeAllPages import scrape_all_pages
from src.utils.rules import rules

# # Download all the webpages of the course
def download_webpages(home_url, username, password, base_url = "https://canvas.oregonstate.edu"):
    download_all_webpages(username, password, base_url = base_url, home_page_link = home_url)

# Extract text from the home page and add to a global temp corpus
def scrape_pages(course_name):
    parent_dir = Path(__file__).parents[1]
    home_html_path = os.path.join(parent_dir, "static", "HTML_DATA", course_name, "HomePage.html")
    
    home_html_out_path = os.path.join(parent_dir, "HTML_extracted_lines")
    page_to_json(file_path=home_html_path,
                            out_file_path=home_html_out_path,
                            out_file_name="HomePageData")
    scrape_all_pages(course_name)

# Checking rules
def check_rules(course_name):
    parent_dir = Path(__file__).parents[1]
    base_dir = Path(__file__).parents[1]
    json_dir = os.path.join(parent_dir, "HTML_extracted_lines")

    out_html_dir = os.path.join(parent_dir, "static", "OUT_HTML")
    isExists = os.path.exists(out_html_dir)
    if not isExists:
        os.mkdir(out_html_dir)

    out_folder_path = os.path.join(base_dir, "static", course_name)
    isExists = os.path.exists(out_folder_path)
    if not isExists:
        os.mkdir(out_folder_path)

    ext_json_dir = os.path.join(parent_dir, "HTML_extracted_lines")
    isExists = os.path.exists(ext_json_dir)
    if not isExists:
        os.mkdir(ext_json_dir)

    scrape_pages(course_name)
    rule = rules(JSON_DIR = json_dir,
                COURSE_NAME = course_name,
                MODEL_NAME="svm_model.sav",
                NLTK_CORPUS_NAME="Corpus.csv",
                OBJ_CORPUS_NAME="Objective_corpus.json",
                TIME_CORPUS_NAME="Time_corpus.json")

    rule.check_all_rules()
    json.dump(rule.RESULTS, 
                  open(os.path.join(base_dir, "static", course_name, "AllViolations.json"), "w"))
    # return rule.RESULTS

    # results = json.load(open("./static/AllViolations.json"))
    # return results