# LunchScraper
To scrape menu of restaurants and create WebPage

    
- Folder structure: 
        - Output - Additional files needed to run the pages (can contain css, images and others), do not commit any generated html files,note that all files in this folder will e exposed to webpage docker -> files will be online
            ThisImage.png - stupid image of PE guy coding
        - Scripts - scripts? probably
            crontab.txt - crontab command used at start of docker (note that time of docker is winter cambridge time..)
            DockerFile - build commands for docker
            requirements.txt - all libraries needed (file is used during build of docker) 
            run.sh - control script
            scrape.py - main scraping script
            template.html - combination of html and py file which is used as template page
        docker-compose.yml - option for docker 
        docker_load_and_restart.sh - this script is run each morning in 2 a clock and updates repository on server before the build of docker (after dev is done this shall be switched off or some high value)
        README.md -  this file? probably



only i can push mo main branch, please create branches  and merge requests.

nete that these scripts will not be used only by PE, but also by my wife :) so make it as general as possible

How it works: 
each morning 7 a clock cambridge winter time script scrape.py is run, index.html is generated as result, this folder is also source folder for web docker pe.margetaj.cz

to run it locally:
1) clone repository
2) full git folder should be as environment
3) download requirements
4) run scrape.py

