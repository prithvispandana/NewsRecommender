'''
Created on 2 Jun 2017

@author: nitendra
'''
from flask import Flask
from flask import g, session, request, url_for, flash
from flask import redirect, render_template
from flask_oauthlib.client import OAuth


app = Flask(__name__)
app.debug = True
app.secret_key = 'development'

oauth = OAuth(app)

twitter = oauth.remote_app(
    'twitter',
    #consumer_key='xBeXxg9lyElUgwZT6AZ0A',
    #consumer_secret='aawnSpNTOVuDCjx7HMh6uSXetjNN8zWLpZwCEU4LBrk',
    consumer_key='SkaYjiRh8xSeiJdgodBxpbRGZ',
    consumer_secret='ihP1T7lIFEyT3UkX6niqAKdoS1fot8kNamnKNx8s3XUdvHKyLv',
    base_url='https://api.twitter.com/1.1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authorize'
)


@twitter.tokengetter
def get_twitter_token():
    if 'twitter_oauth' in session:
        resp = session['twitter_oauth']
        return resp['oauth_token'], resp['oauth_token_secret']


@app.before_request
def before_request():
    g.user = None
    if 'twitter_oauth' in session:
        g.user = session['twitter_oauth']


@app.route('/')
def index():
    print("hello")
    tweets = None
    if g.user is not None:
        print(g.user)
        resp = twitter.request('statuses/mentions_timeline.json')
        if resp.status == 200:
            tweets = resp.data
        else:
            flash('Unable to load tweets from Twitter.')
    return render_template('index.html', tweets=tweets)




@app.route('/login')
def login():
    callback_url = url_for('oauthorized', next=request.args.get('next'))
    return twitter.authorize(callback=callback_url or request.referrer or None)


@app.route('/logout')
def logout():
    session.pop('screen_name', None)
    flash('You were signed out')
    return redirect(url_for('index'))


@app.route('/oauth-authorized')
def oauthorized():
    resp = twitter.authorized_response()
    if resp is None:
        flash('You denied the request to sign in.')
    else:
        session['twitter_oauth'] = resp
        access_token = resp['oauth_token']
        session['access_token'] = access_token
        session['screen_name'] = resp['screen_name'] 
        session['twitter_token'] = (
            resp['oauth_token'],
            resp['oauth_token_secret'])
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()