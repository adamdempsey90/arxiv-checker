# -*- coding: <utf-8> -*-
from __future__ import print_function
import requests
import bs4
import re
import sys
import os


class Paper():
    """ A class that holds the information for an Arxiv paper. """

    def __init__(self, number, title, auths,abstract):
        """ Initialize a paper with the arxiv number, title, authors, and abstract. """

        self.number = number
        self.title = title
        self.authors = list(auths.values())
        self.author_ids = list(auths.keys())
        self.author_dict = auths.copy()
        self.abstract = abstract
        self.link = u'http://arxiv.org/abs/' + number

    def format_line(self,strval, maxlength,pad_left,pad_right):
        """ Function to format a line of a given length.
        Used by the __str__ routine."""
        temp = re.sub("(.{" + "{:d}".format(maxlength-1) + "})", u"\\1\u2010\n", strval.replace('\n',''), 0, re.DOTALL).strip()

        temp = temp.split('\n')

        temp[-1] = temp[-1] +''.join([u'\u0020']*(maxlength-len(temp[-1])))

        return pad_left + (pad_right + '\n' + pad_left).join(temp) + pad_right

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

def scrape_arxiv(arxiv_names,month=None,year=None,number=12000):
    """
    Scrape the given arxiv pages.
    By default we grab all of the papers in the latest listing.
    You can also specify a certain year and month using the month and year arguments.
    Setting month = 'all' will grab all of the papers for the year.
    Use the number argument to only select a certain number of papers.
    Note that it takes roughly 30-40 seconds to grab ~1,500 papers.
    """
    new = False
    if None in [month,year]:
        new = True
    else:
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
                'dec':12, 'december':12}
        try:
            month = month_dict[month.lower()]
        except AttributeError:
            pass

        year = int(str(year)[-2:])  # Last 2 digits of the year

    if hasattr(arxiv_names, 'lower') and hasattr(arxiv_names, 'upper'):
        # We have just a single arxiv
        arxiv_names = [arxiv_names]

    authors = []
    titles = []
    numbers = []
    abstracts= []

    for arxiv_name in arxiv_names:

        url_str = u'http://arxiv.org/list/'
        if new:
            url_str = url_str +  arxiv_name + u'/new'
        else:
            try:
                if month.lower() == 'all':
                    url_str = url_str + '?year={:02d}&month=all&archive={}&show={:d}'.format(year,arxiv_name,number)
            except AttributeError:
                url_str = url_str + '?year={:02d}&month={:02d}&archive={}&show={:d}'.format(year,month,arxiv_name,number)

        print(u'\tChecking ' + url_str)
        bowl = requests.get(url_str)
        print(u'\tParsing data...')
        soup = bs4.BeautifulSoup(bowl.text, 'html.parser')

        # Every new paper is enclosed in <dd> </dd> tags
        entries = soup.find_all('dd')
        auth_t = [entry.find_next('div', {'class': 'list-authors'}).text.split(
            'Authors:')[-1].strip().split(', \n') for entry in entries]
        handles = [[val['href'].split('+')[-1].split('/')[0].lower()
                    for val in entry.find_all('a')] for entry in entries]

        authors = authors + [dict(zip(h, a))
                             for h, a in zip(handles, auth_t)]

        titles_t = [entry.find_next('div', {'class': 'list-title'}).text.split('Title:')[-1].strip()  for entry in entries]

        if new:
            abstracts_t = []
            for entry in entries:
                temp = entry.find_next('p', {'class': 'mathjax'})
                if temp is None:
                    abstracts_t.append('')
                else:
                    abstracts_t.append(temp.text)
        else:
            abstracts_t = ['']*len(entries)


        abstracts = abstracts + abstracts_t

        titles = titles + titles_t

        # Arxiv numbers are before the <dd> tag
        numbers_t = soup.find_all('span', {'class': 'list-identifier'})
        numbers = numbers + [re.findall("\d+\.\d+", num.text)[0]
                             for num in numbers_t]
    return [Paper(*res) for res in zip(numbers,titles,authors,abstracts)]



def check_keywords(arxiv_names, keywords,month=None,year=None,number=12000):
    """ Check the given arxivs against a list of keywords.
    The keywords can either be in a text file or in a list.
    Returns a list of papers that contain the keywords in either their
    title, abstract, or author list."""

    papers = scrape_arxiv(arxiv_names,month=month,year=year,number=number)

    return check_keywords_from_papers(papers,keywords)


def check_keywords_from_papers(papers,keywords):
    """ Check the given papers against a list of keywords.
    The keywords can either be in a text file or in a list.
    Returns a list of papers that contain the keywords in either their
    title, abstract, or author list."""

    try:
        if os.path.exists(keywords):
            with open(keywords, 'r') as f:
                print('Reading the keywords contained in ' + keywords)
                keyword_list = f.readlines()
            keyword_list = [line.strip().lower() for line in keyword_list]
        else:
            print('Checking for ' + keywords)
            keyword_list = [keywords.strip().lower()]

    except TypeError:
        print('Checking for the keywords: ' + '; '.join(keywords))
        keyword_list = [line.strip().lower() for line in keywords]


    records = []

    for paper in papers:
        if any(key in ' '.join([paper.abstract.lower() , paper.title.lower()]
            + [a.lower() for a in paper.authors]) for key in keyword_list):

            records.append(paper)



    if len(records) > 0:
        print("Found {:d} papers".format(len(records)))
        for record in records:
            print(record)

        return records
    else:
        print('No results.')
        return None


def check_authors(arxiv_names, authors, month=None, year=None, number=12000):
    """ Check the given arxivs against a list of authors given in the form Last, First.
    The authors can either be in a text file or in a list.
    Returns a list of papers that contain the authors."""

    papers = scrape_arxiv(arxiv_names,month=month,year=year,number=number)

    return check_authors_from_papers(papers,authors)

def check_authors_from_papers(papers,authors):
    """ Check the given papers against a list of authors given in the form Last, First.
    The authors can either be in a text file or in a list.
    Returns a list of papers that contain the authors."""

    try:
        if os.path.exists(authors):
            with open(authors, 'r') as f:
                print('Reading the names contained in ' + authors)
                author_list = f.readlines()
            author_list = [line.strip().lower() for line in author_list]
        else:
            print('Checking for ' + authors)
            author_list = [authors.strip().lower()]

    except TypeError:
        print('Checking for the names: ' + '; '.join(authors))
        author_list = [line.strip().lower() for line in authors]



    first_names = [line.split(',')[1].strip().lower() for line in author_list]
    id_list = [(line.split(',')[0].replace('-', '_').strip() + '_' +
                line.split(',')[1].strip()[0]).lower() for line in author_list]


    records = []
    for paper in papers:
        res = False
        for name,id_t in zip(first_names,id_list):
            try:
                paper_name = paper.author_dict[id_t]
                if name in paper_name.lower():
                    res = True
            except KeyError:
               pass
        if res:
            records.append(paper)

    if len(records) > 0:
        print("Found {:d} papers".format(len(records)))
        for record in records:
            print(record)
        return records
    else:
        print('No results.')
        return None


