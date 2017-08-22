#------------------------------------------------
# structure of the project
#------------------------------------------------

__ DataCollection
│   ├── clean.sh		--> daily task for cleaning old news articles and keep only the last 10 days news in the news collection 
│   ├── DataCollection.py	--> the main script for collecting news records
│   ├── log.cfg			--> the configuration of logger
│   ├── news.cfg		--> the configuration of the main script

__ APP
│   ├── _app_.py              --> Application should be run using this file
│   ├── files                 --> Store the twitter user information in files folder
│   ├── prime                 --> categorised data for model
│   ├── primemodel.py         --> prime model trained code
│   ├── static                --> All js , css , fonts, image files stored inside static
│   ├── templates             --> all html page stored inside templates
│   ├── user_sim_matrix_calc.py --> user similarity matrix calculator which runs independently and save cosine matrix to db
|   ├── util.py               --> Utility methods are created which can be accessed throughout the application.
|   ├── sampleNewsData        -->contains sample json news file which contains above 70 thousand news records
|   ├── help                  -->requirements.txt file and help file, if any issue occoured


#------------------------------------------------
#  all tables (collections) used in the sytem
#------------------------------------------------
news		      - store News Articles (only last 10 days)
news_history	- store News Atricles which older than last 10 days
sim_col        - store the similarity matrix
spacytopics    - save user most common words of his timeline
users          - user information is stored in database
searchsave     - user search history in prime application
intrest        - user intrest derived from tweets
friends        - user friends following stored
hastags        - user hashtag storage collection
usernews       - user saved news article
userslikes     - user liked article storage 
usersdislikes  - user disliked article storage, synchronized with userlikes article 
user2category  - user personalised category is stored

#-------------------------------------------------------------------------------------------------
# Install python and necessary packages (Linux Version) #run appliaction in Linux platform
#--------------------------------------------------------------------------------------------------
#Must satisfied the below condition to run the application
# Step1 : install and run Mongodbserver?
Installation of MongoDB serverin Linux

#import public key
$ sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6

#create list file

$ echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.4.list

$sudo apt-get update
$sudo apt-get install -y mongodb-org
$Start Mongodb server
$sudo service mongod start

#Start MongoDb shell
$mongo

# for mor details https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/

# Step2: Load news data in Mongodb collection?
$ mongoimport --db tweets_db --collection news --file '<filepath>/20170815_news_history.json'

# Step3: Index data for fast search?
db.news.ensureIndex({'title' : 1}, {unique : true, dropDups : true})
db.news.ensureIndex({'url' : 1}, {unique : true, dropDups : true})

db.news.createIndex(
   {
     title: "text",
     description: "text"
   },
   {
     weights: {
       title: 3,
       description: 1
     },
     name: "TextIndex"
   }
 )

# Step4: Install all necessary package ?
$pip install -r "/help/requirements.txt"
#In some system pip is not working properly for requirements.txt file use below commands to install 
$ pip install bcrypt
$ pip install tweepy
$ pip install pymongo
$ pip install spacy
$ pip install flask
$ pip install flask_cors
$ pip install sklearn
$ pip install pandas
$ pip install apscheduler

# Step5: datacollection for recent news?
$ Python DataCollection.py

# step6: run user_sim_matrix_calc.py for getting colloborative filtering advantage?
$ python user_sim_matrix_calc.py

# Step7: run application in local system?
$ sudo python _app_.py

#-------------------------------------------------------------------------------------------------
# Install python and necessary packages (Windows Version) #run appliaction in windows platform
#--------------------------------------------------------------------------------------------------

# download Python 3.5.2 (for 64 bit)
https://www.python.org/ftp/python/3.5.2/python-3.5.2-amd64.exe
or 
# download Python 3.5.2 (for 32 bit)
https://www.python.org/ftp/python/3.5.2/python-3.5.2.exe

# install Microsoft Visual C++ 2015
http://landinghub.visualstudio.com/visual-cpp-build-tools

# download get-pip.py under C:/
https://bootstrap.pypa.io/get-pip.py

# install PIP
python get-pip.py

# install all necessary packages
python -m pip install bcrypt
python -m pip install tweepy
python -m pip install pymongo
python -m pip install spacy
python -m pip install sputnik
python -m pip install flask
python -m pip install flask_cors
python -m pip install sklearn
python -m pip install pandas


# download scipy (for 64 bit) to C:/
http://www.lfd.uci.edu/~gohlke/pythonlibs/tuft5p8b/scipy-0.19.1-cp35-cp35m-win_amd64.whl
or 
# download scipy (for 32 bit) to C:/
http://www.lfd.uci.edu/~gohlke/pythonlibs/tuft5p8b/scipy-0.19.1-cp35-cp35m-win32.whl

# install scipy (for example, 64 bit)
cd C:/
python -m pip install scipy-0.19.1-cp35-cp35m-win_amd64.whl


# download numpy+mkl (for 64 bit) to C:/
http://www.lfd.uci.edu/~gohlke/pythonlibs/tuft5p8b/numpy-1.13.1+mkl-cp35-cp35m-win_amd64.whl
or
# download numpy+mkl (for 32 bit) to C:/
http://www.lfd.uci.edu/~gohlke/pythonlibs/tuft5p8b/numpy-1.13.1+mkl-cp35-cp35m-win32.whl
cd C:/
python -m pip install numpy-1.13.1+mkl-cp35-cp35m-win_amd64.whl


#------------------------------------------------
# Install MongoDB  (Windows Version)
#------------------------------------------------

# step1 - download MongoDB v3.4.6 
https://www.mongodb.com/download-center#enterprise

# step2 - install
mkdir C:\MongoDB
install to C:\MongoDB\

# step3 - run the server
mkdir C:\MongoDB\data
cd C:\MongoDB\Server\3.4\bin
mongod -dbpath "C:\MongoDB\data"

# step4 - check if it is running successfully
If you can see "waiting for connections on port 27017", it started successfully

#------------------------------------------------
# Initialization of the System
#------------------------------------------------
#insert sample data into mongodb news collection 
> mongoimport --db tweets_db --collection news --file '<filepath>/20170815_news_history.json'
# step0 - access to MongoDB shell
> mongo
> use tweets_db

# step1 - create Unique Index on collection NEWS
db.news.ensureIndex({'title' : 1}, {unique : true, dropDups : true})
db.news.ensureIndex({'url' : 1}, {unique : true, dropDups : true})


# step2 - create Text Index on collection NEWS
db.news.createIndex(
   {
     title: "text",
     description: "text"
   },
   {
     weights: {
       title: 3,
       description: 1
     },
     name: "TextIndex"
   }
 )


# step3 - set the daily tasks
# remove old data into news_history and keep data of last 10 days in collection news only [daily task]
10 0 * * * /bin/bash /home/student/recommender/Prime-Repo/DataCollection/clean.sh

# back up the collection news  [daily task]
10 1 * * * /usr/bin/mongoexport --db tweets_db --collection news --out /TEAM_PRIME_NEWS_BACKUP/`date +\%Y\%m\%d`_news.json

# back up the collection news_history  [daily task]
20 1 * * * /usr/bin/mongoexport --db tweets_db --collection news_history --out /TEAM_PRIME_NEWS_BACKUP/`date +\%Y\%m\%d`_news_history.json


#------------------------------------------------
# How to run the system 
#------------------------------------------------

# download the scripts
Download the whole project from GitHub and release it to C:/ as PrimeNews folder

# run Data Collection
cd C:\PrimeNews\DataCollection
Python DataCollection.py

# run Calculator for User Similarity
cd C:\PrimeNews\
Python user_sim_matrix_calc.py

# run web app
cd C:\PrimeNews\
Python _app_.py
