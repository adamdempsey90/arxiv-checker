# -*- coding: <utf-8> -*-
from __future__ import print_function
import requests
import bs4
import json
import re
import sys
import os


class Paper():
    """ A class that holds the information for an Arxiv paper. """

    def __init__(self, number=None, title=None, auths=None,abstract=None,fromfile=None):
        """ Initialize a paper with the arxiv number, title, authors, and abstract. """

        if fromfile is not None:
            self.load(fromfile)

        else:
            self.number = number
            self.title = title
            if auths is not None:
                self.authors = list(auths.values())
                self.author_ids = list(auths.keys())
                self.author_dict = auths.copy()
            else:
                self.authors = None
                self.author_ids = None
                self.author_dict = None

            self.abstract = abstract
            self.link = u'http://arxiv.org/abs/' + number

    def format_line(self,strval, maxlength,pad_left,pad_right):
        """ Function to format a line of a given length.
        Used by the __str__ routine."""
        temp = re.sub("(.{" + "{:d}".format(maxlength) + "})", u"\\1\u2010\n", strval.replace('\n',''), 0, re.DOTALL).strip()

        temp = temp.split('\n')

        temp[-1] = temp[-1] +''.join([u'\u0020']*(maxlength-len(temp[-1])))
        if len(temp) > 1:
            temp[0] = temp[0][:-1]+temp[0][-1]

        return pad_left + (pad_right + '\n' + pad_left).join(temp) + pad_right

    def get_search_string(self):

        return '  '.join([self.abstract.lower(),self.title.lower(), self.number] + [a.lower() for a in self.author_ids] +  [a.lower() for a in self.authors])

    def save(self,filename):
        with open(filename,"a") as f:
            json.dump(vars(self),f)
    def load(self,filename):
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    dat = json.load(f)
            else:
                dat = filename
        except TypeError:
            dat = filename
        for key,val in dat.items():
            setattr(self,key,val)


    def __eq__(self,paper):
        return (self.number == paper.number)

    def __ne__(self,paper):
        return not self.__eq__(paper)

    def __le__(self,paper):
        return float(self.number) <= float(paper.number)
    def __ge__(self,paper):
        return float(self.number) >= float(paper.number)
    def __lt__(self,paper):
        return float(self.number) <  float(paper.number)
    def __gt__(self,paper):
        return float(self.number) >  float(paper.number)

    def __str__(self):
        """ Display the paper in a somewhat nice looking way. """

        maxlen = 80
        pad_char = u"\u0025"
        newline_char = u"\u000A"
        space_char = u"\u0020"
        tab_char = space_char + space_char + space_char + space_char
        comma_char = u"\u002C"
        and_char = u"\u0026"


        pad_left = pad_char + pad_char + pad_char + tab_char
        pad_right = tab_char + pad_char + pad_char + pad_char

        if len(self.authors) == 1:
            authstr = self.authors[0]
        else:
            authstr = (comma_char + space_char).join(self.authors[:-1])
            authstr += comma_char + space_char + and_char + space_char + self.authors[-1]

        authstr  = self.format_line(authstr,  maxlen, pad_left, pad_right)
        titlestr = self.format_line(self.title, maxlen, pad_left, pad_right)
        linkstr  = self.format_line(self.link, maxlen, pad_left, pad_right)
        border = ''.join([pad_char]*(maxlen + len(pad_left) + len(pad_right)))
        blank_line = pad_left + ''.join([space_char] * maxlen) + pad_right


        strbody = newline_char + \
                border + newline_char + \
                blank_line  + newline_char + \
                titlestr + newline_char + \
                blank_line  + newline_char + \
                linkstr + newline_char + \
                blank_line  + newline_char + \
                authstr + newline_char + \
                blank_line  + newline_char + \
                border + newline_char + \
                newline_char

        # Check for python 2 to convert from unicode
        if sys.version_info < (3,):
            strbody = strbody.encode("utf8","ignore")
        return strbody


def save_many(papers,filename):

    try:
        papers = list(papers.values())
    except AttributeError:
        try:
            papers = list(papers)
        except TypeError:
            papers = [papers]

    dat = [vars(paper) for paper in papers]
    with open(filename,'w') as f:
        json.dump(dat,f)

def load_many(filename):

    with open(filename,'r') as f:
        dat = json.load(f)
    papers =[Paper(fromfile=d) for d in dat]

    return {paper.number: paper for paper in papers}
def authors_list_to_dict(author_list):

    authors_dict = {}
    for a in author_list:

        if '(' in a:
            # We have an affiliation
            a = a.split('(')[0]
            #a = ' ' .join(a.split('(')[0])
        temp = a.split()

        if len(temp) > 2:
            # More than two names, take first and last
            name = (temp[0],temp[-1])
        elif len(temp) == 1:
            # Just one name, probably a spacing error
            temp = temp[0].split('.')
            name = (temp[0],temp[-1])
        else:
            # Two names
            name = (temp[0],temp[1])

        authors_dict[name[1]+'_'+name[0][0].upper()] = ' '.join(temp)
    return authors_dict

def read_paper_from_url(number):

    bowl = requests.get('http://arxiv.org/abs/'+ str(number))
    soup = bs4.BeautifulSoup(bowl.text, 'html.parser')
    title = soup.find_all('h1',attrs={'class':'title mathjax'})[0].text.split('Title:')[-1].strip()

    authors = [x.strip() for x in soup.find_all('div',attrs={'class': 'authors'})[0].text.split('Authors:')[-1].split(',')]

    abstract =  soup.find_all('blockquote',attrs={'class':'abstract mathjax'})[0].text.split('Abstract:')[-1].strip()


    return Paper(number,title,authors_list_to_dict(authors),abstract)


def scrape_arxiv(arxiv_names,new=True,recent=False,month=None,year=None,number=200,skip=0,silent=False,mute=False):
    """
    Scrape the given arxiv pages.
    By default we grab all of the papers in the latest listing.
    You can also specify a certain year and month using the month and year arguments.
    Setting month = 'all' will grab all of the papers for the year.
    Use the number argument to only select a certain number of papers.
    Note that it takes roughly 30-40 seconds to grab ~1,500 papers.
    """

    if month is None and year is None:
        if recent:
            new = False

    else:
        new = False
        recent = False
        month_dict = {'jan':1, 'january':1,
                'feb':2, 'feburary':2,
                'mar':3, 'march':3,
                'apr':4, 'april':4,
                'may':5,
                'jun':6, 'june':6,
                'jul':7, 'july':7,
                'aug':8, 'august':8,
                'sep':9, 'september':9,
                'oct':10, 'october':10,
                'nov':11, 'november':11,
                'dec':12, 'december':12,
                'all':'all'}
        try:
            month = month_dict[month.lower()]
        except AttributeError:
            pass

        try:
            year = int(str(year)[-2:])  # Last 2 digits of the year
        except ValueError:
            pass

    if hasattr(arxiv_names, 'lower') and hasattr(arxiv_names, 'upper'):
        # We have just a single arxiv
        arxiv_names = [arxiv_names]

    res = {}
    for arxiv_name in arxiv_names:

        url_str = u'http://arxiv.org/list/'
        if new:
            url_str = url_str +  arxiv_name + u'/new'
        elif recent:
            url_str = url_str + arxiv_name + u'/pastweek?skip={:d}&show={:d}'.format(skip,number)
        else:
            try:
                if month.lower() == 'all':
                    url_str = url_str + '?year={:02d}&month=all&archive={}&show={:d}'.format(year,arxiv_name,number)
            except AttributeError:
                url_str = url_str + '?year={:02d}&month={:02d}&archive={}&show={:d}'.format(year,month,arxiv_name,number)

        if not mute:
            print(u'\tChecking ' + url_str)
        bowl = requests.get(url_str)
        if not silent:
            print(u'\tParsing data...')
        soup = bs4.BeautifulSoup(bowl.text, 'html.parser')

        # Every new paper is enclosed in <dd> </dd> tags
        entries = soup.find_all('dd')

        cutoff = 0
        for list_item in soup.find_all('li'):
            temp = list_item.find_next('a')
            if temp.text == 'Replacements':
                cutoff = int(re.findall(r'\d+',temp['href'])[0])



        numbers = [re.findall('\d*\.\d+|\d+',num.text)[0] for num in soup.find_all('span', {'class': 'list-identifier'})][:cutoff-1]



        for i, (num, entry) in enumerate(zip(numbers, entries[:cutoff-1]),start=1):

            authors = entry.find_next('div', {'class': 'list-authors'}).text.split('Authors:')[-1].strip().split(', \n')
            authors = authors_list_to_dict(authors)

            title = entry.find_next('div', {'class': 'list-title'}).text.split('Title:')[-1].strip()
            abstract = entry.find_next('p', {'class': 'mathjax'})

            if abstract is None:
                abstract = ''
            else:
                abstract = abstract.text

            res[num] = Paper(num,title,authors,abstract)



    return res



def check_keywords(arxiv_names, keywords,new=True,recent=False,month=None,year=None,number=200, skip=0, silent=True, mute=False):
    """ Check the given arxivs against a list of keywords.
    The keywords can either be in a text file or in a list.
    Returns a list of papers that contain the keywords in either their
    title, abstract, or author list."""

    papers = scrape_arxiv(arxiv_names,new=new,recent=recent,month=month,year=year,number=number,skip=skip,silent=silent,mute=mute)

    return check_keywords_from_papers(papers,keywords,silent=silent,mute=mute)


def load_keywords(keywords):
    try:
        if os.path.exists(keywords):
            with open(keywords, 'r') as f:
                keyword_list = f.readlines()
            keyword_list = [line.strip().lower() for line in keyword_list]
        else:
            keyword_list = [keywords.strip().lower()]

    except TypeError:
        keyword_list = [line.strip().lower() for line in keywords]

    res_list = []

    for key in keyword_list:
        res_list.append(key)
        if ',' in key:
            key = key.split(',')

            last_name = key[0].strip().title()
            first_name = key[1].strip().title()
            res_list.append((first_name +' ' + last_name).lower())
            res_list.append((last_name + '_' + first_name[0]).lower())

    return res_list

def check_authors_from_papers(papers,authors,silent=False,mute=False):
    """ Check the given papers against a list of authors.
    The authors can either be in a text file or in a list.
    Returns a list of papers that contain the authors in either their
    title, abstract, or author list."""
    return check_keywords_from_papers(papers,authors,silent=silent,mute=mute)


def check_keywords_from_papers(papers,keywords,silent=False,mute=False):
    """ Check the given papers against a list of keywords.
    The keywords can either be in a text file or in a list.
    Returns a list of papers that contain the keywords in either their
    title, abstract, or author list."""


    keyword_list = load_keywords(keywords)


    record_list = []

    try:
        paper_list = list(papers.values())
    except AttributeError:
        paper_list = list(papers)

    for paper in paper_list:
        hits = [paper.get_search_string().count(key) for key in keyword_list]
        res_count = sum(hits)
        if res_count > 0:
            found_keys = [key for hit,key in zip(hits,keyword_list) if hit >0]
            record_list.append((res_count,found_keys,paper))


    if len(record_list) > 0:
        record_list = sorted(record_list,reverse=True)
        if not mute:
            print("Found {:d} {}".format(len(record_list),'papers' if len(record_list)>1 else 'paper'))
            for record in record_list:
                print('{:d} {}'.format(record[0], 'hits' if record[0]>1 else 'hit'))
                print(record[1])
                print(record[-1])

            return {temp[-1].number:temp[-1] for temp in record_list}
    else:
        if not mute:
            print('No results.')
        return None





def check_authors(arxiv_names, authors, new=True,recent=False, month=None, year=None, number=200,skip=0,silent=True,mute=False):
    """ Check the given arxivs against a list of authors given in the form Last, First.
    The authors can either be in a text file or in a list.
    Returns a list of papers that contain the authors."""

    papers = scrape_arxiv(arxiv_names,new=new,recent=recent,month=month,year=year,number=number,skip=skip,silent=silent,mute=mute)

    return check_keywords_from_papers(papers,authors,silent=silent,mute=mute)



