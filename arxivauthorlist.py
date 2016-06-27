#!/usr/bin/env python

import requests
import bs4
import re


def check_authors(arxiv_name, author_filename):
    """
    Check the new arxiv mailing for the given authors.
    arxiv_name = The arxiv you're interested in, e.g astro-ph
    author_filename = text file that contains the arxiv identifiers of
                    the authors you want to check for. Note that arxiv
                    tags authors as LASTNAME_FIRSTNAMEINITIAL.
    """

    url_str = 'http://arxiv.org/list/' + arxiv_name + '/new'

    print 'Checking ', url_str
    print '\tagainst names contained in ', author_filename

    bowl = requests.get(url_str)
    soup = bs4.BeautifulSoup(bowl.text,'html.parser')

    entries=soup.find_all('dd') # Every new paper is enclosed in <dd> </dd> tags
    authors = [entry.find_next('div',{'class':'list-authors'}).text.split(':')[-1].strip().split(', \n') for entry in entries]
    handles=[[val['href'].split('+')[-1].split('/')[0].lower() for val in entry.find_all('a')] for entry in entries]

    authors = [ dict(zip(h,a)) for h,a in zip(handles,authors) ]

    titles = [entry.find_next('div',{'class':'list-title'}).text.split(':')[-1].strip() for entry in entries]

    # Arxiv numbers are before the <dd> tag
    numbers = soup.find_all('span',{'class':'list-identifier'})
    numbers= [re.findall("\d+\.\d+",num.text)[0] for num in numbers]



    # Now we crossreference the author list versus the department

    try:
        with open(author_filename,'r') as f:
            author_list = f.readlines()
    except IOError:
        print author_filename, 'could not be found!'
        raise


    author_list =[line.strip().lower() for line in author_list]
    db_authors=[]
    for person in author_list:
        for auths,title,number in zip(authors,titles,numbers):
            if person in auths.keys():
                db_authors.append([auths[person],title,number])
    if len(db_authors) > 0:
        for (person,title,number) in db_authors:
            print person + ': ' + number + ', ' + title
    else:
        print 'No one posted a paper today.'
if __name__ == "__main__":
    import sys

    """ For command line arguments:
        first argument is arxiv name, i.e astro-ph
        second argument is file name for author list to check against """

    if len(sys.argv) > 2:
        check_authors(sys.argv[1],sys.argv[2])
    else:
        print 'Please supply two arguments.'
