import os
from bs4 import BeautifulSoup

def get_links_from_modules_page(file_path, base_url = "https://canvas.oregonstate.edu"):
    file_open_mode = "r"
    encoding = "utf-8"
    bs_parser = "html.parser"
    li_title_name_mods = "Page"
    li_title_name_dsc = "Discussion topic"
    # li_title_name_quiz = "Quiz"
    # li_title_name_asg = "Assignment"
    page_id_content = "content"
    content_html_dict = {"id": "context_modules"}
    modules_html_dict = {"class": "content"}

    with open(file_path, file_open_mode, encoding=encoding) as f:
        html = f.read()

    soup = BeautifulSoup(html, bs_parser)
    soup = soup.find(id=page_id_content)

    content_html = soup.find("div", content_html_dict)
    modules_html_list = content_html.findAll("div", modules_html_dict)

    unordered_lists = []
    for module in modules_html_list:
        unordered_lists.append(module.find('ul'))

    links_dict = []
    for unordered_list in unordered_lists:

        pages_links = []
        asg_links = []
        list_items = unordered_list.findAll("li")
        
        for list_item in list_items:
            
            span_title = list_item.find('span')['title']
            if span_title == li_title_name_mods or span_title == li_title_name_dsc:
                page_link = base_url + list_item.find('a')['href']
                pages_links.append(page_link)
            
            else:
            # elif list_item.find('span')['title'] == li_title_name_asg:
                asg_link = base_url + list_item.find('a')['href']
                asg_links.append(asg_link)
        
        links_dict.append({"Pages": pages_links, "Assignments":asg_links})
    
    return links_dict