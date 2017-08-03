
# the document created by Bo SUN, 2017/08/03

////////////////////////////////////////////////

SCRIPT & BACKUP FILE LOCATION

///////////////////////////////////////////////

- main script and its log file
/home/student/recommender/Prime-Repo/DataCollection/DataCollection.py
/home/student/recommender/Prime-Repo/DataCollection/data_collection.log 

- old data backup script and its log file
/home/student/recommender/Prime-Repo/DataCollection/clean.sh
/home/student/recommender/Prime-Repo/DataCollection/clean.log

- backup folder
/TEAM_PRIME_NEWS_BACKUP


////////////////////////////////////////////////

MONGO DB

///////////////////////////////////////////////

- create unique index
db.news.ensureIndex({'title' : 1}, {unique : true, dropDups : true})
db.news.ensureIndex({'url' : 1}, {unique : true, dropDups : true})

- create text index
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


////////////////////////////////////////////////

TIME SCHEDULE

///////////////////////////////////////////////

# remove old data into news_history and keep data of last 10 days in collection news only [daily task]
10 0 * * * /bin/bash /home/student/recommender/Prime-Repo/DataCollection/clean.sh

# back up the collection news  [daily task]
10 1 * * * /usr/bin/mongoexport --db tweets_db --collection news --out /TEAM_PRIME_NEWS_BACKUP/`date +\%Y\%m\%d`_news.json

# back up the collection news_history  [daily task]
20 1 * * * /usr/bin/mongoexport --db tweets_db --collection news_history --out /TEAM_PRIME_NEWS_BACKUP/`date +\%Y\%m\%d`_news_history.json


