import requests
import bs4
import re


class Paper():
    """ A class that holds the information for an Arxiv paper. """

    def __init__(self, number, title, names=None, ids=None):
        """ Initialize a paper with the arxiv number and the title.
            The authors and ids can also be added.
        """

        self.number = number
        self.title = title
        self.authors = []
        self.identifiers = []
        self.link = u'http://arxiv.org/abs/' + number

        if names is not None:
            self.add_author(names)
        if ids is not None:
            self.add_identifier(ids)

    def add_author(self, names):
        """ Add the authors names to the paper. """
        try:
            self.authors = self.authors + names
        except TypeError:
            self.authors.append(names)

    def add_identifier(self, ids):
        """ Add the identifiers ids to the paper. """
        try:
            self.identifers = self.identifiers + ids
        except TypeError:
            self.identifiers.append(ids)

    def remove_author(self, howmany=1):
        """ Remove the last howmany authors form the paper. """
        for i in range(howmany):
            if len(self.authors) > 0:
                print('Removing ' + self.authors.pop(-1) + ' from author list')

    def remove_identifier(self, howmany=1):
        """ Remove the last howmany identifiers form the paper. """
        for i in range(howmany):
            if len(self.identifiers) > 0:
                print('Removing ' + self.identifiers.pop(-1) +
                      ' from identifier list')

    def __str__(self):
        """ Display the paper in a somewhat nice looking way. """
        pad_left = '%%%  '
        pad_right = '  %%%'
        lp_left = len(pad_left)
        lp_right = len(pad_right)
        lp_tot = lp_left + lp_right
        authstr = 'Including ' + ', '.join(self.authors)
        maxlen = max([len(self.title), len(self.link), len(authstr)]) + lp_tot

        border = ''.join(['%'] * maxlen)
        spacer = pad_left + ''.join([' '] * (maxlen - lp_tot)) + pad_right
        spacer_title = ''.join([' '] * (maxlen - len(self.title) - lp_tot))
        spacer_link = ''.join([' '] * (maxlen - len(self.link) - lp_tot))
        spacer_authstr = ''.join([' '] * (maxlen - len(authstr) - lp_tot))
        strbody = '\n\n' + \
            border + \
            '\n' + spacer + \
            '\n' + pad_left + self.title + spacer_title + pad_right + \
            '\n' + pad_left + self.link + spacer_link + pad_right + \
            '\n' + pad_left + authstr + spacer_authstr + pad_right + \
            '\n' + spacer + \
            '\n' + border + '\n'
        return strbody


def check_authors(arxiv_names, author_filename):
    """

    Check the new arxiv mailing for the given authors.
    arxiv_names = The arxivs you're interested in, e.g astro-ph
        To check multiple arxivs include them as a list.

    author_filename = text file that contains the names of the authors
                    you want to check for.

        The format of the file should be one name per line and Last, First, e.g

        Smith,John
        James, Tom

    An example of a call would be,
    check_authors( ['astro-ph','gr-qc','hep-th','physics'], '~/my_list.txt')

    """

    print('Reading the names contained in ' + author_filename)
    if hasattr(arxiv_names, 'lower') and hasattr(arxiv_names, 'upper'):
        # We have just a single arxiv
        arxiv_names = [arxiv_names]

    authors = []
    titles = []
    numbers = []
    for arxiv_name in arxiv_names:
        url_str = 'http://arxiv.org/list/' + arxiv_name + '/new'

        print('\tChecking ' + url_str)

        bowl = requests.get(url_str)
        soup = bs4.BeautifulSoup(bowl.text, 'html.parser')

        # Every new paper is enclosed in <dd> </dd> tags
        entries = soup.find_all('dd')
        auth_t = [entry.find_next('div', {'class': 'list-authors'}).text.split(
            ':')[-1].strip().split(', \n') for entry in entries]
        handles = [[val['href'].split('+')[-1].split('/')[0].lower()
                    for val in entry.find_all('a')] for entry in entries]

        authors = authors + [dict(zip(h, a))
                             for h, a in zip(handles, auth_t)]

        titles_t = [entry.find_next('div', {'class': 'list-title'}).text.split(
            ':')[-1].strip() for entry in entries]

        titles = titles + titles_t

        # Arxiv numbers are before the <dd> tag
        numbers_t = soup.find_all('span', {'class': 'list-identifier'})
        numbers = numbers + [re.findall("\d+\.\d+", num.text)[0]
                             for num in numbers_t]

    # Now we crossreference the author list versus the department

    try:
        with open(author_filename, 'r') as f:
            author_list = f.readlines()
    except IOError:
        print(author_filename + ' could not be found!')
        raise

    author_list = [line.strip().lower() for line in author_list]

    first_names = [line.split(',')[1].strip().lower() for line in author_list]
    id_list = [(line.split(',')[0].replace('-', '_').strip() + '_' +
                line.split(',')[1].strip()[0]).lower() for line in author_list]

    papers = []
    for person, id_t in zip(first_names, id_list):
        for auths, title, number in zip(authors, titles, numbers):
            if id_t in auths.keys():
                # Check that the first name matches to avoid non-unique
                # identifiers
                if person in auths[id_t].lower():
                    if number not in [paper.number for paper in papers]:
                        # New paper
                        record = Paper(number, title)
                        record.add_author(auths[id_t])
                        record.add_identifier(id_t)
                        papers.append(record)
                    else:
                        # Add this author to the paper
                        for i, paper in enumerate(papers):
                            # Make sure we don't add the same author twice to
                            # the same paper
                            if id_t not in paper.identifiers:
                                if number == paper.number:
                                    papers[i].add_author(auths[id_t])
                                    papers[i].add_identifier(id_t)

    if len(papers) > 0:
        for paper in papers:
            print(paper)
    else:
        print('No one posted a paper today.')


if __name__ == "__main__":

    """ For command line arguments:
        first arguments are arxiv names, i.e astro-ph gr-qc physics
        last argument is file name for author list to check against """

    import sys

    if len(sys.argv) > 2:
        check_authors(sys.argv[1:-1], sys.argv[-1])
    else:
        print('Please supply an arxiv name and a list of authors.')
