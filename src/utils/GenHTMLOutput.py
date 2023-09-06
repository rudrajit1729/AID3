import os
import bs4
import json
from pathlib import Path

# Create all the dirs
def create_dir(all_violations, out_dir):
    for dir in list(all_violations.keys()):
        path = os.path.join(out_dir, dir)
        isExists = os.path.exists(path)
        if not isExists:
            os.makedirs(path)

def generate_HTML_output(page_type, page_violations, html_dir, module_name, body_html_dict, out_dir, violations_json, course_name):
    if bool(page_violations):
        for page_name, violation in page_violations.items():
            violation_count = 0
            content_violations = violation["content"]
            pre_h2_violations = violation["__pre_h2__"]

            # if bool(content_violations):
            #     for key, val in content_violations.items():
            #         violation_count = violation_count + len(content_violations[key])
            
            # violation_count = violation_count + len(pre_h2_violations)
            # if page_name == "Module10_Pages26.html.json":
            #     print(violation_count)
                

            page_name = page_name.replace(".json", "") 
            dir = os.path.join(html_dir, module_name, page_type, page_name)
            with open(dir, "r", encoding="utf-8") as f:
                page_html = f.read()
            soup = bs4.BeautifulSoup(page_html, features="html.parser")
            
            soup_data = soup.find(id="content")
            body_html = soup_data.find('div', body_html_dict).find("div")
            if not body_html:
                body_html = soup_data.find('div', body_html_dict)
            
            if bool(content_violations):
                all_headings = list(content_violations.keys())
                for heading in body_html.find_all("h2"):
                    if heading.text in all_headings:
                        for violation_coords in content_violations[heading.text]:
                            para_idx = 0
                            ol_idx = 0
                            ul_idx = 0
                            for sibling in heading.find_next_siblings():
                                if sibling.name == "h2":
                                    break
                                
                                if violation_coords["type"] == "para":
                                    if sibling.name == "p":
                                        para_key = int(violation_coords["para_key"].split("_")[1])
                                        line_num = violation_coords["line_num"]
                                        if para_idx == para_key:
                                            para_text = sibling.text.split(".")
                                            # para_text = str(sibling).split(".")
                                            new_text = "<p>"
                                            for idx, text in enumerate(para_text):
                                                if idx == line_num and len(text) >10:
                                                    new_text = new_text + "<span style=\"background-color:yellow;\">" + text + "</span>"
                                                    violation_count = violation_count + 1
                                                else:
                                                    new_text = new_text + text + "."
                                            new_text = new_text + "</p>"
                                            new_soup = bs4.BeautifulSoup(new_text, features="html.parser")
                                            sibling.replace_with(new_soup.p)
                                        para_idx = para_idx + 1
                                
                                if violation_coords["type"] == "li":
                                    li_type = violation_coords["list_idx"].split("_")[0]
                                    li_key = int(violation_coords["list_idx"].split("_")[1])
                                    if sibling.name == "ul" and li_type == "ul":
                                        if ul_idx == li_key:
                                            line_num = violation_coords["line_num"]
                                            violation_li = sibling.findAll("li")[line_num]

                                            text = violation_li.text
                                            # text = str(violation_li)
                                            new_text = "<li>"
                                            new_text = new_text + "<span style=\"background-color:yellow;\">" + text + "</span>" + "</li>"
                                            violation_count = violation_count + 1
                                            new_soup = bs4.BeautifulSoup(new_text, features="html.parser")
                                            violation_li.replace_with(new_soup.li)
                                        ul_idx = ul_idx + 1

                                    if sibling.name == "ol" and li_type == "ol":
                                        li_key = int(violation_coords["list_idx"].split("_")[1])
                                        if ol_idx == li_key:
                                            line_num = violation_coords["line_num"]
                                            violation_li = sibling.findAll("li")[line_num]

                                            text = violation_li.text
                                            # text = str(violation_li)
                                            new_text = "<li>"
                                            new_text = new_text + "<span style=\"background-color:yellow;\">" + text + "</span>" + "</li>"
                                            violation_count = violation_count + 1

                                            new_soup = bs4.BeautifulSoup(new_text, features="html.parser")
                                            violation_li.replace_with(new_soup.li)
                                        ol_idx = ol_idx + 1
                
            if len(pre_h2_violations) > 0:
                for pre_h2_violation in pre_h2_violations:
                    pre_h2_para_idx = 0
                    if pre_h2_violation["type"] == "para":
                        para_key = int(pre_h2_violation["para_key"].split("_")[1])
                        line_num = pre_h2_violation["line_num"]

                        for anchor_point in body_html.findChildren():
                            if anchor_point.name == "h2":
                                break

                            if anchor_point.name == "p":
                                if pre_h2_para_idx == para_key:
                                    para_text = anchor_point.text.split(".")
                                    # para_text = str(anchor_point).split(".")
                                    new_text = "<p>"
                                    for idx, text in enumerate(para_text):
                                        if idx == line_num and len(text) > 10:
                                            new_text = new_text + "<span style=\"background-color:yellow;\">" + text + "</span>"
                                            violation_count = violation_count + 1
                                        else:
                                            new_text = new_text + text + "."
                                    new_soup = bs4.BeautifulSoup(new_text, features="html.parser")
                                    anchor_point.replace_with(new_soup.p)

                                pre_h2_para_idx = pre_h2_para_idx + 1
            
            if page_name in list(violations_json.keys()):
                violations_json[page_name]["rule1_violation_count"] = violation_count
            
            with open(os.path.join(out_dir, module_name, f"{page_name}"), "w", encoding="utf-8") as file:
                file.write(str(soup))
        
        parent_dir = Path(__file__).parents[2]
        out_file_path = os.path.join(parent_dir, 'static', course_name)
        json.dump(violations_json, open(os.path.join(out_file_path, "AllViolations.json"), "w"))

def generate_HTML(course_name):
    parent_dir = Path(__file__).parents[2]
    json_dir = os.path.join(parent_dir, "static", course_name)
    html_dir = os.path.join(parent_dir, "static", "HTML_DATA", course_name)

    html_static_dir = Path(__file__).parents[2]
    out_dir = os.path.join(html_static_dir, "static", "OUT_HTML")

    body_html_dict = {"class": "show-content"}
    violations_json = json.load(open(os.path.join(json_dir, "violations.json")))
    all_violations = json.load(open(os.path.join(json_dir, "AllViolations.json")))

    create_dir(violations_json, out_dir)

    for module_name, module_violations in violations_json.items():
        page_type = "Pages"
        body_html_dict = {"class": "show-content"}
        page_violations = module_violations[page_type]
        generate_HTML_output(page_type,
                             page_violations, 
                             html_dir, 
                             module_name, 
                             body_html_dict, 
                             out_dir,
                             all_violations,
                             course_name)
        
        page_type = "Assignments"
        body_html_dict = {'class': 'description'}
        asg_violations = module_violations[page_type]
        generate_HTML_output(page_type,
                             asg_violations, 
                             html_dir, 
                             module_name, 
                             body_html_dict, 
                             out_dir,
                             all_violations,
                             course_name)