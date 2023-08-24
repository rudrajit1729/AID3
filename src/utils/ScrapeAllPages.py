import os
import shutil
from pathlib import Path
from src.utils.PageToJSON import page_to_json
from src.utils.AsgToJSON import assignment_to_json

def scrape_all_pages(course_name):

    parent_dir = Path(__file__).parents[2]
    html_path = os.path.join(parent_dir, "static", "HTML_DATA", course_name)
    json_path = os.path.join(parent_dir, "HTML_extracted_lines")

    isExists = os.path.exists(json_path)
    if not isExists:
        os.mkdir(json_path)

    list_to_remove = ["HomePage.html", "ModulesPage.html"]
    html_folders = os.listdir(html_path)
    html_folders = list(set(html_folders) - set(list_to_remove))

    temp_folders = []
    for folder in html_folders:
        temp_folders.append((int(folder[folder.index("_")+1:]), folder))
    temp_folders = sorted(temp_folders)

    html_folders = []
    for temp in temp_folders:
        html_folders.append(temp[1])

    for folder in html_folders:
        folder_path = os.path.join(json_path, folder)
        isExists = os.path.exists(folder_path)
        if not isExists:
            os.mkdir(folder_path)
            os.mkdir(os.path.join(folder_path, "Pages"))
            os.mkdir(os.path.join(folder_path, "Assignments"))

    for folder in html_folders:
        asg_path = os.path.join(html_path, folder, "Assignments")
        pages_path = os.path.join(html_path, folder, "Pages")

        asg_files = os.listdir(asg_path)
        pages_files = os.listdir(pages_path)
        
        if len(asg_files) > 0:
            for asg_file in asg_files:
                asg_html_path = os.path.join(asg_path, asg_file)
                asg_out_path = os.path.join(json_path, folder, "Assignments")
                assignment_to_json(file_path=asg_html_path,
                                   out_file_path=asg_out_path,
                                   out_file_name=asg_file)

        if len(pages_files) > 0:
            for pages_file in pages_files:
                pages_html_path = os.path.join(pages_path, pages_file)
                pages_out_path = os.path.join(json_path, folder, "Pages")
                page_to_json(file_path=pages_html_path,
                            out_file_path=pages_out_path,
                            out_file_name=pages_file)
                
        else:
            parent_dir = Path(__file__).parents[2]
            dir = os.path.join(parent_dir, "HTML_extracted_lines")

            prev_folders = html_folders[:html_folders.index(folder)]
            for prev_folder in prev_folders:
                files = os.listdir(os.path.join(dir, prev_folder, "Pages"))
                for file in files:
                    src_json_path = os.path.join(dir, prev_folder, "Pages", file)
                    dist_json_path = os.path.join(dir, folder, "Pages", file)
                    shutil.copy(src_json_path, dist_json_path)