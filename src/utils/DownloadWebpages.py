import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from src.utils.ScrapeModulesPage import get_links_from_modules_page

def login(home_url, username, password):
	driver = webdriver.Chrome()
	driver.get(home_url)
	
	# Find the username and password fields and submit button
	username_field = driver.find_element(By.ID, 'username')
	password_field = driver.find_element(By.ID, 'password')
	submit_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
	
	# Enter the login credentials and submit the form
	username_field.send_keys(username)
	password_field.send_keys(password)
	submit_button.click()

	# Wait for the page to load after login
	time.sleep(20)

	return driver

def save_page_html(driver, file_path):
	html = driver.page_source
	# print(html)
	with open(file_path, "w") as f:
		f.write(html)

def load_html(file_path):
	with open(file_path, "r", encoding="utf-8") as f:
		html = f.read()
	return html

def create_folder_structure(path):
	isExist = os.path.exists(path)
	asg_path = os.path.join(path, "Assignments")
	pages_path = os.path.join(path, "Pages")
	if not isExist:
		os.makedirs(asg_path)
		os.makedirs(pages_path)
	
	return [pages_path, asg_path]

def download_modules_webpages(driver, links, module_idx, path, page_name):
	for idx, url in enumerate(links):
		driver.get(url)
		html = driver.page_source
		filename = f"Module{module_idx}_{page_name}{idx}"
		with open(os.path.join(path, f"{filename}.html"), "w") as f:
			f.write(html)

def download_all_webpages(username, password, base_url, home_page_link):
	parser = 'html.parser'
	home_filename = f"HomePage"
	modules_filename = f"ModulesPage"
	modules_link_class_name = "modules"
	html_data_filepath = "../HTML_DATA"
	html_corpus_filepath = "../HTML_extracted_lines"

	# Login
	driver = login(base_url, username, password)
	
	# Extract home page data
	driver.get(home_page_link) 
	home_file_path = os.path.join(html_data_filepath, f"{home_filename}.html")
	save_page_html(driver, home_file_path)

	# Extract modules page data
	home_html = load_html(home_file_path)

	soup = BeautifulSoup(home_html, parser)
	modules_link = base_url + soup.find('a', {'class': modules_link_class_name})['href']

	driver.get(modules_link)
	module_file_path = os.path.join(html_data_filepath, f"{modules_filename}.html")
	save_page_html(driver, module_file_path)
	
	# Get list of all the links for the pages and the modules
	module_page_links = get_links_from_modules_page(module_file_path, base_url)

	download_links_list = []
	for idx, module in enumerate(module_page_links):
		page_links_list = module["Pages"]
		asg_links_list = module["Assignments"]

		if len(asg_links_list) == 0:
			download_links_list.extend(page_links_list)

		else:
			download_links_list.extend(page_links_list)
			download_links_list.append(asg_links_list)
			
			# Create folder to hold the webpages
			html_path = os.path.join(html_data_filepath, f"Module_{idx}")
			corpus_path = os.path.join(html_corpus_filepath, f"Module_{idx}")

			pages_path, asg_path = create_folder_structure(html_path) # Creating folders for html
			_, _ = create_folder_structure(corpus_path) # Creating folders for corpus
			
			# Download webpage
			pages_links = download_links_list[0:len(download_links_list)-1]
			asg_links = download_links_list[-1]
			
			download_modules_webpages(driver, 
			    pages_links, 
				idx, 
				pages_path, 
				page_name="Pages")
			
			download_modules_webpages(driver, 
			    asg_links, 
				idx, 
				asg_path,  
				page_name="Asg")

			download_links_list = []

if __name__ == "__main__":
	home_url = "https://canvas.oregonstate.edu/"
	username = ""
	password = ""
	course_home_page = "https://canvas.oregonstate.edu/courses/1870084"
	download_all_webpages(username, password, base_url = home_url, home_page_link = course_home_page)