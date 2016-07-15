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
        temp = re.sub("(.{" + "{:d}".format(maxlength) + "})", u"\\1\u2010\n", strval.replace('\n',''), 0, re.DOTALL).strip()

        temp = temp.split('\n')

        temp[-1] = temp[-1] +''.join([u'\u0020']*(maxlength-len(temp[-1])))
        if len(temp) > 1:
            temp[0] = temp[0][:-1]+temp[0][-1]

        return pad_left + (pad_right + '\n' + pad_left).join(temp) + pad_right

    def save(self,filename):
        with open(filename,"a") as f:
            f.write(str(self))


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

def read_papers(filename):
    with open(filename,"r") as f:
        lines = f.readlines()

    papers = []
    index_start = 0
    index_end = 0
    have_start = False

    for i,line in enumerate(lines):
        line = line.decode('utf8')

        if line.count(u'\u0025') > 10:
            if have_start:
                # End of new paper
                index_end = i

                papers.append(read_single_paper('\n'.join(lines[index_start:(index_end+1)])))
                have_start = False
            else:
                # Beggining of new paper
                index_start = i
                have_start = True

    return papers

def read_single_paper(sample):

    sample = sample.replace(u'\u0025','').strip()

    try:
        sample = sample.decode('utf8')
    except UnicodeEncodeError:
        pass

    try:
        title,url,authors = '\n'.join(sample).replace(u'\u2010\u000A','').strip().split(u'\u000A\u000A')
    except ValueError:
        print('Caught it')
        print('\n'.join(sample).replace(u'\u2010\u000A','').strip().split(u'\u000A\u000A'))
        return sample

    authors = [auth.replace(u'\u0026','').strip() for auth in authors.split(u'\u002C')]

    authors_id = [auth.split()[-1] + u'\u005F' + auth.split()[0][0].upper() for auth in authors]


    authors_dict = {key:val for key,val in zip(authors_id,authors)}

    number = url.split('/')[-1]


    return Paper(number,title,authors_dict,'')


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


def scrape_arxiv(arxiv_names,month=None,year=None,number=12000,silent=False,mute=False):
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

        if not mute:
            print(u'\tChecking ' + url_str)
        bowl = requests.get(url_str)
        if not mute:
            print(u'\tParsing data...')
        soup = bs4.BeautifulSoup(bowl.text, 'html.parser')

        # Every new paper is enclosed in <dd> </dd> tags
        entries = soup.find_all('dd')

        if len(entries) > 0:
            auth_t = [entry.find_next('div', {'class': 'list-authors'}).text.split(
                'Authors:')[-1].strip().split(', \n') for entry in entries]
            #handles = [[val['href'].split('+')[-1].split('/')[0].lower()
            #            for val in entry.find_all('a')] for entry in entries]
            authors = authors + [ authors_list_to_dict(x) for x in auth_t ]
            #authors = authors + [dict(zip(h, a))
            #                     for h, a in zip(handles, auth_t)]

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
        else:
            if not silent and not mute:
                print(u'No papers found at the url {}, are you sure {} is a proper archive?'.format(url_str,arxiv_name))

    return { res[0]:Paper(*res) for res in zip(numbers,titles,authors,abstracts) }



def check_keywords(arxiv_names, keywords,month=None,year=None,number=12000, silent=False, mute=False):
    """ Check the given arxivs against a list of keywords.
    The keywords can either be in a text file or in a list.
    Returns a list of papers that contain the keywords in either their
    title, abstract, or author list."""

    papers = scrape_arxiv(arxiv_names,month=month,year=year,number=number,silent=silent,mute=mute)

    return check_keywords_from_papers(papers,keywords,silent=silent,mute=mute)


def check_keywords_from_papers(papers,keywords,silent=False,mute=False):
    """ Check the given papers against a list of keywords.
    The keywords can either be in a text file or in a list.
    Returns a list of papers that contain the keywords in either their
    title, abstract, or author list."""

    try:
        if os.path.exists(keywords):
            with open(keywords, 'r') as f:
                if not mute:
                    print('Reading the keywords contained in ' + keywords)
                keyword_list = f.readlines()
            keyword_list = [line.strip().lower() for line in keyword_list]
        else:
            if not mute:
                print('Checking for ' + keywords)
            keyword_list = [keywords.strip().lower()]

    except TypeError:
        if not mute:
            print('Checking for the keywords: ' + '; '.join(keywords))
        keyword_list = [line.strip().lower() for line in keywords]


    records = []


    try:
        paper_list = list(papers.values())
    except AttributeError:
        paper_list = list(papers)

    for paper in paper_list:
        if any(key in ' '.join([paper.abstract.lower() , paper.title.lower()]
            + [a.lower() for a in paper.authors]) for key in keyword_list):

            if paper not in records: # Make sure we don't have duplicates
                records.append(paper)



    if len(records) > 0:
        if not mute:
            print("Found {:d} papers".format(len(records)))
            for record in records:
                print(record)

        return { r.number: r for r in records }
    else:
        if not mute:
            print('No results.')
        return None


def check_authors(arxiv_names, authors, month=None, year=None, number=12000,silent=False,mute=False):
    """ Check the given arxivs against a list of authors given in the form Last, First.
    The authors can either be in a text file or in a list.
    Returns a list of papers that contain the authors."""

    papers = scrape_arxiv(arxiv_names,month=month,year=year,number=number,silent=silent,mute=mute)

    return check_authors_from_papers(papers,authors,silent=silent,mute=mute)

def check_authors_from_papers(papers,authors,silent=False,mute=False):
    """ Check the given papers against a list of authors given in the form Last, First.
    The authors can either be in a text file or in a list.
    Returns a list of papers that contain the authors.
    Set silent = True if you don't want to see warnings.
    Set mute = True if you  don't want to see the progress reports.
    """

    try:
        if os.path.exists(authors):
            with open(authors, 'r') as f:
                if not mute:
                    print('Reading the names contained in ' + authors)
                author_list = f.readlines()
            author_list = [line.strip().lower() for line in author_list]
        else:
            if not mute:
                print('Checking for ' + authors)
            author_list = [authors.strip().lower()]

    except TypeError:
        if not mute:
            print('Checking for the names: ' + '; '.join(authors))
        author_list = [line.strip().lower() for line in authors]



    last_names = [line.split(',')[0].strip().lower() if len(line.split(','))>1 else line.strip().lower() for line in author_list]
    first_names = [line.split(',')[1].strip().lower() if len(line.split(','))>1 else '*' for line in author_list]
    id_list = [(line.split(',')[0].replace('-', '_').strip() + '_' +
                line.split(',')[1].strip()[0]).lower() if len(line.split(','))>1 else line.strip().lower() for line in author_list]


    records = []
    try:
        paper_list = list(papers.values())
    except AttributeError:
        paper_list = list(papers)

    for paper in paper_list:
        res = False
        for fname,lname,id_t in zip(first_names,last_names,id_list):
            try:
                paper_name = paper.author_dict[id_t]
                if fname in paper_name.lower():
                    res = True
            except KeyError:
                if fname == '*':
                    if lname in ' '.join(paper.authors).lower():
                        if not silent and not mute:
                            print(u'Found {} in {}, but no first name was supplied!'.format(lname,paper.number))
                        res = True

        if res and paper not in records:
            records.append(paper)

    if len(records) > 0:
        if not mute:
            print("Found {:d} papers".format(len(records)))
            for record in records:
                    print(record)
        return {r.number : r for r in records}
    else:
        if not mute:
            print('No results.')
        return None


