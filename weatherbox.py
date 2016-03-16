# -*- coding=utf8 -*-
import webapp2
import cPickle
import urllib2
import datetime as dt
from lib import CosInterp, prepare_xticks, prepare_ploting, read_images_for_conditions, prepare_ploting_conditions
from storeClass import WStore2
import traceback, sys # for traceback to work
#----------------------------------------------------
#matplotlib dependencies
import numpy as np, matplotlib, matplotlib.pyplot as plt, StringIO, os
os.environ["MATPLOTLIBDATA"] = os.getcwdu()  # own matplotlib data
os.environ["MPLCONFIGDIR"] = os.getcwdu()    # own matplotlibrc
#------
from matplotlib import cm
#=============================

class MainPage(webapp2.RequestHandler):

    def get(self):
        #stuf for response in browser
        self.response.write("""<html><head><title>Ar lis?</title></head><body>""")
        #self.response.headers['Content-Type'] = 'text/plain'
        #make query within week
        
        ZD=dt.datetime.today()
        ZERO_DAY_ORDINAL=dt.datetime(ZD.year, ZD.month, ZD.day, ZD.hour, ZD.minute, ZD.second).toordinal()-1
        CURD=dt.datetime.fromordinal(ZERO_DAY_ORDINAL)
        Q=WStore2.query(WStore2.cur_date >= CURD ).order(-WStore2.cur_date)
        N_PLOT=['meteo_lt',  'gismeteo_lt', 'delfi_lt',  'GFS50']#, 'WRF9', 'WRF27'] 'gismeteo_lt'
        N_PLOT_COND=['meteo_lt', 'gismeteo_lt', 'delfi_lt', 'GFS50'] #
        self.response.write(self.future_weather2(Q, N_PLOT))
        self.response.write(self.future_cond(Q, N_PLOT))

        self.response.write("""</body> </html>""")
        
    def future_weather2(self, Q, N_PLOT):
        try:
            fig, ax = plt.subplots(2, 1, figsize=(13, 6))
            fig.suptitle("Vilnius", size=20)
            fig.subplots_adjust(top=0.86, bottom=0.07, hspace=0)
            #ax[0].set_title('Dienos temperatura')
            #ax[1].set_title('Nakties temperatura')
            ZD=dt.datetime.today()
            ZERO_DAY_ORDINAL=dt.datetime(ZD.year, ZD.month, ZD.day, ZD.hour, ZD.minute, ZD.second).toordinal()+1  # here we define 'tomorrow'
            XTICK_LABEL=prepare_xticks(ZERO_DAY_ORDINAL, 7) # number of days in forecast
            #------------------------------------------------------------------
            #going through query and piking info to plot
            COLORS=['b', 'r', 'c',  'm', 'k']#, 'y', 'g']
            SHIFTS=np.linspace(-0.25,0.25,5)
            for pl, clr_id, sh in zip(N_PLOT, COLORS, SHIFTS):
                for key in Q.filter(WStore2.src == pl).fetch(1):
                    try:
                        X, YD, YN=prepare_ploting(key.content, ZERO_DAY_ORDINAL)
                    except:
                        return pl,  str(e)
                    filt=(X>-0.8)&(X<6.8) # filtering of X
                    X_interp=np.linspace(X[filt][0]+0.05, X[filt][-1]-0.05, 100)
                    YD_interp=CosInterp(X[filt], YD[filt]+sh, X_interp)
                    YN_interp=CosInterp(X[filt], YN[filt]+sh, X_interp)
                    ax[0].scatter(X[filt]+0.5, YD[filt]+sh, c=clr_id, edgecolor='none', zorder=2, s=20)
                    ax[0].plot(X_interp+0.5, YD_interp, '-'+clr_id, label=key.src, zorder=1, linewidth=1.5)
                    ax[1].scatter(X[filt], YN[filt]+sh, c=clr_id, edgecolor='none', zorder=2, s=20)
                    ax[1].plot(X_interp, YN_interp, '-'+clr_id, label=key.src, zorder=1, linewidth=1.5)
            #ax[0].set_xticklabels(XTICK_LABEL)
            ax[1].set_xticklabels(XTICK_LABEL)
            ax[1].tick_params(axis='both', which='major', labelsize=13)
            ax[0].tick_params(axis='both', which='major', labelsize=13)
            ax[0].axhline(0, linestyle='--', color='k', linewidth=3, alpha=0.5)
            ax[1].axhline(0, linestyle='--', color='k', linewidth=3, alpha=0.5)
	    ax[0].grid(b=True, which='major', color='k', linestyle=':')
	    ax[1].grid(b=True, which='major', color='k', linestyle=':')

            ax[0].set_xlim(-0.25, 6.75)
            #===========================
            #save litile space of unused axes
            limits=ax[0].get_ylim()
            ax[0].set_ylim([limits[0]+0.5, limits[1]-0.5])
            limits=ax[1].get_ylim()
            ax[1].set_ylim([limits[0]-0.5, limits[1]+0.5]) # cia neisku kodel taip veikia!
            #=============================
            ax[0].axvspan(-0.25, 6.75, facecolor='y', alpha=0.1)
            #ax[0].set_xlabel('Dienos')
            ax[0].set_ylabel('Dienos t., C', size=20)
            
            #hide overlaping ticks
            yticks = ax[0].yaxis.get_major_ticks()
            yticks[0].label1.set_visible(False)
            yticks = ax[1].yaxis.get_major_ticks()
            yticks[-1].label1.set_visible(False)
    
            ax[1].set_xlim(-0.25, 6.75)
            #ax[1].set_xlabel('Dienos')
            ax[1].set_ylabel('Nakties t., C', size=20)
            ax[1].axvspan(-0.25, 6.75, facecolor='b', alpha=0.1)

            ax[0].legend(bbox_to_anchor=(0., 1.03, 1., .102), loc=3,
       ncol=7, mode="expand", borderaxespad=0.)
            rv = StringIO.StringIO()
            plt.savefig(rv, format="png")
            plt.close()
            return """<img src="data:image/png;base64,%s"/>""" % rv.getvalue().encode("base64").strip()
        except Exception as e:
            plt.close()
            return str(e)#+'\n'+key.src+'\n'+str(key.content)

    def future_cond(self, Q, N_PLOT):
        try:
            fig, ax = plt.subplots(1, 1, figsize=(13, 6))
            fig.patch.set_alpha(0)
            fig.subplots_adjust(top=0.9)
            ax.set_title('Oro salygos', size=20)
            ZD=dt.datetime.today()
            ZERO_DAY_ORDINAL=dt.datetime(ZD.year, ZD.month, ZD.day, ZD.hour, ZD.minute, ZD.second).toordinal()+1  # here we define 'tomorrow'
            XTICK_LABEL=prepare_xticks(ZERO_DAY_ORDINAL, 7) # number of days in forecast
            #------------------------------------------------------------------
            #prepare images for axes decoration
            images=read_images_for_conditions()
            fig.figimage(images['giedra.png'], 90, 120,zorder=10)
            fig.figimage(images['mazai_deb.png'], 90, 250,zorder=10)
            fig.figimage(images['deb_prag.png'], 90, 380,zorder=10)
            fig.figimage(images['debesuota.png'], 90, 500,zorder=10)
            
            #COLORS=['b', 'g', 'r', 'c', 'm', 'y']
            COLORS=['b', 'r',  'c', 'm', 'k']#, 'y', 'g']
            SHIFTS=np.linspace(-0.2,0.2,5)
            cbar=''
            for pl, clr_id, sh in zip(N_PLOT, COLORS, SHIFTS):
                for key in Q.filter(WStore2.src == pl).fetch(1):
                   try:
                        X, Y, CLR, SYM=prepare_ploting_conditions(key.content, pl, ZERO_DAY_ORDINAL)
                        filt=(X>-0.4)&(X<6.8) # filtering of X
                        X_interp=np.linspace(X[filt][0]+0.05, X[filt][-1]-0.05, 400)
                        Y_interp=CosInterp(X[filt], Y[filt], X_interp)
                        ax.plot(X_interp, Y_interp+sh, '-'+clr_id, label=key.src, zorder=1, linewidth=1.5)
                        cbar=ax.scatter(X[filt], Y[filt]+sh, c=CLR[filt], s=SYM[filt]*40, edgecolor='k', vmin=-5, vmax=5, cmap=cm.RdBu, zorder=2)
                   except Exception as e:
                        return pl+'\n '+ str(e)+'\n '+key.src+'\n '+str(key.content), len(X), len(Y), len(CLR), len(SYM)
               
            ax.set_xlim(-0.25, 6.75)
            ax.set_ylim(-0.3,3.3)
            ax.set_xticklabels(XTICK_LABEL)
            ax.set_yticklabels([])
            for night0, night1 in zip(np.arange(-0.25, 6.5, 1), np.arange(0.25, 6.5, 1)):
                ax.axvspan(night0, night1, facecolor='b', alpha=0.1)
            for day0, day1 in zip(np.arange(0.25, 6.5, 1), np.arange(0.75, 6.8, 1)):
                ax.axvspan(day0, day1, facecolor='y', alpha=0.1)
    
            ax.set_xlabel('Dienos')
            ax.tick_params(axis='both', which='major', labelsize=12)
            cbar_ax = fig.add_axes([0.9, 0.1, 0.025, 0.8]) #[left, bottom, width, height]
            color_bar=fig.colorbar(cbar, cax=cbar_ax, ticks=[-5,  0,  5])
            color_bar.set_ticklabels(['Sniegas','Ivairus','Lietus'])
            
#            ax.legend(bbox_to_anchor=(0., 1.1, 1., .102), loc=3,
#            ncol=6, mode="expand", borderaxespad=0.)
    
            rv = StringIO.StringIO()
            plt.savefig(rv, format="png")
            plt.close()
            return """<img src="data:image/png;base64,%s"/>""" % rv.getvalue().encode("base64").strip()
        except Exception as e:
            plt.close()
            return pl+'\n '+ str(e)+'\n '+key.src+'\n '+str(key.content)

application = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
