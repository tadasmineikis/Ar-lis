# -*- coding=utf8 -*-
from bs4 import BeautifulSoup
import datetime as dt
import re
import numpy as np
import Image
import numpy as np
import yaml

def same_dicts(A, B):
    key0='TEMP_DAY'
    if len(A[key0]) == len(B[key0]):
        DUPLICATE=[]
        for key in ['DATE','TEMP_DAY','TEMP_NIGHT', 'COND_DAY', 'COND_NIGHT']:
            DUPLICATE.append( set(A[key]) ^ set(B[key]) == set([]) )
        if all(DUPLICATE):
            return True
        else:
            return False
    else:
        return False

def extract_meteo(wstring):
    DICT={}
    soup=BeautifulSoup(wstring)
    
    sval=str(soup.findAll('p')[1])
    i1_first=sval.find('>')
    i1_last=sval.find('<', i1_first+1)
    
    YMD=sval[i1_first+1:i1_last].split()[1] # year, month, date
    HMS=sval[i1_first+1:i1_last].split()[2] # hour, minute, sec
    KEY=dt.datetime(int(YMD.split('-')[0]), int(YMD.split('-')[1]), int(YMD.split('-')[2]),\
                                  int(HMS.split(':')[0]), int(HMS.split(':')[1]), int(HMS.split(':')[2]))
    
    #print "Date of data:", KEY
    
    DICT={'DATA_DATE':KEY,'DATE':[],'TEMP_DAY':[],'TEMP_NIGHT':[],'COND_DAY':[],'COND_NIGHT':[],'WIND_DAY':[],'WIND_NIGHT':[]}
    
    table = soup.find('table', {'class': 'oru_prog_lt_miest'})
    for row, idx in zip(table.findAll('tr')[1:], range(len(table.findAll('tr')[1:]))):
        col = row.findAll('td')
        if idx == 0:
            for c in col[1:]:
                elem=c
                s1val=str(elem)
                i1_first = s1val.find('>')
                i1_last = s1val.find('<',i1_first+1)
                KEY_0=s1val[i1_first+1:i1_last].split()[0]
                s2val=str(elem.findAll('span'))
                i2_first = s2val.find('>')
                i2_last = s2val.find('<',i2_first+1)
                KEY_1=s2val[i2_first+1:i2_last].split()[0]
                DICT['DATE'].append(KEY_0+"_"+KEY_1)
        if idx == 1 or idx == 2:
            for c, ix in zip(col,range(len(col))):
                elem=c.findAll('div')
                #print len(col), ix
                for e, mKEY in zip(elem,['COND','WIND','TEMP']):
                    s1val = str(e.findAll('img'))
                    i1_first = s1val.find('"')
                    i1_last = s1val.find('"',i1_first+1)
        
                    s2val = str(e.findAll('span'))
                    i2_first = s2val.find('">')
                    i2_last = s2val.find(' ', i2_first+1)
                    
                    if mKEY != 'WIND': 
                        if idx == 1:
                            DICT['COND_NIGHT'].append(s1val[i1_first+1:i1_last])
                            DICT['TEMP_NIGHT'].append( int(s2val[i2_first+2:i2_last]) )
                        if idx == 2:
                            DICT['COND_DAY'].append(s1val[i1_first+1:i1_last])
                            DICT['TEMP_DAY'].append( int(s2val[i2_first+2:i2_last]) )
                    else:
                        if idx == 1:
                            DICT['WIND_NIGHT'].append(s1val[i1_first+1:i1_last])
                        if idx == 2:
                            DICT['WIND_DAY'].append(s1val[i1_first+1:i1_last])
    return [DICT]
    
def extract_gismeteo(wstring):
    soup=BeautifulSoup(wstring)
    
    DICT={'DATA_DATE':[],'TEMP_DAY':[],\
    'TEMP_NIGHT':[],'COND_DAY':[],\
    'COND_NIGHT':[],'WIND_DAY':[],\
    'WIND_NIGHT':[], 'DATE':[], 'EXTRA_COND':[]}
    
    WEEK_NUM_2_DIENA={0:'Pirmadienis',1:'Antradienis',2:'Trečiadienis',\
                  3:'Ketvirtadienis',4:'Penktadienis',5:'Šeštadienis',6:'Sekmadienis'}
    
    idx=0
    for data in soup.find_all('td',class_="cltext"):        
        if idx%6 > 1:
            DICT['EXTRA_COND'].append( str(data).split('>')[1].split('<')[0] )
        idx+=1
    
    WDATA=soup.find_all('div',class_="rframe wblock wdata")
    #--------------------------------------------------------------------------------------
    # Temperatures
    for data in WDATA:
        TEMP=data.find_all('td',class_='temp')
        #print TEMP
        TEMP_NIGHT=re.findall(r'[-+]?\d+',str(TEMP[0]).replace('\xe2\x88\x92','-'))
        TEMP_DAY=re.findall(r'[-+]?\d+',str(TEMP[1]).replace('\xe2\x88\x92','-'))
        DICT['TEMP_NIGHT'].append(int(TEMP_NIGHT[0]))
        DICT['TEMP_DAY'].append(int(TEMP_DAY[0]))
    #=================================================
    #  Conditions
    for data in WDATA:
        COND=data.find_all('div',class_="wbshort")[0].find_all('td',class_='cltext')
        DICT['COND_NIGHT'].append(str(COND[0]).split('>')[1].split('<')[0])
        DICT['COND_DAY'].append(str(COND[1]).split('>')[1].split('<')[0])
    #=================================================
    # extra conditions

    #=================================================
    # Dates
    YEAR=int(str(soup.find_all('span',class_='icon date')).split('\"')[-2].split('-')[0])
    DAY=int(str(WDATA[0].find_all('div',class_='s_date')[0]).split('>')[1].split('<')[0].split('.')[0])
    MONTH=int(str(WDATA[0].find_all('div',class_='s_date')[0]).split('>')[1].split('<')[0].split('.')[1])
    
    DATA_DATE=dt.datetime(YEAR,MONTH,DAY)
    DICT['DATA_DATE']=DATA_DATE
    for data, n_data in zip(WDATA,range(len(WDATA))):
        date=data.find_all('div',class_='s_date')[0]
        dkey=dt.date.fromordinal(DATA_DATE.toordinal()+n_data)
        sav_key=dt.date.fromordinal(DATA_DATE.toordinal()+n_data).weekday()
        DICT['DATE'].append(str(dkey)+'_'+WEEK_NUM_2_DIENA[sav_key])
    
    return [DICT]
    
def extract_windguru(wstring):
    soup=BeautifulSoup(wstring)
    ## extracting forecast data
    a=soup.findAll('', {'class': 'fcsttabf'})
    b=str(str(a).replace('null','0').split('=')[5])
    b=b.replace('\\','')
    b=b.replace(';','')
    b=b.replace('\nvar wgopts_1','')
    GFS50 = yaml.load(b)
    GFS50 = extract_windguru_tool(GFS50,'3','APCP')
    
    b=str(str(a).replace('null','0').split('=')[12])
    b=b.replace('\\','')
    b=b.replace(';','')
    b=b.replace('\nvar wgopts_2','')
    WRF9 = yaml.load(b)
    WRF9 = extract_windguru_tool(WRF9,'21','APCP1')
    
    b=str(str(a).replace('null','0').split('=')[19])
    b=b.replace('\\','')
    b=b.replace(';','')
    b=b.replace('\nvar wgopts_3','')
    WRF27 = yaml.load(b)
    WRF27 = extract_windguru_tool(WRF27,'14','APCP1')
    
    return [GFS50, WRF9, WRF27]

def extract_windguru_tool(d, ID,PCP_CODE):
    #============================
    
    DICT={'DATA_DATE':[],'TEMP_DAY':[],\
    'TEMP_NIGHT':[],'COND_DAY':[],\
    'COND_NIGHT':[],'WIND_DAY':[],\
    'WIND_NIGHT':[], 'DATE':[], 'EXTRA_COND':[],'EXTRA_TEMP':[],'EXTRA_DAY':[]}
    
    WEEK_NUM_2_DIENA={0:'Pirmadienis',1:'Antradienis',2:'Trečiadienis',\
                  3:'Ketvirtadienis',4:'Penktadienis',5:'Šeštadienis',6:'Sekmadienis'}
                  
    sunrise=(float(d['sunrise'].split(':')[0])+float(d['sunrise'].split(':')[1])/60.)/24.
    sunset=(float(d['sunset'].split(':')[0])+float(d['sunset'].split(':')[1])/60.)/24.
    
    DICT['DATA_DATE']=dt.datetime.strptime(d['fcst'][ID]['initdate'],'%Y-%m-%d %H:%M:%S')
    uniq_day,uniq_idx=np.unique(d['fcst'][ID]['hr_d'],return_index=True)
    n_day=0

    for key in uniq_idx:
        dkey=dt.date.fromordinal(DICT['DATA_DATE'].toordinal()+n_day)
        DICT['DATE'].append(str(dkey)+'_'+WEEK_NUM_2_DIENA[d['fcst'][ID]['hr_weekday'][key]])
        n_day+=1
    
    for key in d['fcst'][ID]['TMPE']:
        DICT['EXTRA_TEMP'].append(key)
    
    for key  in  d['fcst'][ID]['hours']:
        DICT['EXTRA_DAY'].append( (float(d['fcst'][ID]['hr_h'][0])+float(key))/24. )
        #DICT['EXTRA_DAY'].append(int(key0))
    
    for key0, key1 in zip(d['fcst'][ID]['TCDC'],d['fcst'][ID][PCP_CODE]):
        if key1 == '':
            key1=0
        if key0=='':
            key=0
        DICT['EXTRA_COND'].append([key0, float(key1)])
    day_array=np.array(d['fcst'][ID]['hr_d'])
    temp_array=np.array(d['fcst'][ID]['TMPE'])
    
    unique_array,unique_index=np.unique(day_array,return_index=True)
    
    for index in sorted(unique_index):
        ind = (day_array[index]==day_array)
        cur_day = np.array(DICT['EXTRA_DAY'])[ind]%1
        cur_day_temp = temp_array[ind]
        max_day = max(cur_day)
        mid_day=(sunrise+sunset)*0.5
    
        if max_day > mid_day:
            day_ind = (cur_day > sunrise ) & (cur_day<sunset)
        else:
            day_ind=np.array([],dtype=np.bool)
        night_ind = (cur_day < sunrise ) & (cur_day>0)
            
        try:
            DICT['TEMP_DAY'].append(max(cur_day_temp[day_ind]))
        except:
            DICT['TEMP_DAY'].append(np.nan)
        try:
            DICT['TEMP_NIGHT'].append(min(cur_day_temp[night_ind]))
        except:
            DICT['TEMP_NIGHT'].append(np.nan)
    return DICT
    
def extract_yrno(wstring):
    DICT={'DATA_DATE':[],'TEMP_DAY':[],\
    'TEMP_NIGHT':[],'COND_DAY':[],\
    'COND_NIGHT':[],'WIND_DAY':[],\
    'WIND_NIGHT':[], 'DATE':[], 'EXTRA_COND':[]}
    soup=BeautifulSoup(wstring)
    
    #set data date
    RAW_TIME=soup.find_all('div',id="yr-timestamp")
    TIME=re.findall(r'\d+',str(RAW_TIME))
    HOUR=int(TIME[0])
    MIN=int(TIME[1])
    TODAY=dt.datetime.now()
    DICT['DATA_DATE']=dt.datetime(TODAY.year, TODAY.month, TODAY.day, HOUR, MIN)
    
    #preextract data
    WDATA=soup.find_all('table',id='detaljert')
    #extract dates
    WEEK_NUM_2_DIENA={0:'Pirmadienis',1:'Antradienis',2:'Trečiadienis',\
         3:'Ketvirtadienis',4:'Penktadienis',5:'Šeštadienis',6:'Sekmadienis'}
    DATES=WDATA[0].find_all('th',scope="rowgroup")
    for item in DATES:
        d=re.findall(r'\d+',str(item))[1:]
        DAY=int(d[0])
        MONTH=int(d[1])
        YEAR=int(d[2])
        
        WEEK_DAY=dt.date(YEAR,MONTH,DAY).weekday()
        DICT['DATE'].append(str(YEAR)+'-'+str(MONTH)+'-'+str(DAY)+'_'+WEEK_NUM_2_DIENA[WEEK_DAY])
    #pre-extract data further
    PROP_DATA=WDATA[0].find_all('td')
    #extract temps and conditions
#    for idx in range(len(DICT['DATE'])*4):
#        if idx % 2 == 0:
#            if idx % 4 == 0:
#                for item, it_idx in zip(PROP_DATA[idx*5:(idx+1)*5],range(5)):
#                    if it_idx ==1:
#                        DICT['COND_NIGHT'].append( str(item).split('"')[1].split('.')[0] )
#                    elif it_idx ==2:
#                        DICT['TEMP_NIGHT'].append( int(re.findall(r'[+-]?\d+',str(item))[0]) )
#            else:
#                for item, it_idx in zip(PROP_DATA[idx*5:(idx+1)*5],range(5)):
#                    if it_idx ==1:
#                        DICT['COND_DAY'].append( str(item).split('"')[1].split('.')[0] )
#                    elif it_idx ==2:
#                        DICT['TEMP_DAY'].append( int(re.findall(r'[+-]?\d+',str(item))[0]) )
    
    #extract all temperatures
    DAY_TEMP={}
    DAY_IDX=-1
    DAY_TEMP[DAY_IDX]=[]
    for idx in range(len(DICT['DATE'])*4):
        if idx%4==0: # because idx starts with 0
            DAY_IDX+=1
            DAY_TEMP[DAY_IDX]=[]
        for item, it_idx in zip(PROP_DATA[idx*5:(idx+1)*5],range(5)):
            if it_idx == 2:
               # print it_idx,item, int(re.findall(r'[+-]?\d+',str(item))[0])
                DAY_TEMP[DAY_IDX].append( int(re.findall(r'[+-]?\d+',str(item))[0]) )
    
    DAY_IDX=-1
    for idx in range(len(DICT['DATE'])*4):
        if idx%4==0: # because idx starts with 0
            DAY_IDX+=1
        if idx % 2 == 0:
            if idx % 4 == 0:
                for item, it_idx in zip(PROP_DATA[idx*5:(idx+1)*5],range(5)):
                    if it_idx ==1:
                        DICT['COND_NIGHT'].append( str(item).split('"')[1].split('.')[0] )
                    elif it_idx ==2:
                        DICT['TEMP_NIGHT'].append( min(DAY_TEMP[DAY_IDX]) )
            else:
                for item, it_idx in zip(PROP_DATA[idx*5:(idx+1)*5],range(5)):
                    if it_idx ==1:
                        DICT['COND_DAY'].append( str(item).split('"')[1].split('.')[0] )
                    elif it_idx ==2:
                        DICT['TEMP_DAY'].append( max(DAY_TEMP[DAY_IDX]) )


    
    for idx in range(len(DICT['DATE'])*4):
        for item, it_idx in zip(PROP_DATA[idx*5:(idx+1)*5],range(5)):
            if it_idx == 1:
                DICT['EXTRA_COND'].append(str(item).split('"')[1].split('.')[0])
    return [DICT]
    
def extract_uk(wstring):
    DICT={'DATA_DATE':[],'TEMP_DAY':[],\
    'TEMP_NIGHT':[],'COND_DAY':[],\
    'COND_NIGHT':[],'WIND_DAY':[],\
    'WIND_NIGHT':[], 'DATE':[], 'EXTRA_COND':[], 'EXTRA_PROB':[]}
    soup=BeautifulSoup(wstring)
    #set data date
    SHMONTH_TO_NUM={"Jan":1,"Feb":2,"Mar":3,\
                "Apr":4,"May":5,"Jun":6,\
                "Jul":7,"Aug":8,"Sep":9,\
                "Oct":10,"Nov":11,"Dec":12}
    RAW_DDATE=soup.find_all('div',class_='last_up')[0]
    DDATE=str(RAW_DDATE).split(',')
    TODAY=dt.datetime.now()
    DAY=int(DDATE[1].split()[0])
    MONTH=SHMONTH_TO_NUM[ DDATE[1].split()[1] ]
    DTIME=re.findall(r'\d+',DDATE[-1])
    HOUR=int(DTIME[0])
    MIN=int(DTIME[1])
    #-----------------------
    DATA_DATE=dt.datetime(TODAY.year,MONTH,DAY,HOUR,MIN)
    DICT['DATA_DATE']=DATA_DATE
    #---------------------
    #pre-proccess data
    WDATA=soup.find_all('table', class_='g3_14_day')
    #write temperatures
    for item in WDATA[0].find_all('tr')[1]:
        try:
            d=str(item).split('>')[1].split('<')[0]
            DICT['TEMP_DAY'].append(int(d))
        except:
            pass    
    for item in WDATA[0].find_all('tr')[2]:
        try:
            d=str(item).split('>')[1].split('<')[0]
            DICT['TEMP_NIGHT'].append(int(d))
        except:
            pass
    
    CONTAINER=WDATA[0].find_all('img',title=True)
    N_TIMES=len(CONTAINER)
    for item, idx in zip(CONTAINER,range(N_TIMES)):
        if idx<8:
            DICT['COND_NIGHT'].append(str(item).split('\"')[1].rstrip(' '))
        elif idx>15 and idx <24:
            DICT['COND_DAY'].append(str(item).split('\"')[1].rstrip(' '))
            
    CONTAINER=WDATA[0].find_all('img',title=True)
    N_TIMES=len(CONTAINER)
    COND={3:[],9:[],15:[],21:[]}
    for item, idx in zip(CONTAINER,range(len(CONTAINER))):
        if idx<8:
            COND[3].append(str(item).split('\"')[1].rstrip(' '))
            DICT['COND_NIGHT'].append(str(item).split('\"')[1].rstrip(' '))
        elif idx>7 and idx<16:
            COND[9].append(str(item).split('\"')[1].rstrip(' '))
        elif idx>15 and idx <24:
            COND[15].append(str(item).split('\"')[1].rstrip(' '))
            DICT['COND_DAY'].append(str(item).split('\"')[1].rstrip(' '))
        else:
            COND[21].append(str(item).split('\"')[1].rstrip(' '))
    for i in range(len(COND[21])):
        DICT['EXTRA_COND'].append(COND[3][i])
        DICT['EXTRA_COND'].append(COND[9][i])
        DICT['EXTRA_COND'].append(COND[15][i])
        DICT['EXTRA_COND'].append(COND[21][i])
    
    WEEK_NUM_2_DIENA={0:'Pirmadienis',1:'Antradienis',2:'Trečiadienis',\
              3:'Ketvirtadienis',4:'Penktadienis',5:'Šeštadienis',6:'Sekmadienis'}
              
    for item, idx in zip(DICT['TEMP_DAY'], range(len( DICT['TEMP_DAY'] ))):
        date=dt.datetime.fromordinal(DATA_DATE.toordinal()+idx)
        DICT['DATE'].append( str(date.date())+"_"+WEEK_NUM_2_DIENA[date.weekday()] )
        
    return [DICT]
    
def string_date(CUR_DATE):
    WEEK_NUM_2_DIENA={0:'Pirmadienis',1:'Antradienis',2:'Trečiadienis',\
              3:'Ketvirtadienis',4:'Penktadienis',5:'Šeštadienis',6:'Sekmadienis'}
    
    return str( CUR_DATE.date())+"_"+ WEEK_NUM_2_DIENA[CUR_DATE.weekday()]
    

def CosInterp(X, Y, Xnew):
    """ Interpolate with cosine betwean points """
    Ynew=np.zeros(Xnew.size)
    for xn, xni in zip(Xnew,range(Xnew.size)):
        for xi in range(X.size):
            if X[xi] <= xn and X[xi+1] > xn:
                dX=X[xi+1]-X[xi]
                z=(1.-np.cos( (xn-X[xi])/dX*np.pi) )/2.
                Ynew[xni]=float(Y[xi])*(1.-z)+float(Y[xi+1])*z
                break
    return Ynew
    
def prepare_ploting(DICT, ZERO_DAY_ORDINAL):
    SIZE=np.min([len(DICT['TEMP_DAY']), len(DICT['TEMP_NIGHT']), len(DICT['DATE'])])
    Y_DAY=np.array( DICT['TEMP_DAY'], dtype=np.float )
    Y_NIGHT=np.array( DICT['TEMP_NIGHT'], dtype=np.float  )
    X=np.zeros(len( DICT['DATE'] ), dtype=np.float)
    for date, i_date in zip(DICT['DATE'], range(len( DICT['DATE'] ))):
        tdate=date.split('_')[0].split('-')
        X[i_date]=dt.date(int(tdate[0]), int(tdate[1]), int(tdate[2])).toordinal()-ZERO_DAY_ORDINAL
    return X[:SIZE], Y_DAY[:SIZE], Y_NIGHT[:SIZE]

MAP_COND={\
#============ meteo ===============
'meteo_lt':{             'Giedra':[0, 0, 0],\
        'Ma\xc5\xbeai debesuota':[1, 0, 0],\
'Debesuota su pragiedruliais':[2, 0, 0],\
                                 'Debesuota':[3, 0, 0],\
                           'R\xc5\xabkas':[3, 0, 0],\
                           r'Perk\xc5\xnija':[3, 6, 0],\
                     'Trumpas sniegas':[2, -3,  1],\
                       'Trumpas lietus':[2, 3,  1],\
                       'Trumpas lietus su perk\xc5\xabnija':[2, 6,  1],\
                    'Nedidelis lietus':[3, 3, 1],\
                'Nedidelis sniegas':[3, -3, 1],\
                'Protarpiais lietus':[2, 3,  3],\
              'Protarpiais sniegas':[2, -3,  3],\
                    '\xc5\xa0lapdriba':[3, 0, 3],\
                                  'Lijundra':[3, -1, 3],\
                                   'Sniegas':[3, -3, 3],\
                                      'Lietus':[3, 3, 3], \
         'Lietus su perk\xc5\xabnija':[3, 6, 3], \
                       'Smarkus Lietus':[3, 3, 5],\
                     'Smarkus sniegas':[3, -3, 5] }, \
#======== gismteo=============
'gismeteo_lt_cloud':{ 'giedra':[0],\
                          'ma\xc5\xbeas debesuotumas':[1],\
                                      'debesuota':[2],\
                                      'migla':[1], \
                                 'didelis debesuotumas':[3],\
                                                'r\xc5\xabkas':[3]}, \
'gismeteo_lt_cond':{'\xc5\xabkana':[ 0,  0],\
                                  'r\xc5\xabkas':[ 0,  0],\
                                  'migla':[0, 1], \
                                  'lijundra':[-1, 1], \
                    'dulksna':[3, 1], \
                    'silpni krituliai':[0, 1], \
                    'sniego dulksna':[-3,1],\
                    'sniego kruopos':[-3, 1], \
                    'silpna dulksna':[3, 1], \
                   'nedidelis lietus':[ 3,  1],\
                   'dulksna':[ 3,  1],\
                 'nedidelis sniegas':[ -3,  1],\
                                     'lietus':[3,  3],\
                                   'sniegas':[ -3,  3],\
                           'snigs ir pustys':[-3,3],\
                    'stiprus sniegas':[ -3,  5],\
                      'stiprus lietus':[ 3,  5],\
                      'li\xc5\xabtis':[ 3,  5],\
        'protarpiais krituliai':[ 0,  1], \
                                'krituliai':[ 0,  3], \
                            'griaustinis':[ 6,  3]}, \
# delfi_lt
'delfi_lt':{'Clear sky':[0, 0, 0], \
                      'Fair':[1, 0, 0], \
                      'Partly cloudy':[2, 0, 0], \
                      'Cloudy':[3, 0, 0], \
                      'Rain showers':[2, 3, 3], \
                      'Light rain showers':[2, 3, 1], \
                      'Light sleet showers':[2, 0, 1], \
                      'Heavy rain showers':[2, 3, 5], \
                      'Snow showers':[2, -3, 3], \
                      'Sleet showers':[2, 0, 3], \
                      'Light sleet':[3, 0, 1], \
                      'Light rain':[3, 3, 1], \
                      'Light snow':[3, -3, 1], \
		      'Light snow showers':[2, -3, 1], \
                      'Rain':[3, 3, 3], \
                      'Snow':[3, -3, 3], \
                      'Heavy rain':[3, 3, 5], \
                      'Heavy snow':[3, -3, 5], \
		      'Heavy sleet':[3, -0, 5], \
		      'Heavy sleet showers':[3, -0, 5], \
                      'Sleet':[3, 0, 3]}, \
'uk_cloud':{'clear':[0], \
                      'sunny':[0], \
                       'mostly sunny':[0.5], \
                       'few clouds':[1], \
                       'partly fog':[1], \
                       'various clouds':[1.5], \
                       'cloudy':[2], \
                       'overcast':[3], \
                       'fog':[3]}, \
'uk_cond':{'light sleet':[0, 1], \
                     'sleet':[0, 3], \
                     'light snow':[-3, 1], \
                      'isolated snow showers':[-3, 1], \
                      'snow':[-3, 3], \
                      'snow showers':[-3, 3], \
                      'rain showers':[3, 3], \
                      'light rain':[3, 1], \
                      'isolated sleet showers':[0, 1], \
                      'isolated showers':[3, 1], \
                      'isolated showers and thunderstorms':[6, 1],\
                      'heavy showers and thunderstorms':[6, 5], \
                      'sleet showers':[0, 3], \
                      'rain':[3, 3], \
                      'freezing drizzle':[-1, 1], \
                      'freezing rain':[-1, 3], \
                      'showers':[3, 3], \
                      'showers and thunderstorms':[6, 3], \
                      'heavy showers':[3, 5] }}
                                
def prepare_ploting_conditions(DICT, SRC, ZERO_DAY_ORDINAL):
    if SRC=='gismeteo_lt' or SRC=='uk' or SRC=='delfi_lt' or SRC=='GFS50' or SRC =='WRF9' or SRC == 'WRF27':
        SIZE=np.min(len(DICT['EXTRA_COND']))
    else:
        SIZE=np.min([len(DICT['TEMP_DAY']), len(DICT['TEMP_NIGHT']), len(DICT['DATE'])])*2
    Y_DN=[]
    SYM_DN=[]
    CLR_DN=[]
    X=[]
    if SRC=='gismeteo_lt' or SRC=='uk' or SRC=='delfi_lt' or SRC=='meteo_lt':
        for date in DICT['DATE']:
            tdate=date.split('_')[0].split('-')
            if SRC=='gismeteo_lt' or SRC=='uk' or SRC=='delfi_lt':
                X.append( dt.date(int(tdate[0]), int(tdate[1]), int(tdate[2])).toordinal()-ZERO_DAY_ORDINAL )
                X.append( dt.date(int(tdate[0]), int(tdate[1]), int(tdate[2])).toordinal()-ZERO_DAY_ORDINAL+0.25 )
                X.append( dt.date(int(tdate[0]), int(tdate[1]), int(tdate[2])).toordinal()-ZERO_DAY_ORDINAL+0.5 )
                X.append( dt.date(int(tdate[0]), int(tdate[1]), int(tdate[2])).toordinal()-ZERO_DAY_ORDINAL+0.75 )
            else:
                X.append( dt.date(int(tdate[0]), int(tdate[1]), int(tdate[2])).toordinal()-ZERO_DAY_ORDINAL )
                X.append( dt.date(int(tdate[0]), int(tdate[1]), int(tdate[2])).toordinal()-ZERO_DAY_ORDINAL+0.5 )
    elif SRC=='GFS50' or SRC== 'WRF9' or SRC=='WRF27':
        tdate= DICT['DATE'][0].split('_')[0].split('-')
        SHIFT=dt.date(int(tdate[0]), int(tdate[1]), int(tdate[2])).toordinal()-ZERO_DAY_ORDINAL
        for X_DATE in DICT['EXTRA_DAY']:
            X.append(X_DATE+SHIFT)
    
    if SRC=='meteo_lt':
        for day_cnd, night_cnd in zip(DICT['COND_DAY'], DICT['COND_NIGHT']):
             Y_DN.append(MAP_COND[SRC][night_cnd][0])
             Y_DN.append(MAP_COND[SRC][day_cnd][0])
             
             CLR_DN.append(MAP_COND[SRC][night_cnd][1])
             CLR_DN.append(MAP_COND[SRC][day_cnd][1])
             
             SYM_DN.append(MAP_COND[SRC][night_cnd][2])
             SYM_DN.append(MAP_COND[SRC][day_cnd][2])
    elif SRC=='delfi_lt_less':
        for day_cnd, night_cnd in zip(DICT['COND_DAY'], DICT['COND_NIGHT']):
             Y_DN.append(MAP_COND[SRC][night_cnd][0])
             Y_DN.append(MAP_COND[SRC][day_cnd][0])
             
             CLR_DN.append(MAP_COND[SRC][night_cnd][1])
             CLR_DN.append(MAP_COND[SRC][day_cnd][1])
             
             SYM_DN.append(MAP_COND[SRC][night_cnd][2])
             SYM_DN.append(MAP_COND[SRC][day_cnd][2])
    elif SRC=='delfi_lt':
        for cnd in DICT['EXTRA_COND']:
             Y_DN.append(MAP_COND[SRC][cnd][0])
             CLR_DN.append(MAP_COND[SRC][cnd][1])
             SYM_DN.append(MAP_COND[SRC][cnd][2])
    elif SRC=='gismeteo_lt_less':
        for day_cnd, night_cnd in zip(DICT['COND_DAY'], DICT['COND_NIGHT']):
             day=day_cnd.split(', ')
             night=night_cnd.split(', ')
             Y_DN.append(MAP_COND[SRC+'_cloud'][night[0]][0])
             Y_DN.append(MAP_COND[SRC+'_cloud'][day[0]][0])
             if len(night) ==2:
                 CLR_DN.append(MAP_COND[SRC+'_cond'][night[1]][0])
                 SYM_DN.append(MAP_COND[SRC+'_cond'][night[1]][1])
             else:
                 CLR_DN.append(0)
                 SYM_DN.append(0)
                
             if len(day) ==2:
                 CLR_DN.append(MAP_COND[SRC+'_cond'][day[1]][0])
                 SYM_DN.append(MAP_COND[SRC+'_cond'][day[1]][1])
             else:
                 CLR_DN.append(0)
                 SYM_DN.append(0)
    elif SRC=='gismeteo_lt':
        for cnd in DICT['EXTRA_COND']:
             day=cnd.lower().split(', ')
             Y_DN.append(MAP_COND[SRC+'_cloud'][day[0]][0])
             if len(day) ==2:
                 print day
                 CLR_DN.append(MAP_COND[SRC+'_cond'][day[1]][0])
                 SYM_DN.append(MAP_COND[SRC+'_cond'][day[1]][1])
             elif len(day) == 1:
                 CLR_DN.append(0)
                 SYM_DN.append(0)
             elif len(day) >=3:
                if day[2] == 'griaustinis':
                    CLR_DN.append(MAP_COND[SRC+'_cond'][day[2]][0])
                    SYM_DN.append(MAP_COND[SRC+'_cond'][day[1]][1])
                else:
                    CLR_DN.append(MAP_COND[SRC+'_cond'][day[1]][0])
                    SYM_DN.append(MAP_COND[SRC+'_cond'][day[1]][1])
    elif SRC=='GFS50' or SRC== 'WRF9' or SRC=='WRF27':
        for cnd,  X_test in zip(DICT['EXTRA_COND'], X):
            if cnd[0] == '':
                Y_DN.append(0)
            else:
                Y_DN.append(cnd[0]*3./100.)
            CLR_DN.append(3)
            SYM_DN.append(cnd[1]*3.0)
             
    elif SRC=='uk_less':
        for day_cnd, night_cnd in zip(DICT['COND_DAY'], DICT['COND_NIGHT']):
             day=day_cnd.split(', ')
             night=night_cnd.split(', ')
             Y_DN.append(MAP_COND[SRC+'_cloud'][night[0]][0])
             Y_DN.append(MAP_COND[SRC+'_cloud'][day[0]][0])
             if len(night) ==2:
                 CLR_DN.append(MAP_COND[SRC+'_cond'][night[1]][0])
                 SYM_DN.append(MAP_COND[SRC+'_cond'][night[1]][1])
             else:
                 CLR_DN.append(0)
                 SYM_DN.append(0)
                
             if len(day) ==2:
                 CLR_DN.append(MAP_COND[SRC+'_cond'][day[1]][0])
                 SYM_DN.append(MAP_COND[SRC+'_cond'][day[1]][1])
             else:
                 CLR_DN.append(0)
                 SYM_DN.append(0)
    elif SRC=='uk':
        for cnd in DICT['EXTRA_COND']:
             day=cnd.split(', ')
             Y_DN.append(MAP_COND[SRC+'_cloud'][day[0]][0])
             if len(day) ==2:
                 CLR_DN.append(MAP_COND[SRC+'_cond'][day[1]][0])
                 SYM_DN.append(MAP_COND[SRC+'_cond'][day[1]][1])
             else:
                 CLR_DN.append(0)
                 SYM_DN.append(0)
    return np.array(X, dtype=np.float)[:SIZE],\
    np.array(Y_DN, dtype=np.float)[:SIZE],\
    np.array(CLR_DN, dtype=np.float)[:SIZE],\
    np.array(SYM_DN, dtype=np.float)[:SIZE]

def prepare_xticks(ZERO_DAY_ORDINAL, N_LEN):
    WEEK_NUM_2_DIENA={0:'Pir',1:'Ant',\
                                          2:'Tre',3:'Ket',\
                                          4:'Pen',5:'Ses', \
                                          6:'Sek'}
    XTICKS=[''] # dirty hack, because first label is skipped for unknown reason..
    zero_date=dt.date.fromordinal( ZERO_DAY_ORDINAL )
    for day in range(N_LEN):
        date=dt.date.fromordinal( ZERO_DAY_ORDINAL+day )
        XTICKS.append(WEEK_NUM_2_DIENA[date.weekday()]+'\n['+str(date.month)+'-'+str(date.day)+']')
    return XTICKS
    
def read_images_for_conditions():
    names=[item.split()[0] for item in open('img/list.txt')]
    images={}
    for name in names:
         images[name]=np.array(Image.open('img/'+name)).astype(np.float)/255
    return images
    
if __name__ =='__main__':
    extraxt()
