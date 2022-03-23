from bs4 import BeautifulSoup
import re
import requests
import pandas as pd
import urllib.request
from representative import Representatives
from selenium import webdriver

'''
script to grab all the Utah representatives and their contact info
'''

def grab_utah_house():
    """returns pandas df of the Utah House members"""

    url_root = 'https://house.utah.gov/' # root url where we'll scrape everything

     ## dictionary to store values
    house_data = {
    "District": [],
    "Mail Address": [],
    "Email Address":[],
    "Representative": [],
    "Party": [],
    "Counties": [],
    "Phone Number": [],
    }

    # load roster of the house members
    source = requests.get(url_root + 'house-members/').text
    soup = BeautifulSoup(source, 'lxml')

    count = 0 # count through each data cell in the table
    rep = [] # temp list to store a row of data
    get_email_flag = True # boolean flag to grab email address and mail address from drill down site
    for m in soup.find_all('table', id='repdata')[0].find_all('td'):
        # second column has drill down link to get other two fields
        if m.find_all('a', href=True) and get_email_flag:
            more_info_source = requests.get(url_root + m.find_all('a', href=True)[0]['href']).text
            more_info_soup = BeautifulSoup(more_info_source, 'lxml')
            for div in more_info_soup.find_all('div', class_='et_pb_blurb_description'):
                if re.match('(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})', div.text):
                    continue
                if div.text == '\n\n\n\n\n\n\n':
                    continue
                rep.append(div.text)
            get_email_flag = False
        rep.append(m.text)
        count += 1
        if count % 5 == 0:
            # append row of data\
            house_data["District"].append(rep[0])
            house_data["Mail Address"].append(rep[1])
            house_data["Email Address"].append(rep[2])
            house_data["Representative"].append(rep[3])
            house_data["Party"].append(rep[4])
            house_data["Counties"].append(rep[5].split(','))
            house_data["Phone Number"].append(rep[6].replace("View Rep Page", ""))
            rep = [] # reset temp row
            get_email_flag = True

    df = pd.DataFrame(house_data)
    df['Chamber'] = "House"
    df = df[["District", "Representative", "Party", "Chamber", "Counties", "Phone Number", "Email Address", "Mail Address"]]

    print("Done scraping the house.")

    return df

def grab_utah_senate():
    """returns pandas df of the Utah senate members"""

     ## dictionary to store values
    senate_data = {
    "District": [],
    "Representative": [],
    "Party": [],
    "Email Address":[],
    "Counties": []
    }


    # load roster of the house members
    roster_url = 'https://senate.utah.gov/senate-roster/'
    options = webdriver.ChromeOptions()
    DRIVER_PATH = '/Users/isaacstevens/Downloads/chromedriver 4'
    options.add_argument("--incognito")
    wd = webdriver.Chrome(executable_path=DRIVER_PATH, options = options)
    wd.get(roster_url)
    toggle = wd.find_element_by_xpath("//button[@id='toggle-table']")
    toggle.click()
    html_source = wd.page_source
    wd.close()
    wd.quit()

    soup = BeautifulSoup(html_source, 'lxml')
    rep = []
    count = 0
    for row in soup.find_all('td'):
        rep.append(row.text)
        count += 1
        if count % 5 == 0:
            # append row of data
            senate_data["District"].append(rep[0])
            senate_data["Representative"].append(rep[1])
            if rep[2] == 'D':
                senate_data["Party"].append("Democrat")
            else:
                senate_data["Party"].append("Republican")
            senate_data["Email Address"].append(rep[3])
            senate_data["Counties"].append(rep[4].split(','))
            rep = [] # reset temp row

    df = pd.DataFrame(senate_data)
    df['Phone Number'] = 'NA'
    df['Mail Address'] = 'NA'
    df['Chamber'] = "Senate"
    df = df[["District", "Representative", "Party", "Chamber", "Counties", "Phone Number", "Email Address", "Mail Address"]]

    print("Done scraping the senate.")

    return df

# get dataframes, add together, then save as csv
df1 = grab_utah_house()
df2 = grab_utah_senate()
all_reps = pd.concat([df1, df2], ignore_index=True, sort=False)

all_reps.to_csv("all_reps.csv", index=False)
