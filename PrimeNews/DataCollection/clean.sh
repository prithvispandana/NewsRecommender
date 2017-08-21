#!/usr/bin/sh

mongo tweets_db <<\EOF
db.news.find({ publishedAt: { $lt: `date +\%Y\%m\%d -d-10day`} } ).forEach(function(doc){ db.news_history.insert(doc); db.news.remove({_id: doc._id})});
EOF

echo clean up successfully - `date +\%Y\%m\%d` >> clean.log
