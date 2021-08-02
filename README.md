This script scrapes https://www.phmsa.dot.gov/regulations-fr/notices and 1) builds phsma_notices.csv with three columns: publish date, Federal Register # and a summary. This can be searched (offline); 2) downloads the pdf files to /pdf.

The program goes through the 27 pages (at the time of committing the code) to get a listing of all notices and saves that data to phsma_urls_.pickle.
Then it loops through each file, checks if the pdf exists in /pdf and if not, downloads the pdf and appends the notice information to phsma_notices.csv.