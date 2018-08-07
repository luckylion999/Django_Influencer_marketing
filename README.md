##ShoutOurBiz Installation Guide:

---

**1) Set up SSH:**

- Generate a public/private SSH key pair for `Bitbucket`
- Add the public key to your `Bitbucket` account

**2) Install MySQL:**

- Helpful links:
    - For Windows: http://www.mysqltutorial.org/install-mysql/
    - For Mac OSX: https://sequelpro.com/docs/ref/mysql/install-on-osx
    - For Debian: https://www.linode.com/docs/databases/mysql/how-to-install-mysql-on-debian-7
    - If all fails, install a container that has MySQL like `WAMP`, `XAMPP`, or variations thereof...

**3) Install Python 2.7.12:**

- Helpful links:
    - For Windows: https://www.howtogeek.com/197947/how-to-install-python-on-windows/
    - For Max OSX: http://python-guide-pt-br.readthedocs.io/en/latest/starting/install/osx/
    - For Debian: Should be included with Ubuntu distributions. If not, here are instructions: https://askubuntu.com/questions/101591/how-do-i-install-the-latest-python-2-7-x-or-3-x-on-ubuntu
- Remember to set environment variables

**4) Create a `virtualenv` for the project:**

- This step is *optional* but is *highly* recommended.
- `virtualenv` is a tool that keeps the dependencies required by different projects in separate places. It helps keep different packages from interferring with one another.
- Installation instructions:
    - http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/
    - There's wrapper library called `virtualenvwrapper` that makes `virtualenv` easier to work with. You can see more here: https://virtualenvwrapper.readthedocs.io/en/latest/
- Activate the `virtualenv`

**5) Install project:**

- Clone the project to a local directory:
    - `git clone git+ssh://git@bitbucket.org/serpclix/shoutourbiz.git`
- Open a command line in the `manage.py` directory
- `pip install -r requirements.txt`

*You may have trouble installing lxml (a dependency for pytrends) if you are using Debian (i.e. Ubuntu or its variations). See if this solves your problem: https://stackoverflow.com/questions/6504810/how-to-install-lxml-on-ubuntu

**6) Install Gulp:**

*This is optional, but is recommended to quickly abstract project preparation for local, dev, and prod environments.*

- Download and install NodeJS (https://nodejs.org/en/download/)
- `cd` into the project directory where manage.py is located and open up a command line. Enter the following to install Gulp.
- `npm install --global gulp`
- `npm install --global gulp-cli`
- `npm install`
- Here are commands to prep the project for all environments
    - `gulp prep-local` (local environment)
    - `gulp prep-dev` (remote dev environment)
    - `gulp prep-prod` (remote prod environment)
- For instance, if you want to prep the project to run locally, input `gulp prep-local`

**7) Migrate database:**

- `python manage.py migrate`


**8) Collect static files:**

- `python manage.py collectstatic`

**9) Install Elasticsearch 2.4.5**

- Elasticsearch (ES) is a search backend that speeds up retrieval. In order to use the sort and search functionalities on the site, you'll need to install it. 
- We use an older version of ES because Haystack (the intermediary between ES and Django) does not support the latest version.
- Install instructions:
    - Download and unzip ES in a folder:
        - https://www.elastic.co/downloads/past-releases/elasticsearch-2-4-5
    - We use some custom settings for ES. In `elasticsearch.yml` (which can be found in the directory where you installed `elasticsearch` or in `/etc/elasticsearch/elasticsearch.yml` on Ubuntu), append the following settings:
        - `index.number_of_replicas: 0`
        - `index.max_result_window: 100000`
        - `index.search.slowlog.threshold.query.debug: 0s`
        - `index.search.slowlog.threshold.fetch.debug: 0s`
        - `index.indexing.slowlog.threshold.index.debug: 0s`
    - We use these settings to (1) show all results and (2) log all queries
    - Open a *second* and separate console window
    - Run `bin/elasticsearch` (or `bin\elasticsearch.bat` on Windows)
    - Wait `10-15` seconds for the server to start
        - Go to `http://localhost:9200` to double-check that ES is running
    - Leave the second console open (you can minimize it)
    - On the first console, `cd` to the `manage.py` directory in the project
    - Run `python manage.py rebuild_index --verbosity=2`
        - This will build all documents that will be searcheable
        - This will take `15-20` mins

**10) Run app:**

- Run ES in the first console as a separate server
- Run Django in a second console: `python manage.py runserver`