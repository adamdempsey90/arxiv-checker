#!/usr/bin/env python

import requests
import bs4
import re


print 'Opening link...'
bowl = requests.get('http://arxiv.org/list/astro-ph/new')
soup = bs4.BeautifulSoup(bowl.text,'html.parser')
author_list=[]

entries=soup.find_all('dd')
authors = [entry.find_next('div',{'class':'list-authors'}).text.split(':')[-1].strip().split(', \n') for entry in entries]
handles=[[val['href'].split('+')[-1].split('/')[0].lower() for val in entry.find_all('a')] for entry in entries]

authors = [ dict(zip(h,a)) for h,a in zip(handles,authors) ]

titles = [entry.find_next('div',{'class':'list-title'}).text.split(':')[-1].strip() for entry in entries]
numbers = soup.find_all('span',{'class':'list-identifier'})
numbers= [re.findall("\d+\.\d+",num.text)[0] for num in numbers]




with open('/Users/zeus/ciera_members/ciera_members.txt','r') as f:
    ciera=f.readlines()


ciera=[line.strip().lower() for line in ciera]
ciera_authors=[]
for person in ciera:
    for auths,title,number in zip(authors,titles,numbers):
        if person in auths.keys():
            ciera_authors.append([auths[person],title,number])
if len(ciera_authors) > 0:
    print 'Some ciera members released an article today.'
    for (person,title,number) in ciera_authors:
        print person + ': ' + number + ', ' + title
else:
    print 'Nobody form Ciera posted a paper today.'

