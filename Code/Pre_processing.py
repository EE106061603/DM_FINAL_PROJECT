# -*- coding: utf-8 -*-
import pandas as pd
from glob import glob
import re, os
import pickle
def add_data ( target, other, key_name, no_month=False ) :
    d = []
    for x,y in zip(target.Date,target.COUNTYID) :
        try :
            if no_month : d.append(other[x[:3]][y])
            else : d.append(other[x][y])
        except :
            d.append(None)
    target[key_name] = d
    return target
data_othe = pd.read_excel('./Data/交通36_人口36_所得3.xlsx',header=None)
data_coun = pd.read_excel('./Data/Country_ID.xlsx')
country_dict = { x[0]:x[1] for x in data_coun.values.tolist()}
country_inverse_dict = { x[1]:x[0] for x in data_coun.values.tolist() }
def pd_clean ( path, data_othe=data_othe, data_coun=data_coun, country_dict=country_dict, country_inverse_dict=country_inverse_dict ) :
    d = pd.read_csv(path, encoding ='ansi',keep_default_na=True)
    useful = d[['COUNTYID','STATUS','SO2','CO','O3','PM10','PM25','NO2','WINDSPEED','WINDDIREC','DATACREATIONDATE']]
    print(os.path.basename(path)+' with length',d.shape[0],end=' ')
    useful = useful.dropna()
    print('=>',useful.shape[0],'add other data',end='=>')
    data_chem = useful.dropna()
    def chem_data_transform ( string ) : # transform '03-1月 -15' to '104-1'
        year_month = re.findall('\d+',string)[-2:][::-1]
        return year_month[0][0]+'0'+str(int(year_month[0][1])-1)+'-'+year_month[1]
    data_chem['Date'] = data_chem.DATACREATIONDATE.apply(lambda x: chem_data_transform(x))
    data_chem['Country'] = data_chem.COUNTYID.apply(lambda x: country_dict[x])
    # Processing of population, motocycles and money data
    data_othe['CountryID'] = data_othe[0].apply(lambda x: country_inverse_dict[x] )
    data_othe = data_othe.drop(columns=0)
    other=data_othe.values.tolist()
    other_population = {x[-1]:x[0:36] for x in other}
    other_moto = {x[-1]:x[36:72] for x in other}
    other_money = {x[-1]:x[72:-1] for x in other}
    info = pd.read_csv('month_info.txt',encoding='ansi',header=None,sep='\t')
    info = info.values.tolist()[0][1:]
    info = ['-'.join(re.findall('\d+',x)) for x in info ]
    info_population = info[0:36]
    info_moto = info[36:72]
    info_money = info[72:]
    data_population = pd.DataFrame.from_dict(other_population,orient='index',columns=info_population)
    data_moto = pd.DataFrame.from_dict(other_moto,orient='index',columns=info_moto)
    data_money = pd.DataFrame.from_dict(other_money,orient='index',columns=info_money)
    # Add population, motocycles and money data to polution data
    data_chem = add_data(data_chem,data_population,'Population')
    data_chem = add_data(data_chem,data_moto,'Veichle')
    data_chem = add_data(data_chem,data_money,'Income',True)
    # Clean data
    data_chem = data_chem.dropna()
    print(data_chem.shape[0])
    data_chem = data_chem[['COUNTYID', 'SO2', 'CO', 'O3', 'PM10', 'PM25', 'NO2',
           'WINDSPEED', 'WINDDIREC', 'Population', 'Veichle', 'Income', 'STATUS']]
    return data_chem
def combine_all ( path , operation=pd_clean ) :
    data = [ operation(path[0]) ]
    data_new = [ operation(path[_]) for _ in range(1,len(path)) ]
    data = data + data_new
    data_all = pd.concat(data)
    return data_all
#%% Read data
r = glob('./Data/*.csv')
file = [  os.path.basename(i) for i in r ]
#%% Combine all with simple data processing
data_all = combine_all(r)
with open('clean_data.pkl','wb') as fw :
    pickle.dump(data_all,fw)
#%% 標籤處理
with open('clean_data.pkl','rb') as fr :
    data_chem = pickle.load(fr)
print(set(data_chem.STATUS),data_chem.shape[0])
data_chem = data_chem.replace('非常不健康','非常不良')
data_chem = data_chem.replace('對所有族群不健康','非常不良')
data_chem = data_chem.replace('對所有族群不良','不良')
data_chem = data_chem.replace('危害','非常不良')
data_chem = data_chem.replace('有害','不良')
data_chem = data_chem.replace('設備維護',' ')
data_chem = data_chem[data_chem.STATUS!=' ']
print(set(data_chem.STATUS),data_chem.shape[0])
with open('clean_data_v2.pkl','wb') as fw :
    pickle.dump(data_chem,fw)
#%% 標準化
#%% 標準化
for key in data_chem.columns[:-1] :
    data_chem[key] = (data_chem[key]-data_chem[key].mean())/(data_chem[key].var()**.5)
with open('data_normal_v3.pkl','wb') as fw :
    pickle.dump(data_chem,fw)
