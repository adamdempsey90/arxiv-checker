# ArxivAuthorList
Get all of the authors from the most recent mailing of arxiv and cross check the results with a list of authors you're interested in.

As an example, say you have a list of authors' arxiv identifiers housed in the file "authors.txt". To check these names against the most recent mailing of the astro-ph arxiv, you would simply do,

~~~~
git clone https://github.com/adamdempsey90/ArxivAuthorList.git && python ArxivAuthorList/arxivauthorlist.py astro-ph /path/to/file/authors.txt
~~~~

It's also easy to set this script up to run every morning after a new mailing has been sent out using a Cronjob. For example, on my work computer I have a Cronjob that runs an update script every morning at 8 am and emails me the results. To monitor arxiv I added these lines at the end of my update script.   
~~~~
if [[ $(date +%u) -lt 6 ]]; # Check that it's a weekday
then
    cd ~/ArxivAuthorList
    git pull
    python arxivauthorlist.py astro-ph /path/to/file/members.txt 
fi
~~~~
