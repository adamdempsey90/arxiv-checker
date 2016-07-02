ArxivChecker
============

Cross-check a file of author names against the most recent axiv.org
mailing.

To install::

  git clone https://github.com/adamdempsey90/ArxivChecker.git

To check the names contained in authors.txt against the astro-ph, gq-qc, and
physics mailings:: 

  python ArxivChecker/arxivchecker.py astro-ph gr-qc physics authors.txt

The Arxiv Checker requires the request, bs4, and re modules.

  It's also easy to set this script up to run every morning after a new
  mailing has been sent out using a Cronjob. For example, on my work
  computer I have a Cronjob that runs an update script every morning at
  8 am and emails me the results. To monitor arxiv I added these lines
  at the end of my update script.::
  
    if [[ $(date +%u) -lt 6 ]]; # Check that it's a weekday
    then 
        cd ~/ArxivChecker git pull python arxivchecker.py astro-ph /path/to/file/members.txt 
    fi
