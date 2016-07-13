arxiv-checker
============

A Python module to search arXiv.org. You can cross check a list of authors or keywords against either the most recent arXiv mailing or a given month/year.  Works with python 2.7 and python 3.

To install::

    pip install arxiv-checker

To check the most recent mailings of several arXiv subjects against a list of authors::

    import arxivchecker
    papers = arxivchecker.check_authors(['astro-ph', 'gr-qc', 'physics'], ['Smith, John', 'Doe, Jane'])

When displayed, each paper lists the title, a clickable url link to the abstract, and the author list. 

To check against a long list of names, use a file::
  
    papers = arxivchecker.check_authors(['astro-ph', 'gr-qc', 'physics'], 'names.txt')

If instead of names, you want to check each paper against a list of keywords in the title and abstract use::

    papers = arxivchecker.check_keywords('astro-ph', ['Planet Formation','Hot Jupiter'])
  
You can also grab all of the papers first using the scrape_arxiv function::

    papers = arxivchecker.scrape_arxiv('astro-ph')
    results = arxivchecker.check_authors_from_papers(papers, 'Doe, Jane')

Similarly, for checking keywords::
  
    papers = arxivchecker.scrape_arxiv('astro-ph')
    results = arxivchecker.check_keywords_from_papers(papers, ['GJ876','Gilese-876'])

If you want to grab all of the papers from a given month you can supply the year and month arguments::
  
    papers = arxivchecker.scrape_arxiv('astro-ph',year=2016,month=6) # June 2016
    papers = arxivchecker.scrape_arxiv('astro-ph',year=2016,month='May') # May 2016
   
Or grab all of the papers for a given year::

    papers = arxivchecker.scrape_arxiv('astro-ph',year=2016,month='all')
  
Note however that this can take a while to complete (there could be more than 10,000 papers), and arXiv discourages against crawling through the website. 

Finally, to run straight from the command line::

    python -c "import arxivchecker; arxivchecker.check_authors(['astro-ph', 'gr-qc', 'physics'], 'authors.txt') > results.txt

To email the results use the Unix mail command::

    mail -s "Arxiv Mailing" email@gmail.com < results.txt
 
The arxivchecker requires the request and bs4 modules. 


