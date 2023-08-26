#Command to run: flask --app app.py --debug run

import os
import re
import shutil
import json
from src.app_logic import check_rules
from src.utils.GenHTMLOutput import generate_HTML
from flask import Flask, render_template, request, redirect
from flask_paginate import Pagination, get_page_args


app = Flask(__name__)
app.template_folder = './src/templates'

results_dict = {}
count = 0

def get_all_links_and_results(results, course_name):
    all_pages = list(results.keys())
    html_path = "../static"
    page_render_list = []
    rule_1 = []
    rule_2 = []
    rule_3 = []
    rule_4 = []

    for page_name in all_pages:
        module_name = page_name.split("_")[0]
        module_num = re.sub('[^0-9]+', ' ', module_name).strip()
        page_type = page_name.split("_")[1].replace(".html.json", "")
        page_type = re.sub('[^A-Za-z]+', ' ', page_type).strip().split(" ")[0]
        if results[page_name]['rule1'] == False and results[page_name]['rule2'] == False and results[page_name]['rule3'] == False:
            continue
        if results[page_name]['rule1'] == False:
            if page_type == "Pages":
                page_path = os.path.join(html_path, "HTML_DATA", course_name, f"Module_{module_num}", "Pages", page_name)
            else:
                page_path = os.path.join(html_path, "HTML_DATA", course_name, f"Module_{module_num}", "Assignments", page_name)
        else:
            page_path = os.path.join(html_path, "OUT_HTML", f"Module_{module_num}", page_name)
        page_render_list.append(page_path)

        rule_1.append(results[page_name]['rule1'])
        rule_2.append(results[page_name]['rule2'])
        rule_3.append(results[page_name]['rule3'])
        rule_4.append(results[page_name]['rule4'])

    return page_render_list, rule_1, rule_2, rule_3, rule_4


def pagenate_result(iterable, offset=0, per_page=5):
    return iterable[offset: offset + per_page]

def package_results(links, rule1, rule2, rule3, rule4):
    result = []
    for i in range(len(links)):
        result.append({
            "link": links[i],
            "rule1": rule1[i],
            "rule2": rule2[i],
            "rule3": rule3[i],
            "rule4": rule4[i]
        })
    return result

def package_results_filter(links, rule):
    result = []
    for i in range(len(links)):
        result.append({
            "link": links[i],
            "rule": rule[i],
        })
    return result

@app.route("/")
def home():
    global count
    count = 0
    html_extracted_path = "./HTML_extracted_lines"
    isExists = os.path.exists(html_extracted_path)
    if isExists:
        try:
            shutil.rmtree(html_extracted_path)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))
    
    out_html_path = "./static/OUT_HTML"
    isExists = os.path.exists(out_html_path)
    if isExists:
        try:
            shutil.rmtree(out_html_path)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))

    return render_template("index.html")

# course_name == "CS 161":
@app.route("/results", methods=['GET', 'POST'])
def results():
    course_name = request.form.get("course_name")
    if course_name == "Choose":
        return render_template("index.html")
    
    else:
        return redirect(f"/results/{course_name}")
    

@app.route("/results/<course_name>", methods=['GET', 'POST'])
def course_results(course_name):
    print("COURSE NAME", course_name)
    global count
    global results_dict
    if count == 0:
        # check_rules(course_name)
        generate_HTML(course_name)
        count = count + 1
    
    results_dict = json.load(open(f"./static/{course_name}/AllViolations.json"))
    links, rule1, rule2, rule3, rule4 = get_all_links_and_results(results_dict, course_name)
    page, per_page, offset = get_page_args(page_parameter='page',
                                        per_page_parameter='per_page')
    # per_page = 5
    total = len(links)
    pagination_links = pagenate_result(links, offset=offset, per_page=per_page)
    render_results_rule1 = pagenate_result(rule1, offset=offset, per_page=per_page)
    render_results_rule2 = pagenate_result(rule2, offset=offset, per_page=per_page)
    render_results_rule3 = pagenate_result(rule3, offset=offset, per_page=per_page)
    render_results_rule4 = pagenate_result(rule4, offset=offset, per_page=per_page)

    pkg_results = package_results(pagination_links, 
                                  render_results_rule1, 
                                  render_results_rule2, 
                                  render_results_rule3,
                                  render_results_rule4)

    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap5')
    
    return render_template('results.html',
                        results=pkg_results,
                        page=page,
                        per_page=per_page,
                        pagination=pagination,
                        course_name=course_name,
                        )

@app.route("/results/filter", methods=['GET'])
def course_results_filter():
    course_name = request.args.get("course_name")
    rule_num = request.args.get("rule")
    
    results_dict = json.load(open(f"./static/{course_name}/AllViolations.json"))
    links, rule1, rule2, rule3, rule4 = get_all_links_and_results(results_dict, course_name)
    page, per_page, offset = get_page_args(page_parameter='page',
                                        per_page_parameter='per_page')
    # per_page = 5

    if rule_num == "1":
        render_results = pagenate_result(rule1, offset=offset, per_page=per_page)
        links = [links[i] for i in range(len(rule1)) if rule1[i]]
    elif rule_num == "2":
        render_results = pagenate_result(rule2, offset=offset, per_page=per_page)
        links = [links[i] for i in range(len(rule2)) if rule2[i]]
    elif rule_num == "3":
        render_results = pagenate_result(rule3, offset=offset, per_page=per_page)
        links = [links[i] for i in range(len(rule3)) if rule3[i]]
    else:
        render_results = pagenate_result(rule4, offset=offset, per_page=per_page)
        links = [links[i] for i in range(len(rule4)) if rule4[i]]

    total = len(links)
    pagination_links = pagenate_result(links, offset=offset, per_page=per_page)
    pkg_results = package_results_filter(pagination_links, render_results)

    pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap5')
    
    if total == 0:
        return render_template('no_violations.html',
                        results=pkg_results,
                        page=page,
                        per_page=per_page,
                        pagination=pagination,
                        course_name=course_name,
                        rule_num = rule_num
                        )    
    
    return render_template('results_filtered.html',
                        results=pkg_results,
                        page=page,
                        per_page=per_page,
                        pagination=pagination,
                        course_name=course_name,
                        rule_num = rule_num
                        )

if __name__ == '__main__':
    app.run(debug=True)
