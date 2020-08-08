
#%%
'''
Written by: Antonis Kartapanis
Scope: Retrieve info from http://securities.stanford.edu. The program initially loops over the filings list provided
    by stanford on http://securities.stanford.edu/filings.html. Having collected that information (which will be 
    output in an excel file called filings_list.xlsx), it then loops over individual case filings and collects info
    regarding: 1) the status and first identified complaint (output in an excel file called fic_list.xlsx), 
    2) details from the reference complaint (output in an excel file called ref_list.xlsx) and 3) company related
    info (output in an excel file called comp_info.xlsx). The files can be linked to each other based on the case link
    url.

    In an attempt not to overload stanford's website, a sleep of 10 seconds between page requests is imposed.

You have to define the output location on line 47.

There should be a 1:1 link between all files. If not, then something went wrong.

The code is provided "as is" without warranty of any kind. Future changes made on Stanford can, and most likely will,
affect the overall functionality of the code.
'''


#%%
'''
Import relevant libraries and create empty lists in which to append info later on
'''

from bs4 import BeautifulSoup
import math
import os
import pandas as pd
import re
import requests
import time
from tqdm import tqdm

# Output lists
filings_list = []
fic_list = []
ref_list = []
comp_info_list = []

# Error Lists
filings_error_list = []
addit_info_error_list = []

# Choose where to output the data
os.chdir('Enter_your_output_location')


#%%
'''
Create relevant functions
'''


def get_filings(filings_page):
    '''
    Retrieves the initial list of filings. 
    Inputs: Filing Page
    Returns: A list of dictionaries with:
        1) The case link
        2) Filing Date
        3) District court
        4) Stock Exchange the firm is listed on
        5) Firm's ticker
    '''

    html = BeautifulSoup(filings_page.text, 'lxml')

    for link in html.findAll(class_='table-link'):

        link_temp = link.get('onclick')[17:-1]
        cells = link.findAll('td')

        # Add to Dictionary
        temp = dict(Link=link_temp,
                    Company=cells[0].text.strip(),
                    Filing_Date=cells[1].text.strip(),
                    District_Court=cells[2].text.strip(),
                    Exchange=cells[3].text.strip(),
                    Ticker=cells[4].text.strip())

        filings_list.append(temp)


def get_case_details(rel_part, link):
    '''
    Retrieve relevant filing info within the case filing page. 
    Inputs: rel_part: Refers to whether you want to get info from First Identified or Reference Complaint
            link: case relevant link
    Returns: A dictionary containing:
        1) District Court
        2) Docket number
        3) Judge's name
        4) Filing Date
        5) Class Period Start
        6) Class Period End
        7) Case link [so cases can be matched afterwards]
    '''

    # Try to get relevant data
    try:
        fields = rel_part.findAll('div', {'class': 'span4'})
        temp_dict = dict(Court=fields[0].get_text().strip()[7:],
                         Docket=fields[1].get_text().strip()[10:],
                         Judge=fields[2].get_text().strip()[7:],
                         Date_Filed=fields[3].get_text().strip()[12:],
                         Class_Period_Start=fields[4].get_text().strip()[20:],
                         Class_Period_End=fields[5].get_text().strip()[18:],
                         Link=link)
    # If it doesn't exist, then return "N/A" for those fields (i.e., there is no reference complaint)
    except:
        temp_dict = dict(Court='N/A',
                         Docket='N/A',
                         Judge='N/A',
                         Date_Filed='N/A',
                         Class_Period_Start='N/A',
                         Class_Period_End='N/A',
                         Link=link)

    return temp_dict


def get_company_information(rel_part, link):
    '''
    Retrieves more data regarding the defendant as provided by Stanford in the case page.
    Input: rel_part: Refers to the relevant html part containing this info
           link: case relevant link
    Returns: A dictionary containing:
        1) Defendant
        2) Sector the firm is operating in
        3) Industry the firm is operating in
        4) Firm's HQ location
        5) Ticker
        6) Market (refers to stock exchange)
        7) Status of the firm
        8) Case link [so cases can be matched afterwards]
    '''

    # Try to get the info
    try:
        fields = rel_part.findAll('div', {'class': 'span4'})
        defendant = rel_part.findAll('div', {'class': 'page-header'})[0].get_text()
        defendant = defendant.split(': ')[-1]
        temp_dict = dict(defendant=defendant,
                         sector=fields[0].get_text().strip().split(': ')[-1],
                         industry=fields[1].get_text().strip().split(': ')[-1],
                         hq=fields[2].get_text().strip().split(': ')[-1],
                         ticker=fields[3].get_text().strip().split(': ')[-1],
                         market=fields[4].get_text().strip().split(': ')[-1],
                         status=fields[5].get_text().strip().split(': ')[-1],
                         Link=link)

    # If not available, return "N/A"
    except:
        temp_dict = dict(defendant='N/A',
                         sector='N/A',
                         industry='N/A',
                         hq='N/A',
                         ticker='N/A',
                         market='N/A',
                         status='N/A',
                         Link=link)
    return temp_dict



def get_details(case_page):
    '''
    Main function to collect case relevant information. We enter the case page and calls for other function to then 
    collect the relevant info
    '''
       
    case_page_html = BeautifulSoup(case_page.text, 'lxml')

    # Header Info
    case_page = case_page.text
    header_info = case_page[case_page.find("Case Status"):]
    header_info = header_info[:header_info.find("</p>")]
    header_info = str(BeautifulSoup(header_info, 'html.parser').get_text())
    # Status (to be added in the First Identified Complaint Output)
    header_info = header_info[header_info.find(":") + 1:].strip()
    status = header_info[: header_info.find("\n")].strip()
    # In case status is missing:
    if status.find("On or") > -1:
        status = "Missing"

    # A) Company Info
    comp_info_list.append(get_company_information(case_page_html.find('section', {'id': 'company'}), i['Link']))

    # B) First Identified Complaint - Also add case status here (i.e. settled, dismissed, on-going)
    temp_dict = get_case_details(case_page_html.find('section', {'id': 'fic'}), i['Link'])
    temp = dict(**temp_dict, Status=status)
    fic_list.append(temp)

    # C) Reference Complaint
    ref_list.append(get_case_details(case_page_html.find('section', {'id': 'ref'}), i['Link']))


#%%
'''
Number of pages to loop over
'''

req_page = requests.get('http://securities.stanford.edu/filings.html')
html = BeautifulSoup(req_page.text, 'lxml')
num_filings = html.findAll('div', {'id': 'filings'})[0].text
num_filings = int(re.findall(r'\((.*?)\)', num_filings)[0])
num_pages = math.ceil(num_filings / 20) # 20 filings listed per page


#%%
'''
Loop over stanford's filing list to get info
'''

for i in range(num_pages):
    
    # Request filing page
    filings_page = requests.get("http://securities.stanford.edu/filings?page={}".format(i + 1))

    # Ensure the page was retrieved
    if filings_page.status_code == 200:
        get_filings(filings_page)
    # if not add to the errors list
    else:
        filings_error_list.append("http://securities.stanford.edu/filings?page={}".format(j))

    time.sleep(10)
    
# Output
filings_df = pd.DataFrame.from_dict(filings_list)
filings_df.to_excel(r"filings_list.xlsx", index=False)


#%%
'''
Having identified all filings, loop over them to get case specific details
'''

for i in tqdm(filings_list):
    
    # Request case page
    case_page = requests.get("http://securities.stanford.edu/{}".format(i['Link']))

    # If successful, then get details
    if case_page.status_code == 200:
        get_details(case_page)
    # If not then add to error list
    else:
        addit_info_error_list.append("http://securities.stanford.edu/{}".format(i['Link']))

    time.sleep(10)
    
# Output
fic_df = pd.DataFrame.from_dict(fic_list)
fic_df.to_excel(r"fic_list.xlsx", index=False)

ref_df = pd.DataFrame.from_dict(ref_list)
ref_df.to_excel(r"ref_list.xlsx", index=False)

comp_info_df = pd.DataFrame.from_dict(comp_info_list)
comp_info_df.to_excel(r"comp_info.xlsx", index=False)


#%%
'''
Ensure no errors - If the list is not 0, you need to retrieve those pages as appeared in the relevant lists
'''

print('Filing pages missed: {}'.format(len(filings_error_list)))
print('Case related pages missed: {}'.format(len(addit_info_error_list)))
