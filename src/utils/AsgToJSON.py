import os
import json
from bs4 import BeautifulSoup 

def assignment_to_json(file_path, out_file_path, out_file_name):
    parser = "html.parser"
    page_content_id = "content"
    body_html_dict = {'class': 'description'}
    asg_ovr_html_dict = {"class": "student-assignment-overview"}

    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, parser)
    soup = soup.find(id=page_content_id)


    pre_h2_para_idx = 0
    pre_h2_ol_idx = 0
    pre_h2_ul_idx = 0
    pre_h2_para_sentences = {}
    pre_h2_li_sentences = {}
    preh2_links = {}
    line_num = []

    heading_sentences = soup.find("h1")
    try:
        body_html = soup.find('div', body_html_dict).find("div")
    except AttributeError:
         return
    
    if not body_html:
        body_html = soup.find('div', body_html_dict)

    for anchor_point in body_html.findChildren():
        if anchor_point.name == "h2":
            break

        if anchor_point.name == "p":
            for line_num, line in enumerate(anchor_point):
                if line.find("a") != -1:
                    if f"para_{pre_h2_para_idx}" not in preh2_links.keys():
                        preh2_links[f"para_{pre_h2_para_idx}"] = [line_num] 
                    else:
                        preh2_links[f"para_{pre_h2_para_idx}"].extend(line_num)

            pre_h2_para_sentences[f"para_{pre_h2_para_idx}"] = anchor_point.text
            pre_h2_para_idx = pre_h2_para_idx + 1

        if anchor_point.name == "ul":
            texts_li = anchor_point.findAll('li')
            temp_li = []
            line_num = []
            for idx, line in enumerate(anchor_point):
                if line.find("a") != -1:
                        line_num.append(idx)

            if f"ul_{pre_h2_ul_idx}" not in preh2_links.keys():
                preh2_links[f"ul_{pre_h2_ul_idx}"] = [line_num]
            else:
                preh2_links[f"ul_{pre_h2_ul_idx}"].extend(line_num)

            for text_li in texts_li:
                temp_li.append(text_li.get_text().strip().replace('\n', ' ').replace(",", " ").split(".")[0])

            pre_h2_li_sentences[f"ul_{pre_h2_ul_idx}"] = temp_li
            pre_h2_ul_idx = pre_h2_ul_idx + 1

        if anchor_point.name == "ol":
            texts_li = anchor_point.findAll('li')
            temp_li = []
            line_num = []
            for idx, line in enumerate(anchor_point):
                if line.find("a") != -1:
                        line_num.append(idx)

            if f"ul_{pre_h2_ul_idx}" not in preh2_links.keys():
                preh2_links[f"ul_{pre_h2_ul_idx}"] = [line_num]
            else:
                preh2_links[f"ul_{pre_h2_ul_idx}"].extend(line_num)

            for text_li in texts_li:
                temp_li.append(text_li.get_text().strip().replace('\n', ' ').replace(",", " ").split(".")[0])

            pre_h2_li_sentences[f"ol_{pre_h2_ol_idx}"] = temp_li
            pre_h2_ol_idx = pre_h2_ol_idx + 1

    heading_sentences = heading_sentences.get_text().strip().replace('\n', ' ').replace(",", " ").split(".")

    span_item = {}
    content = {}
    blocks = {}
    content_links = {}
    line_num = []

    if body_html:
        for heading in body_html.find_all("h2"):
            para_idx = 0
            ol_idx = 0
            ul_idx = 0
            para_sentences = {}
            li_sentences = {}

            for sibling in heading.find_next_siblings():
                if sibling.name == "h2":
                    break

                if sibling.name == "p":
                    for line_num, line in enumerate(anchor_point):
                        if line.find("a") != -1:
                            if f"para_{para_idx}" not in content_links.keys():
                                content_links[f"para_{para_idx}"] = [line_num]
                            else:
                                content_links[f"para_{para_idx}"].append(line_num)
                    para_sentences[f"para_{para_idx}"] = sibling.text
                    para_idx = para_idx + 1

                if sibling.name == "ul":
                    texts_li = sibling.findAll('li')
                    temp_li = []
                    line_num = []

                    for idx, line in enumerate(anchor_point):
                        if line.find("a") != -1:
                                line_num.append(idx)
                    
                    if f"ul_{ul_idx}" not in content_links.keys():
                                content_links[f"ul_{ul_idx}"] = [line_num]
                    else:
                        content_links[f"ul_{ul_idx}"].extend(line_num)

                    for text_li in texts_li:
                        temp_li.append(text_li.get_text().strip().replace('\n', ' ').replace(",", " ").split(".")[0])

                    li_sentences[f"ul_{ul_idx}"] = temp_li
                    ul_idx = ul_idx + 1

                if sibling.name == "ol":
                    texts_li = sibling.findAll('li')
                    temp_li = []
                    line_num = []
                    for idx, line in enumerate(anchor_point):
                        if line.find("a") != -1:
                                line_num = idx

                    if f"ol_{ol_idx}" not in content_links.keys():
                                content_links[f"ol_{ol_idx}"] = [line_num]
                    else:
                        content_links[f"ol_{ol_idx}"].append(line_num)
                    for text_li in texts_li:
                        temp_li.append(text_li.get_text().strip().replace('\n', ' ').replace(",", " ").split(".")[0])

                    li_sentences[f"ol_{ol_idx}"] = temp_li
                    ol_idx = ol_idx + 1
    
            # Parsing HTML to check for items in rule 2
            ul_asg_overview = soup.find('ul', asg_ovr_html_dict)
            if ul_asg_overview:
                overview_items = ul_asg_overview.findAll('li')
                
                for item in overview_items:
                        items = item.findAll('span')
                        span_item[items[0].get_text().strip()] = items[1].get_text().strip()
            
            content[heading.text] = {"para_sentences": para_sentences,
                                    "li_sentences": li_sentences,
                                    }

    blocks = {
        "content": content,
        "heading_sentences": heading_sentences,
        "__pre_h2__": {
                            "pre_h2_para_sentences": pre_h2_para_sentences,
                            "pre_h2_li_sentences": pre_h2_li_sentences
                            },
        "__asg_overview__": span_item
    }
    json.dump(blocks, open(os.path.join(out_file_path, f"{out_file_name}.json"), "w"))

if __name__ == "__main__":
    assignment_to_json('../../HTML_DATA/Module_2/Assignments/Module2_Asg0.html', 
                       "../../HTML_extracted_lines",
                       "asg_test_json") #Add Pages html paths here
