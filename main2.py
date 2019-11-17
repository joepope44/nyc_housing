# -*- coding: utf-8 -*-
"""
Spyder Editor


"""
#%%
import re
import pandas as pd
import csv
import glob
import os
import sys
import numpy as np
from tika import parser
import time

#track how long script takes to run 
start = time.time()


# list of all files from nyc.gov
files = ['https://www1.nyc.gov/assets/rentguidelinesboard/pdf/2017manhattanbldgs.pdf',
         'https://www1.nyc.gov/assets/rentguidelinesboard/pdf/2017brooklynbldgs.pdf',
         'https://www1.nyc.gov/assets/rentguidelinesboard/pdf/2017bronxbldgs.pdf',
         'https://www1.nyc.gov/assets/rentguidelinesboard/pdf/2017queensbldgs.pdf',
         'https://www1.nyc.gov/assets/rentguidelinesboard/pdf/2017statenislbldgs.pdf'
        ]

#list of files broken down per borough
mn_file = 'https://www1.nyc.gov/assets/rentguidelinesboard/pdf/2017manhattanbldgs.pdf'
bk_file = 'https://www1.nyc.gov/assets/rentguidelinesboard/pdf/2017brooklynbldgs.pdf'  
bx_file = 'https://www1.nyc.gov/assets/rentguidelinesboard/pdf/2017bronxbldgs.pdf'  
qn_file = 'https://www1.nyc.gov/assets/rentguidelinesboard/pdf/2017queensbldgs.pdf'  
si_file = 'https://www1.nyc.gov/assets/rentguidelinesboard/pdf/2017statenislbldgs.pdf'  

#save column headers for pandas later
column_headers = ["ZIP", "BLDGNO1", "STREET1", "STSUFX1", "CITY", "STATUS1", "STATUS2",
           "STATUS3", "BLOCK", "LOT"]
#len(column_headers) = 10

MNparsedPDF = parser.from_file(mn_file)
BKparsedPDF = parser.from_file(bk_file)
BXparsedPDF = parser.from_file(bx_file)
QNparsedPDF = parser.from_file(qn_file)
SIparsedPDF = parser.from_file(si_file)

MN = MNparsedPDF['content']
BK = BKparsedPDF['content']
BX = BXparsedPDF['content']
QN = QNparsedPDF['content']
SI = SIparsedPDF['content']

print(" \
      Length of MN : {}\n \
      Length of BK: {}\n \
      Length of BX : {}\n \
      Length of QN : {}\n \
      Length of SI : {}".format(len(MN),len(BK),len(BX),len(QN),len(SI)))


#parse pdf with tika, do some newline and tab cleanup
'''temp = []
for file in files: 
    #parsePDF is a dict
    parsedPDF = parser.from_file(file)
    #pdf is a string
    pdf= parsedPDF['content']
    pdf = pdf.replace('\n\n', '\n')
    temp.append(pdf)'''
    
text = MN + BK + BX + QN + SI
#saving to text, but its still tab delimited
text2 = text.splitlines()

#clean up text and remove tab-delimiters. append clean lines to list 'l'. 
l = []
for line in text2:
    out = re.sub(r'\s\t','', line)
    out = re.sub(r'\t',' ', out)
    l.append(out)
    
#print('\n'.join(l))

zip_re = re.compile(r'(^\d{5})')
st_re = re.compile(r'^\w+\s((?=\w+\sTO)\w+\s\w+\s\w+|\w+)')
status_re = re.compile(r'((MULTIPLE DWELLING (A|B))(.*)\s\d{1,6}\s\d{1,6}\Z)')
block_re = re.compile(r'(\d{1,6})\s\d{1,6}\Z')
lot_re = re.compile(r'(\d{1,6}\Z)')

data = []
row = []

for line in l: 
    zip_regex = re.search(zip_re,line)
    st_regex = re.search(st_re,line)
    status_regex = re.search(status_re,line)
    block_regex = re.search(block_re,line)
    lot_regex = re.search(lot_re,line)

    regexers = (zip_regex,st_regex,status_regex,block_regex,lot_regex)
    
    #if regex is NoneType it is error. any statement below resolves. 
    if any(match is None for match in regexers):
        pass
    else:
        fields = [zip_regex.group(1),    #zip code regex
                  st_regex.group(1),     #street number
                  status_regex.group(2), #multiple dwelling A or B
                  status_regex.group(4).strip(), #groups all statuses into one string,
                                         #to be parse later
                  block_regex.group(1),  #block regex
                  lot_regex.group(1)]    #lot regex
        data.append(fields)
      
#clean up statuses and split into up to three columns        

statuses = {'421-A',
            '421-G',
            'ARTICLE 11',
            'ARTICLES 14 & 15',
            'COOP/CONDO PLAN FILE',
            'EVICT COOP/CONDO',
            'GARDEN COMPLEX',
            'J-51',
            'NON-EVICT COOP/CONDO',
            'ROOMING HOUSE',
            'SEC 608'}
snip = [['11201', '131', 'MULTIPLE DWELLING A', '421-A ARTICLE 11', '291', '45'],
        ['11201', '141', 'MULTIPLE DWELLING A', '', '291', '40'],
        ['11201', '145', 'MULTIPLE DWELLING A', '', '291', '38'],
        ['11201', '147', 'MULTIPLE DWELLING A', '', '291', '37'],
        ['11201', '153', 'MULTIPLE DWELLING B', 'ROOMING HOUSE', '291', '34'],
        ['11201', '155', 'MULTIPLE DWELLING A', '', '291', '33'],
        ['11201', '173', 'MULTIPLE DWELLING A', 'NON-EVICT COOP/CONDO', '292', '1']]

     
#break the status2 field into separate strings 

clean_data = []
for line in data:    
    #line[3] is the field in every line where the statuses have been blended
    status2 = line[3]

    #use regex to find the exact match from the set 'statuses' and 
    #add the matches to list 'status_break'
    
    status_break = []
    for s in statuses:
        word = re.escape(s)
        result = re.search(r'(^| )'+word+'($| )', status2)
        if result:
            status_break.append(result.group().strip())
    
    #insert status_break into the original fields from line
    newline = line[:3] + status_break + line[4:]
      
    #if some status fields are blank, insert empty strings into those fields
    while len(newline) < 7:
        newline.insert(-2,"")
    
    clean_data.append(newline)    
    
    
    
df = pd.DataFrame(clean_data)
df.columns = ["ZIP","STREET_NO","STATUS1","STATUS2","STATUS3","BLOCK","LOT"]

#%%
#set zips as integers to match with ny_zips data
df["ZIP"] = df["ZIP"].astype('int64')

#import list of nyc zips-> nyc boroughs
zip_df = pd.read_excel('./ny_zips.xlsx')

#%%
#merge zip data in order to get Borough data
df = df.merge(zip_df, how='left',on='ZIP')
df.drop_duplicates(inplace=True)
df = df.reset_index(drop=True)
#%%
#apply nyc city code and apply so we can formulate BBL (borough block lot) field
citycode = {"Manhattan": 1,"Bronx":2,"Brooklyn":3,"Queens":4,"Staten":5}
df["CITY CODE"] = df["BOROUGH"].map(citycode)
#%%
df["BBL"] = df["CITY CODE"].astype(str) + '-' + df["BLOCK"] + '-' + df["LOT"]
#%%

outpath = "./nyc_pdf_scrape.xlsx"
nyc_test = df.to_excel(outpath)

end = time.time()
print("Time script takes to run in seconds: {0:.2f}".format(end - start))

