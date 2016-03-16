# -*- coding=utf8 -*-
import webapp2
import cPickle
import urllib2
import datetime as dt
from lib import CosInterp
from storeClass import WStore2
import Image
#----------------------------------------------------
#matplotlib dependencies
import numpy as np, matplotlib, matplotlib.pyplot as plt, StringIO, os
from matplotlib import cm
os.environ["MATPLOTLIBDATA"] = os.getcwdu()  # own matplotlib data
os.environ["MPLCONFIGDIR"] = os.getcwdu()    # own matplotlibrc
#=============================

class MainPage(webapp2.RequestHandler):

    def get(self):
        #stuf for response in browser
        self.response.write("""<html><head><title>Ar lis?</title></head><body>""")
        #self.response.headers['Content-Type'] = 'text/plain'
        #make query within week
        CURD=dt.datetime(dt.date.today().year, dt.date.today().month, dt.date.today().day-1) 
        Q=WStore2.query(WStore2.cur_date >= CURD ).order(-WStore2.cur_date)
        #N_PLOT=['meteo_lt', 'lrytas_lt', 'gismeteo_lt', 'delfi_lt', 'cnn', 'uk']
        N_PLOT=['meteo_lt']
        self.response.write(self.future_weather(Q, N_PLOT))
#        try:
#            self.response.write(self.future_weather(Q, N_PLOT))
#        except:
#            self.response.write("not today")

        self.response.write("""</body> </html>""")

    def future_weather(self, Q, N_PLOT):
        try:
            fig, ax = plt.subplots(1, 2, figsize=(13, 6))
            fig.patch.set_alpha(0)
            plt.subplots_adjust(top=0.65)
            ax[0].set_title('Dienos oro salygos')
            ax[1].set_title('Nakties oro salygos')
            
            XTICK_LABEL=['']
            for key in Q.filter(WStore2.src == 'meteo_lt').fetch(1):
                for dtk in key.content['DATE']:
                    tik=dtk.split('_')[1][:3]
                    if tik.find('\xc5\xa0')!= -1:
                        tik = 'Ses'
                    tik+='\n['+dtk.split('_')[0][5:]+']'
                    XTICK_LABEL.append( tik ) 
            #------------------------------------------------------------------
            #prepare images for axes decoration
            names=[item.split()[0] for item in open('img/list.txt')]
            images={}
            for name in names:
                 images[name]=np.array(Image.open('img/'+name)).astype(np.float)/255
            fig.figimage(images['giedra.png'], 90, 95,zorder=10)
            fig.figimage(images['mazai_deb.png'], 90, 185,zorder=10)
            fig.figimage(images['deb_prag.png'], 90, 265,zorder=10)
            fig.figimage(images['debesuota.png'], 90, 360,zorder=10)
            
            fig.figimage(images['giedra_naktis.png'], 650, 95,zorder=10)
            fig.figimage(images['mazai_deb_naktis.png'], 650, 185,zorder=10)
            fig.figimage(images['deb_prag_naktis.png'], 650, 270,zorder=10)
            fig.figimage(images['debesuota.png'], 650, 360,zorder=10)
            #going through query and piking info to plot
            COLORS=['b', 'g', 'r', 'c', 'm', 'y']
            SHIFTS=np.linspace(-0.2,0.2,6)
            cbar=''
            for pl, clr_id, sh in zip(N_PLOT, COLORS, SHIFTS):
                for key in Q.filter(WStore2.src == pl).fetch(1):
                    if key.src =='meteo_lt':
                        X=np.arange(len( key.content['TEMP_DAY'][0:7] ))
                        shift=np.zeros(X.size)
                        shift[:]=sh
                        MAP_METEO={'Giedra':[0, 0],\
                       'Ma\xc5\xbeai debesuota':[1, 0],\
                       'Debesuota su pragiedruliais':[2, 0],\
                       'Trumpas sniegas':[2, 1],\
                       'Trumpas lietus':[2, 1],\
                       'Protarpiais lietus':[2, 5],\
                       'Protarpiais sniegas':[2, 5],\
                       'Debesuota':[3, 0],\
                       '\xc5\xa0lapdriba':[3, -5],\
                       'Nedidelis lietus':[3, 1],\
                       'Nedidelis sniegas':[3, -1],\
                       'Smarkus lietus':[3, 8],\
                       'Smarkus sniegas':[3, -8],\
                       'Lijundra':[3, -5],\
                       'R\xc5\xabkas':[3, 0],\
                       'Sniegas':[3, 5],\
                       'Lietus':[3, 5]}
                        Y_DAY=[] ; Y_NIGHT=[]; DAY_SYM=[]; NIGHT_SYM=[]
                        for day_cnd, night_cnd in zip(key.content['COND_DAY'], key.content['COND_NIGHT']):
                            Y_DAY.append(MAP_METEO[day_cnd][0]+sh)
                            DAY_SYM.append(MAP_METEO[day_cnd][1])
                            Y_NIGHT.append(MAP_METEO[night_cnd][0]+sh)
                            NIGHT_SYM.append(MAP_METEO[night_cnd][1])
                        
                Xnew=np.linspace(X[0]+0.05, X[-1]-0.05, 100)
                YnewD=CosInterp(X, Y_DAY, Xnew)
                YnewN=CosInterp(X, Y_NIGHT, Xnew)
                ax[0].scatter(X, Y_DAY, c=DAY_SYM, s=np.abs(DAY_SYM)*50, edgecolor='k', vmin=-8, vmax=8, cmap=cm.jet)
                ax[0].plot(Xnew, YnewD, '-'+clr_id, label=key.src)
                cbar=ax[1].scatter(X, Y_NIGHT, c=NIGHT_SYM, s=np.abs(NIGHT_SYM)*50, edgecolor='k', vmin=-8, vmax=8, cmap=cm.jet)
                ax[1].plot(Xnew, YnewN, '-'+clr_id, label=key.src)
               
            ax[0].set_xlim(-0.4, 6.4)
            ax[0].set_ylim(-0.5,3.2)
            ax[0].set_xticklabels(XTICK_LABEL)
            ax[0].set_yticklabels([])

            ax[0].set_xlabel('Dienos')
            ax[0].set_ylabel('Debesuotumas')

            ax[1].set_xlim(-0.4, 6.4)
            ax[1].set_ylim(-0.5,3.2)
            ax[1].set_yticklabels([])
            ax[1].set_xticklabels(XTICK_LABEL)
            
            
            ax[1].set_xlabel('Dienos')
            ax[1].set_ylabel('Debesuotumas')
            cbar_ax = fig.add_axes([0.9, 0.1, 0.025, 0.55]) #[left, bottom, width, height]
            color_bar=fig.colorbar(cbar, cax=cbar_ax, ticks=[])
            
            ax[0].legend(bbox_to_anchor=(0., 1.1, 1., .102), loc=3,
       ncol=2, mode="expand", borderaxespad=0.)
            ax[1].legend(bbox_to_anchor=(0., 1.1, 1., .102), loc=3,
       ncol=2, mode="expand", borderaxespad=0.)
            rv = StringIO.StringIO()
            plt.savefig(rv, format="png")
            plt.close()
            return """<img src="data:image/png;base64,%s"/>""" % rv.getvalue().encode("base64").strip()
        finally:
            plt.close()

application = webapp2.WSGIApplication([
    ('/tasks/conditions/', MainPage),
], debug=True)
