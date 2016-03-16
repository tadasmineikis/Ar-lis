from google.appengine.api import users
from storeClass import WStore2
import webapp2
import cPickle
import urllib2
from lib import extract_meteo, extract_gismeteo, extract_uk, extract_yrno,  same_dicts,  extract_windguru
import datetime as dt

LOOK_BACK_TIME=2

class MainPage(webapp2.RequestHandler):
    def get(self):
        #stuf for response in browser
        self.response.headers['Content-Type'] = 'text/plain'
        self.UpdateData(url_out=self)
        self.response.write('OK')
    
    def Wget(self, key, URL):
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        try:
            wstring = opener.open(URL, timeout=20).read()                    
            if key == 'meteo_lt':
                DICT=extract_meteo(wstring)
            elif key == 'gismeteo_lt':
                DICT = extract_gismeteo(wstring)
            elif key == 'uk':
                DICT= extract_uk(wstring)
            elif key == 'windguru':
                DICT=extract_windguru(wstring)
            elif key == 'delfi_lt':
                DICT=extract_yrno(wstring)
        except:
            DICT='none'
        return DICT
        
    def UpdateData(self, url_out):
        WURL={r'http://old.meteo.lt/oru_prognoze.php':'meteo_lt', \
                       r'http://www.windguru.cz/int/index.php?sc=57555':'windguru', \
                       r'http://www.gismeteo.lt/city/weekly/4230/':'gismeteo_lt', \
                       r'http://www.weatheronline.co.uk/weather/maps/city?LANG=en&CEL=C&SI=mph&CONT=euro&LAND=LV&REGION=0004&WMO=26730&LEVEL=52&R=0&NOREGION=1':'uk', \
                       r'http://www.yr.no/place/Lithuania/Vilnius/Vilnius/long.html':"delfi_lt"}
        WINDGURU=['GFS50', 'WRF9', 'WRF27']
        for url_key in WURL:
            #retrieve data as dictionary
            MASTER_DICT=self.Wget(WURL[url_key], url_key)
            if MASTER_DICT != 'none':
                for DICT,  id_DICT in zip(MASTER_DICT, range(len(MASTER_DICT))):
                    #prepare to store data
                    if WURL[url_key]=='windguru':
                        store=WStore2(cur_date=dt.datetime.today(),\
                                            content=DICT,\
                                            data_date=DICT['DATA_DATE'],\
                                            idx=dt.datetime.toordinal(DICT['DATA_DATE']),\
                                            src=WINDGURU[id_DICT])
                    else:
                        store=WStore2(cur_date=dt.datetime.today(),\
                                            content=DICT,\
                                            data_date=DICT['DATA_DATE'],\
                                            idx=dt.datetime.toordinal(DICT['DATA_DATE']),\
                                            src=WURL[url_key])
                    #check if such entry already exist
                    if WURL[url_key]=='windguru':
                        qry=WStore2.query(WStore2.idx >= store.idx-LOOK_BACK_TIME, WStore2.src==WINDGURU[id_DICT]).order(WStore2.idx)
                        #store.put()
                        #url_out.response.write(id_DICT+' stored!\n')
                    else:
                        qry=WStore2.query(WStore2.idx >= store.idx-LOOK_BACK_TIME, WStore2.src==WURL[url_key]).order(WStore2.idx)
                    #iterate over recent entries
                    DUPLICATE=False
                    for key in qry.iter():
                         if same_dicts(key.content, store.content):
                             if WURL[url_key]=='windguru':
                                 url_out.response.write('\nDuplicate found, aborting data storing '+WURL[url_key]+' ' +WINDGURU[id_DICT]+'\n')
                             else:
                                  url_out.response.write('\nDuplicate found, aborting data storing '+WURL[url_key]+'\n')
                             DUPLICATE=True
                             break
                    if not DUPLICATE:
                      store.put()
                      if WURL[url_key]=='windguru':
                           url_out.response.write(WURL[url_key]+' ' +WINDGURU[id_DICT]+' stored!\n')
                      else:
                          url_out.response.write(WURL[url_key]+' stored!\n')
            #else:
            #     url_out.response.write('\nError during data retrieval '+WURL[url_key]+'\n')



application = webapp2.WSGIApplication([
    ('/tasks/update/', MainPage),
], debug=True)

