arxiv-checker
============

Cross-check a file of author names against the most recent axiv.org
mailing.

To install::

  pip install arxiv-checker

To check the names contained in authors.txt against the astro-ph, gq-qc, and
physics mailings:: 

  import arxivchecker
  arxivchecker.check_authors(['astro-ph', 'gr-qc', 'physics'], 'authors.txt')

To run straight from the command line::

    python -c "import arxivchecker; arxivchecker.check_authors(['astro-ph', 'gr-qc', 'physics'], 'authors.txt')
 
The Arxiv Checker requires the request, bs4, and re modules. 
