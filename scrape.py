import jinja2
import os
import webapp2

from google.appengine.api import users
from google.appengine.ext import ndb


# We set a parent key on the 'Greetings' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def guestbook_key(guestbook_name='default_guestbook'):
    return ndb.Key('Guestbook', guestbook_name)

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Greeting(ndb.Model):
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        greetings_query = Greeting.query(ancestor=guestbook_key()).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(greetings=greetings,
                                                url=url,
                                                url_linktext=url_linktext))

class Guestbook(webapp2.RequestHandler):
    def post(self):
        greeting = Greeting(parent=guestbook_key())

        if users.get_current_user():
            greeting.author = users.get_current_user()

        greeting.content = self.request.get('content')
        greeting.put()
        self.redirect('/')


from google.appengine.api import urlfetch
from lxml import html
TARGET_URL = 'https://icert.doleta.gov/'
URLFETCH_TIMEOUT = 30
XPATH_CURRENT_DATE = '//*[@id="processingpost"]/p[3]/em/text()'
XPATH_MONTH = '//*[@id="processingpost"]/table[2]/tbody/tr[1]/td[1]/text()'
XPATH_YEAR = '//*[@id="processingpost"]/table[2]/tbody/tr[1]/td[2]/text()'
class MainPage2(webapp2.RequestHandler):
    def get(self):
        response = urlfetch.fetch(TARGET_URL, deadline=URLFETCH_TIMEOUT)
        status_code = int(response.status_code)
        response_headers = response.headers
        if 200 == status_code:
          data = response.content
          result = html.fromstring(data)
          current_date = result.xpath(XPATH_CURRENT_DATE)[0]
          print current_date
          month = result.xpath(XPATH_MONTH)[0]
          year = result.xpath(XPATH_YEAR)[0]
        else:
          current_date='Now'
          month = 'Horse'
          year = 'Monkey'

        template = jinja_environment.get_template('dol_report.html')
        self.response.out.write(template.render(current_date=current_date.strip(),
                                                month=month.strip(),
                                                year=str(year.strip())))

application = webapp2.WSGIApplication([
    ('/', MainPage2),
    ('/sign', Guestbook),
], debug=True)
