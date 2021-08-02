from lxml import html
import requests
from bs4 import BeautifulSoup
import pickle
import csv
import time
from pathlib import Path

# Outline for Requests
# page = requests.get('http://examplesite.com')
# contents = page.content
# soup = BeautifulSoup(contents, 'html.parser')

def getPrjDir(ProjectName):
    path = Path.cwd()
    while str(path).find(ProjectName) > 0:
        path = path.parent
    return path.joinpath(ProjectName)

def ProcessPage(response):
    urls_notices = []
    #response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', class_ = 'dot-table dot-rulemaking-notices-table')
    links = table.find_all('a')
    for row in links:
        url_rel = row.get('href')
        if url_rel.find('notices'):
            pos_start = url_rel.rfind('/')
            pos_end = len(url_rel)
            url_absolute = url[:url.rfind('?')] + url_rel[pos_start:pos_end]
            urls_notices.append(url_absolute)
    return urls_notices

def GetNextPage(response):
    #response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    link = soup.find('a', title = 'Go to next page')
    url_rel = link.get('href')
    page_num_cur = url[url.rfind('=')+1:]
    page_num_new = url_rel[url_rel.rfind('=')+1:]

    if page_num_new > page_num_cur: #on page 26, the new page goes back to 0 so this will be false
        if url_rel.find('notices'):
            url_absolute = url[:-1] + page_num_new
            return url_absolute, False
        else:
            print(url_rel)
            print(page_num_cur)
            print(page_num_new)
            return url_rel, True # return true to get out of the loop. something went wrong
    else:
        print(url_rel)
        print(page_num_cur)
        print(page_num_new)
        return '', True

def ScrapeNotice(response):
    soup = BeautifulSoup(response.text, 'html.parser')

    #Get Published Date"
    temp = soup.find('div', class_="rmntc_published_date") #get the div with the date
    temp = temp.contents[2] #there are a couple children so get the last one
    date_published = temp.strip() #remove the whitespace character to get only the date

    #Get the Summary
    temp = soup.find('div', class_="rmntc_detail_summary") #get the div with the link
    summary = temp.contents[2].strip() #there are a couple children so get the last one and remove white space

    #Get PDF Link
    temp = soup.find('div', class_="rmntc_view_on_link") #get the div with the link
    temp = temp.find('a') # inside it find the link
    url_pdf = temp.get('href') # extract the URL

    # #Get the Document Number
    # pos_start = url_rel.rfind('/')
    # pos_end = url_rel.rfind('.')
    # doc_num = url_pdf[pos_start:pos_end]

    return date_published, summary, url_pdf

# * * * * * * * * * 
# M    A    I    N
# C    O    D    E
# * * * * * * * * * 

# SCRAPE THE URLS #

ProjectName = 'PhmsaNotices'
ProjDir = getPrjDir(ProjectName)
filename = 'phmsa_urls.pickle'
paths_urls = ProjDir.joinpath(filename)

list_page = []
List_urls_notices = [] #this will be a list of lists. 

if Path(paths_urls).is_file() and Path(paths_urls).stat().st_size > 1:
    infile = open(filename,'rb')
    data = pickle.load(infile)
    infile.close()
    list_page = data[0]
    List_urls_notices = data[1]
    del(data)
    
    page = list_page[-1]
    if page < 26: #manually saw that page=27 is blank. the last page to scrap is page=26
        end_of_listing = False
        page = page+1
        url = r'https://www.phmsa.dot.gov/regulations-fr/notices?page=' + str(page)
    else:
        end_of_listing = True
else:
    end_of_listing = False
    page = 0
    url = r'https://www.phmsa.dot.gov/regulations-fr/notices?page=0'

while end_of_listing == False:
    response = requests.get(url)
    #List_urls_notices.append(ProcessPage(url))
    List_urls_notices.append(ProcessPage(response))
    list_page.append(page)
    url, end_of_listing = GetNextPage(response)
    print('Going to next page ... {}'.format(url))
    page += 1
    time.sleep(10)
    
    data = (list_page, List_urls_notices)
    outfile = open(paths_urls,'wb')
    pickle.dump(data,outfile)
    outfile.close()

# SCRAPE THE PDFS & Summary Information #

filename = 'phmsa_notices.csv'
paths_notices = ProjDir.joinpath(filename)
success = 0

with open(paths_notices,'a', newline='') as f:
    writer = csv.writer(f)
    for list in List_urls_notices:
        for url in list:
            doc_num = url[url.rfind('/')+1:]
            filename_pdf = doc_num + '.pdf'
            paths_pdf = ProjDir.joinpath('pdf',filename_pdf)

            if not (Path(paths_pdf).is_file() and Path(paths_pdf).stat().st_size > 1): #ie. if the file does not exist
                # Go to the notice page and get information on the notice
                response = requests.get(url)
                date_published, summary, url_pdf = ScrapeNotice(response)
                data = [date_published, doc_num, summary]
            
                # Download the corresponding pdf
                response_pdf = requests.get(url_pdf, stream=True)
                if response_pdf.status_code == 200:
                    with open(paths_pdf, 'wb') as fd:
                        for chunk in response_pdf.iter_content(2000):
                            fd.write(chunk)
                    writer.writerow(data)
                    success += 1                
                time.sleep(3)              

print('{} pdfs were downloaded'.format(str(success)))
print('done')