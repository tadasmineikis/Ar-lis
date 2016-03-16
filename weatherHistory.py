# -*- coding=utf8 -*-
import webapp2
import cPickle
import urllib2
from storeClass import WStore2
import datetime as dt
from lib import string_date,  CosInterp
#----------------------------------------------------
#matplotlib dependencies
import numpy as np, matplotlib, matplotlib.pyplot as plt, StringIO, os
os.environ["MATPLOTLIBDATA"] = os.getcwdu()  # own matplotlib data
os.environ["MPLCONFIGDIR"] = os.getcwdu()    # own matplotlibrc
#=============================

class MainPage(webapp2.RequestHandler):

    def get(self):
        #stuf for response in browser
        self.response.write("""<html><head><title>Ar lis?</title></head><body>""")
        #make query within week
        CURD=dt.datetime(dt.date.today().year, dt.date.today().month, dt.date.today().day) 
        Q=WStore2.query(WStore2.cur_date >= dt.datetime.fromordinal( CURD.toordinal()-7) ).order(-WStore2.cur_date)
        #N_PLOT=['meteo_lt', 'lrytas_lt', 'gismeteo_lt', 'delfi_lt', 'cnn', 'uk']
        N_PLOT=['meteo_lt']
#        try:
        for pl in N_PLOT:
             self.response.write(self.wheather_history( Q.filter(WStore2.src == pl), pl, CURD))
             self.response.write("""\n""")
#        except:
#            self.response.write("not today")

        self.response.write("""</body> </html>""")

    def wheather_history(self, Q, PLT, CURD):
#        try:
        fig, ax = plt.subplots(1, 2, figsize=(10, 4))
        plt.subplots_adjust(top=0.85)
#        for key in Q.filter(WStore2.src == 'meteo_lt'):
#            plt.suptitle("Duomenys: "+str(key.data_date.date())+"\nVilnius")
#            break
        plt.suptitle("Duomenys: "+str(PLT), size=15)
        ax[0].set_title('Dienos temperatura')
        ax[1].set_title('Nakties temperatura')    
        #------------------------------------------------------------------
        #going through query and piking info to plot
        PLOT_DATE=string_date(CURD) # convert current date to the date of dictionary
        
        PLOT_DATA={'DAY':[],'TEMP_DAY':[],'TEMP_NIGHT':[],'COND_DAY':[], 'FDATE':[]}
        for key in Q:
            for date_day, idx in zip( key.content['DATE'],  range( len(key.content['DATE']) ) ):
                 if PLOT_DATE == date_day:
                      PLOT_DATA['DAY'].append(CURD.toordinal() - key.content['DATA_DATE'].toordinal() )
                      PLOT_DATA['TEMP_DAY'].append( float(key.content['TEMP_DAY'][idx]) )
                      PLOT_DATA['TEMP_NIGHT'].append( float(key.content['TEMP_NIGHT'][idx]) )
                      PLOT_DATA['COND_DAY'].append(key.content['COND_DAY'][idx] )
                      PLOT_DATA['FDATE'].append( key.content['DATA_DATE'] )
                      break
    #========================================
#            AX_0_MIN=np.min( np.array(PLOT_DATA['TEMP_DAY']) )
#            AX_0_MAX=np.max( np.array(PLOT_DATA['TEMP_DAY']) )
#            AX_1_MIN=np.min( np.array(PLOT_DATA['TEMP_NIGHT']) )
#            AX_1_MAX=np.max( np.array(PLOT_DATA['TEMP_NIGHT']) )
        AX_0_MIN=min( PLOT_DATA['TEMP_DAY'] )
        AX_0_MAX=max( PLOT_DATA['TEMP_DAY'] )
        AX_1_MIN=min( PLOT_DATA['TEMP_NIGHT'] )
        AX_1_MAX=max( PLOT_DATA['TEMP_NIGHT'] )
        
        X_interp=np.linspace(min(PLOT_DATA['DAY'])+0.05, max(PLOT_DATA['DAY'])-0.05, 100)
        
        #print X_interp
        #print PLOT_DATA['DAY']
        
        YD_interp=CosInterp(np.array(PLOT_DATA['DAY']),PLOT_DATA['TEMP_DAY'], X_interp)
        YN_interp=CosInterp(np.array(PLOT_DATA['DAY']), PLOT_DATA['TEMP_NIGHT'], X_interp)
        
        ax[0].plot(np.abs( PLOT_DATA['DAY'] ), PLOT_DATA['TEMP_DAY'], 'ok')
        ax[0].plot(X_interp, YD_interp,'-')
        ax[1].plot(np.abs( PLOT_DATA['DAY'] ), PLOT_DATA['TEMP_NIGHT'], 'ok')
        ax[1].plot(X_interp, YN_interp, '-')
        ax[0].set_xlim(0.5, 7.5)
        ax[0].set_ylim(float(AX_0_MIN)-0.5, float(AX_0_MAX)+0.5)
        ax[0].set_xlabel('Dienos pries')
        ax[0].set_ylabel('Temperatura, C')
         
        ax[1].set_xlim(0.5, 7.5)
        ax[1].set_ylim(float(AX_1_MIN)-0.5, float(AX_1_MAX)+0.5)
        ax[1].set_xlabel('Dienos pries')
        ax[1].set_ylabel('Temperatura, C')
     
#        ax[0].legend(bbox_to_anchor=(0., 1.1, 1., .102), loc=3,
#    ncol=2, mode="expand", borderaxespad=0.)
#        ax[1].legend(bbox_to_anchor=(0., 1.1, 1., .102), loc=3,
#    ncol=2, mode="expand", borderaxespad=0.)
        rv = StringIO.StringIO()
        plt.savefig(rv, format="png")
        plt.close()
        return """<img src="data:image/png;base64,%s"/>""" % rv.getvalue().encode("base64").strip()
#        finally:
#            plt.close()
#            return "NOT TODAY"

application = webapp2.WSGIApplication([
    ('/tasks/history/', MainPage),
], debug=True)
