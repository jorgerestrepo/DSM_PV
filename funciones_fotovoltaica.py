from numpy import *
from pylab import *
import matplotlib as mlp
import pickle as pkl
import requests as req
from datetime import datetime
from datetime import timedelta 
import json
import pylab as pl
import pandas as pd
from sklearn.utils import resample
import re
from rpy2.robjects import r, pandas2ri

pandas2ri.activate()

def curva_radiacion_solar(radiacion_test):
    curva_radiacion={}
    for n,x in enumerate(radiacion_test['Hora'].unique()):
        if x in curva_radiacion.keys():
            temporal=radiacion_test.loc[radiacion_test['Hora']==x]
            curva_radiacion[x].append(temporal['Radiacion'].values)
        else:
            curva_radiacion[x]=[]
            temporal=radiacion_test.loc[radiacion_test['Hora']==x]
            curva_radiacion[x].append(temporal['Radiacion'].values)
    return curva_radiacion

def niveles_radiacion_percentile(curva_radiacion,percentile):
    radiacion_percentile=[]
    for x in curva_radiacion.keys():
        if (x > 4) and (x < 19):
            radiacion_percentile.append(np.percentile(curva_radiacion[x],percentile))
    radiacion_percentile=np.array(radiacion_percentile)
    return radiacion_percentile

def escenario_radiacion(radiacion,escenario='medio'):
    radiacion1=np.array(radiacion[0])
    for n,x in enumerate(radiacion):
        if x>0:
            radiacion1 = np.append(radiacion1,x,axis=0)
    radiacion_test={}
    radiacion_test['Fecha']=radiacion1[:,0]
    radiacion_test['Radiacion']=radiacion1[:,1]
    radiacion_test=pd.DataFrame(radiacion_test)
    radiacion_test['Fecha']=radiacion_test['Fecha'].values-np.timedelta64('5', 'h')
    radiacion_test['Fecha']=pd.DatetimeIndex(radiacion_test['Fecha'])
    dates=pd.DatetimeIndex(radiacion_test['Fecha'])
    radiacion_test['Hora']=dates.hour
    curva_radiacion=curva_radiacion_solar(radiacion_test)
    if escenario=='bajo':
        escenario_radiacion = niveles_radiacion_percentile(curva_radiacion,25)
    elif escenario=='medio':
        escenario_radiacion = niveles_radiacion_percentile(curva_radiacion,50)
    elif escenario=='alto':
        escenario_radiacion = niveles_radiacion_percentile(curva_radiacion,75)
    else:
        raise ValueError('Solo puede ingresarse escenario bajo, medio o alto. Otro valor genera error')
    return escenario_radiacion

def cargar_perfiles_demanda():
    # Carga Perfiles de carga
    load_profiles = pkl.load(open( "C:\\Users\\Administrador\\JORGE\\Paper_DSM_Profe_Sandra\\load_profiles_by_day_cluster0.pkl",
                                  "rb"))
    load_profiles = np.append(load_profiles,pkl.load(open("C:\\Users\\Administrador\\JORGE\\"+
                                      "Paper_DSM_Profe_Sandra\\load_profiles_by_day_cluster1.pkl", "rb")),axis=0)
    load_profiles = np.append(load_profiles,pkl.load(open("C:\\Users\\Administrador\\JORGE\\"+
                                      "Paper_DSM_Profe_Sandra\\load_profiles_by_day_cluster2.pkl", "rb")),axis=0)
    load_profiles = np.append(load_profiles,pkl.load(open("C:\\Users\\Administrador\\JORGE\\"+
                                      "Paper_DSM_Profe_Sandra\\load_profiles_by_day_cluster3.pkl", "rb")),axis=0)
    load_profiles = np.append(load_profiles,pkl.load(open("C:\\Users\\Administrador\\JORGE\\"+
                                      "Paper_DSM_Profe_Sandra\\load_profiles_by_day_cluster4.pkl", "rb")),axis=0)
    load_profiles = np.append(load_profiles,pkl.load(open("C:\\Users\\Administrador\\JORGE\\"+
                                      "Paper_DSM_Profe_Sandra\\load_profiles_by_day_cluster5.pkl", "rb")),axis=0)
    return load_profiles

def obtener_radiacion():
    radiacion = []
    headers = {'X-Requested-With':'',
               'User-Agent':'Ciencias_Naturales',
               'Authorization':'Basic QWRtaW5pc3RyYWRvcjpFTSZEX1NlcnZlcg==',
               'Host':'168.176.26.208'}
    webID = ("A0E-qeMCkAjBkyG0M8q4fVEngG71Gadqy5xGUT5y2VAxwZQ9"+
             "_vSJY1Hy1ADqq7fKrdQhwTEFCSS1NQUlOLUFGXEFGX1NFUlZ"+
             "FUlwxMDNfQ0FNUFVTQk9HX0VNX1wwMV9NRURJQ0lOQXxfU09MQVJSQUQ")
    
    maxCount = '150000' #Cantidad maxima de puntos a extraer
    
    startTime = datetime(2017,1,24)
    endTime  = startTime+timedelta(days=120)
    endTime1 = datetime.now()
    if endTime > endTime1:
        endTime = endTime1
    
    while startTime+timedelta(minutes=10)< datetime.now():     
        url = ('https://168.176.26.208/piwebapi/streams/'+webID+
               '/recorded?'+'startTime='+str(startTime.strftime("%Y-%m-%d %H:%M:%S"))+
               '&endTime='+str(endTime.strftime("%Y-%m-%d %H:%M:%S")) +'&maxCount='+maxCount)
        print(url)
        r = req.get(url,
                    headers=headers,
                    verify=False)
        data = json.loads(r.content)
        radiacion.append(([[datetime.strptime(x['Timestamp'][:19],
                                              '%Y-%m-%dT%H:%M:%S'),
                            x['Value']] if isinstance(x['Value'],float) else [datetime.strptime('2018-09-13T00:00:00.000000',
                                                                                                '%Y-%m-%dT%H:%M:%S.%f'),
                                                                              float('NaN')] for x in data['Items']]))
        startTime = endTime
        endTime  = startTime+timedelta(days=120)
        endTime1 = datetime.now()
        if endTime > endTime1:
            endTime = endTime1
    '''
    radiacion_values=[]
    for x in np.array(radiacion)[:,1]:
        if isnan(x):
            continue
        else:
            radiacion_values.append(x)
    '''
    return radiacion

def datos_bogota():
    filename = u"C:/Users/Administrador/JORGE/Encuesta Calidad de Vida 2015/Datos de la vivienda/Datos de la vivienda.sav"
    car_vivienda = r('foreign::read.spss("%s", to.data.frame=TRUE)' % filename)
    bogota=car_vivienda.loc[car_vivienda["P1_DEPARTAMENTO"]=="Bogota D.C"]
    bogota=bogota.drop(["REGION_BUENAVENTURA"],axis=1)
    bogota_cabecera=bogota.loc[bogota["P3"]=="Cabecera"]
    bogota_index=bogota_cabecera["DIRECTORIO"]
    return bogota_index,bogota_cabecera

def estrato_clientes(bogota_cabecera):
    estrato_encuesta=[]
    for x in bogota_cabecera["P8520S1A1"].tolist():
        if x == '0 - Recibos sin estrato o el servicio es pirata':
            estrato_encuesta.append(0)
        elif x == '1 - Bajo - bajo':
            estrato_encuesta.append(1)
        elif x == '2 - Bajo':
            estrato_encuesta.append(2)
        elif x == '3 - Medio - bajo':
            estrato_encuesta.append(3)
        elif x == '4 - Medio':
            estrato_encuesta.append(4)
        elif x == '5 - Medio - alto':
            estrato_encuesta.append(5)
        elif x == '6 - Alto':
            estrato_encuesta.append(6)
        else:
            continue
    estrato_encuesta = np.array(estrato_encuesta)
    return estrato_encuesta

def datos_servicios_hogar(bogota_index,estrato_encuesta):
    filename = u"C:/Users/Administrador/JORGE/Encuesta Calidad de Vida 2015/Servicios del hogar/Servicios del hogar.sav"
    servicios_hogar = r('foreign::read.spss("%s", to.data.frame=TRUE)' % filename)
    servicios_hogar.set_index("DIRECTORIO", inplace=True)
    servicios_hogar1 = servicios_hogar.loc[bogota_index]
    servicios_hogar = servicios_hogar1[~servicios_hogar1.index.duplicated(keep='first')]

    estrato_percapita = np.concatenate((estrato_encuesta.reshape(len(estrato_encuesta),1),
                    servicios_hogar["PERCAPITA"].as_matrix().reshape(len(servicios_hogar["PERCAPITA"]),1)),
                   axis=1
                  )

    # Se obtiene el ingreso total

    estrato_ingreso = np.concatenate((estrato_encuesta.reshape(len(estrato_encuesta),1),
                    servicios_hogar["I_HOGAR"].as_matrix().reshape(len(servicios_hogar["I_HOGAR"]),1)),
                   axis=1
                  )

    # Se obtiene el ingreso total de la unidad de gasto.

    estrato_gasto = np.concatenate((estrato_encuesta.reshape(len(estrato_encuesta),1),
                    servicios_hogar["I_UGASTO"].as_matrix().reshape(len(servicios_hogar["I_UGASTO"]),1)),
                   axis=1
                  )


    #Numero de personas en promedio por hogar por estrato

    numero_personas = (np.append(estrato_encuesta.reshape(len(estrato_encuesta),1),
                                 servicios_hogar['CANT_PERSONAS_HOGAR'].
                                 as_matrix().
                                 reshape(len(servicios_hogar['CANT_PERSONAS_HOGAR']),1),axis=1))
    
    return estrato_percapita,estrato_ingreso,estrato_gasto,numero_personas

def tenencia_hogar(bogota_index):
    #Tenencia y financiacion del hogar

    filename = (u"C:/Users/Administrador/JORGE/"+
                u"Encuesta Calidad de Vida 2015/"+
                u"Tenencia y financiacion de la vivienda que ocupa el hogar/"+
                u"Tenencia y financiacion de la vivienda que ocupa el hogar.sav")
    tenencia_hogar = r('foreign::read.spss("%s", to.data.frame=TRUE)' % filename)
    tenencia_hogar.set_index("DIRECTORIO", inplace=True)
    tenencia_hogar1 = tenencia_hogar.loc[bogota_index]
    tenencia_hogar = tenencia_hogar1[~tenencia_hogar1.index.duplicated(keep='first')]

    posesion_vivienda = []
    for x in tenencia_hogar['P5095']:
        if (x == "Propia, totalmente pagada") or (x =='Propia, lo est\xe1n pagando'):
            posesion_vivienda.append(1)
        else:
            posesion_vivienda.append(0)
        '''
        elif x =='En arriendo o subarriendo':
            posesion_vivienda.append(0)
        elif x =='Con permiso del propietario, sin pago alguno (usufructuario)':
            posesion_vivienda.append(2)

        '''
    posesion_vivienda = np.array(posesion_vivienda).reshape(len(posesion_vivienda),1)

    # Viviendas propias Pagadas
    # Dato de gran importancia debido a que solo los usuarios que cuentan con una vivienda propia
    # pagada tomarian en cuenta hacer una inversion en PV

    print("{0}% de las viviendas son propias ya pagadas".
          format(np.where(np.array(posesion_vivienda)==1)[0].shape[0]/double(len(posesion_vivienda))*100))
    
    return posesion_vivienda

def regresar_tipo_vivienda(bogota_index):
    # Tipo de vivienda

    filename = u"C:/Users/Administrador/JORGE/Encuesta Calidad de Vida 2015/Datos de la vivienda/Datos de la vivienda.sav"
    datos_vivienda = r('foreign::read.spss("%s", to.data.frame=TRUE)' % filename)
    datos_vivienda.set_index("DIRECTORIO", inplace=True)
    datos_vivienda1 = datos_vivienda.loc[bogota_index]
    datos_vivienda = datos_vivienda1[~datos_vivienda1.index.duplicated(keep='first')]

    tipo_vivienda = []
    for x in datos_vivienda['P1070']:
        if x == "Casa":
            tipo_vivienda.append(0)
        elif x =='Apartamento':
            tipo_vivienda.append(1)
        elif x =='Cuarto(s)':
            tipo_vivienda.append(2)
        else:
            tipo_vivienda.append(3)
    tipo_vivienda = np.array(tipo_vivienda).reshape(len(tipo_vivienda),1)
    
    return tipo_vivienda

def datos_encuesta_CV_2015():
    [bogota_index,bogota_cabecera] = datos_bogota()
    ## Estrato del cliente
    estrato_encuesta = estrato_clientes(bogota_cabecera)
    # Se obtiene el ingreso per-capita por estrato
    [estrato_percapita,estrato_ingreso,estrato_gasto,numero_personas]=datos_servicios_hogar(bogota_index,estrato_encuesta)                 
    
    posesion_vivienda=tenencia_hogar(bogota_index)
    tipo_vivienda=regresar_tipo_vivienda(bogota_index)
    
    return estrato_encuesta,estrato_percapita,tipo_vivienda,posesion_vivienda

def cargar_df_consumo():
    # Obtener estratos e identificacion de usuarios
    try:
        df_agosto_nonduplicated=pd.read_pkl('./df_agosto_nonduplicated.pkl')
    except:
        df_agosto = pd.read_csv('C:\\Users\\Administrador\\Datos_Consumo_Energia_PAIS\\medicion_inteligente\\'+
                                '03_ENEL\\2017-08_Agosto.csv',
                                header=0,
                                names=['cliente',
                                       'municipio',
                                       'localidad',
                                       'estrato',
                                       'fecha_hora',
                                       'valor',
                                       'estado'],
                                sep=";")
        df_agosto_nonduplicated = df_agosto.drop_duplicates(subset=['cliente', 'fecha_hora'], keep='last')
        df_agosto_nonduplicated.to_pickle('./df_agosto_nonduplicated.pkl')
    return df_agosto_nonduplicated

def matrix_id_cliente_profile_estrato(load_profiles,estrato_clientes):
    clientes_Cluster= load_profiles[:,0]
    estrato=[]
    for x in clientes_Cluster:
        estrato.append(estrato_clientes[np.where(estrato_clientes[:,0]==x),1][0][0])
    estrato = np.array(estrato).reshape(len(estrato),1)
    profiles_strata = np.concatenate((load_profiles,estrato),axis=1)
    return profiles_strata

def consumo_promedio_diario(profiles_strata):
    consumo = []
    desv_consumo = []
    estrato_modelo = []
    for x in np.unique(profiles_strata[:,0]):
        usuario = np.where(profiles_strata[:,0] == x)
        estrato_modelo.append(profiles_strata[usuario,25][0][0])
        #if profiles_strata[usuario,25][0][0] == 0:
        #    consumo.append(np.mean(np.sum(profiles_strata[usuario,1:25],axis=1))*1000)
        #else:
        #    consumo.append(np.mean(np.sum(profiles_strata[usuario,1:25],axis=1)))
        consumo.append(np.mean(np.sum(profiles_strata[usuario,1:25],axis=1)))
        desv_consumo.append(np.std(np.sum(profiles_strata[usuario,1:25],axis=1)))
    consumo = np.array(consumo)
    desv_consumo = np.array(desv_consumo)
    estrato_modelo = np.array(estrato_modelo)
    return consumo, desv_consumo, estrato_modelo

def consumo_medio_estrato_func(estrato_modelo,consumo,desv_consumo,escenario):
    if escenario == 'RESIDENCIAL':  
        consumo_medio_estrato = []
        desv_consumo = []
        for x in np.unique(estrato_modelo):
            indexes = np.where(estrato_modelo==x)[0]
            consumo_medio_estrato.append(np.mean(consumo[indexes]))
            desv_consumo.append(np.std(consumo[indexes]))
        consumo_medio_estrato = np.array(consumo_medio_estrato)/1000.
        desv_consumo = np.array(desv_consumo)/1000.
    elif escenario == 'COMERCIAL':
        consumo_medio_estrato = []
        desv_consumo = []
        consumo_medio_estrato.append(np.mean(consumo))
        desv_consumo.append(np.std(consumo))
        consumo_medio_estrato = np.array(consumo_medio_estrato)
        desv_consumo = np.array(desv_consumo)
    return consumo_medio_estrato,desv_consumo

def modelo_agentes(estrato_encuesta,
                   estrato_percapita,
                   tipo_vivienda,
                   posesion_vivienda,
                   consumo_medio_estrato,
                   desv_consumo,escenario):
    if escenario == 'RESIDENCIAL':
        matriz_modelo = np.concatenate([estrato_encuesta.reshape(len(estrato_encuesta),1),
                                    estrato_percapita[:,1].reshape(len(estrato_encuesta),1),
                                    tipo_vivienda,
                                    posesion_vivienda],
                                   axis=1)
        consumo = []
        desviacion_consumo = []
        for x in matriz_modelo[:,0]:
            consumo.append(consumo_medio_estrato[int(x)])
            desviacion_consumo.append(desv_consumo[int(x)])
        consumo = np.array(consumo).reshape(len(consumo),1)
        desviacion_consumo = np.array(desviacion_consumo).reshape(len(desviacion_consumo),1)
        matriz_modelo = np.concatenate([matriz_modelo,
                                        consumo,
                                       desviacion_consumo],
                                       axis=1)
    elif escenario == 'COMERCIAL':
        matriz_modelo = np.concatenate([estrato_encuesta.reshape(len(estrato_encuesta),1),
                                    estrato_percapita[:,1].reshape(len(estrato_encuesta),1),
                                    tipo_vivienda,
                                    posesion_vivienda],
                                   axis=1)
        consumo = []
        desviacion_consumo = []
        for x in matriz_modelo[:,0]:
            consumo.append(consumo_medio_estrato[0])
            desviacion_consumo.append(desv_consumo[0])
        consumo = np.array(consumo).reshape(len(consumo),1)
        desviacion_consumo = np.array(desviacion_consumo).reshape(len(desviacion_consumo),1)
        matriz_modelo = np.concatenate([matriz_modelo,
                                        consumo,
                                       desviacion_consumo],
                                       axis=1)
    return matriz_modelo

def excel_date(date1):
        temp = datetime(1899, 12, 30)    # Note, not 31st Dec but 30th!
        delta = date1 - temp
        return float(delta.days) + (float(delta.seconds) / 86400)
    
def year_price_anual(year_eval,escenario):
    year_price = []
    for x in xrange(20):
        year = excel_date(datetime(x+2018+year_eval, 1, 1, 0, 0,0))
        year_price.append((0.0695*year-2523.8))
    year_price = np.array(year_price)
    if (escenario == 'COMERCIAL'):
        year_price = year_price*0.7873 #El precio de la energia para usuarios comerciales a 34.5 kV es mejor.
    return year_price

def precio_bolsa(year_eval):
    bag_price = np.ones(20)
    for x in xrange(20):
        bag_price[x] = 200*(1+0.052*(x+year_eval))
    return bag_price

def ahorro_estrato_1(matriz_modelo,bag_price,E_pv,year_price,x):
    # Modelo para generar a partir de los datos existentes un consumo mensual
    energy = (np.random.normal(matriz_modelo[x,4],matriz_modelo[x,5]))*365
    while energy < 0:
        energy = (np.random.normal(matriz_modelo[x,4],matriz_modelo[x,5]))*365
    ## Si el consumo es menor al de subsistencia
    ## Consumo de subsistencia al ano es 130*12 para la ciudad de Bogota. 
    ## 130 kWh subsidiados cada mes
    if energy<130*12:
        # Si la generacion mensual es menor a la energia consumida
        if E_pv[x:0]<energy:
            ahorro = ((E_pv[x,:]*year_price*0.5))
        else:
        # En caso de que la generacion mensual es mayor a la energia consumida
            ahorro = (((E_pv[x,:]-np.ones(E_pv[x,:].shape)*energy)*bag_price)+
                                 (np.ones(E_pv[x,:].shape)*(energy*year_price*0.5))
                         )
    ## Si el consumo es mayor al de subsistencia
    else:
        ## Caso donde la generacion no supera el consumo, 
        ##pero cubre todo lo no subsidiado y una parte del subsidiado
        if ((E_pv[x,0]<energy) and (energy - E_pv[x,0] <= 130*12)):
            no_subsidiado = energy - 130*12
            subsidiado = E_pv[x,0] - no_subsidiado
            ahorro = (
                (np.ones(E_pv[x].shape)*no_subsidiado)*year_price +
                (np.ones(E_pv[x].shape)*subsidiado)*year_price*0.5
                         )
        ## Caso donde la generacion no supera el consumo y no cubre lo subsidiado
        elif ((E_pv[x,0]<energy) and (energy - E_pv[x,0] > 130*12)):
            ahorro = (
                (E_pv[x]*year_price)
                         )
        else:
        ## Caso donde la generacion cubre todo lo consumido y puede o no exportar energia
            ahorro = (
                ((E_pv[x]-np.ones(E_pv[x].shape)*energy)*bag_price)+
                ((np.ones(E_pv[x].shape)*energy*year_price*0.5))
            )
    return ahorro

def ahorro_estrato_2(matriz_modelo,bag_price,E_pv,year_price,x):
    # Modelo para generar a partir de los datos existentes un consumo mensual
    energy = (np.random.normal(matriz_modelo[x,4],matriz_modelo[x,5]))*365
    while energy < 0:
        energy = (np.random.normal(matriz_modelo[x,4],matriz_modelo[x,5]))*365
    ## Si el consumo es menor al de subsistencia
    ## Consumo de subsistencia al ano es 130*12 para la ciudad de Bogota. 
    ## 130 kWh subsidiados cada mes
    if energy<130*12:
        # Si la generacion mensual es menor a la energia consumida
        if E_pv[x:0]<energy:
            ahorro = ((E_pv[x,:]*year_price*0.6))
        else:
        # En caso de que la generacion mensual es mayor a la energia consumida
            ahorro = (
                ((E_pv[x,:]-np.ones(E_pv[x,:].shape)*energy)*bag_price)+
                (np.ones(E_pv[x,:].shape)*energy*year_price*0.6)
            )
    ## Si el consumo es mayor al de subsistencia
    else:
        ## Caso donde la generacion no supera el consumo, 
        ## pero cubre todo lo no subsidiado y una parte del subsidiado
        if ((E_pv[x,0]<energy) and (energy - E_pv[x,0] <= 130*12)):
            no_subsidiado = energy - 130*12
            subsidiado = E_pv[x,0] - no_subsidiado
            ahorro = (
                (np.ones(E_pv[x].shape)*no_subsidiado)*year_price +
                (np.ones(E_pv[x].shape)*subsidiado)*year_price*0.6
                         )
        ## Caso donde la generacion no supera el consumo y no cubre lo subsidiado
        elif ((E_pv[x,0]<energy) and (energy - E_pv[x,0] > 130*12)):
            ahorro = (
                (E_pv[x]*year_price)
            )
        else:
        ## Caso donde la generacion cubre todo lo consumido y puede o no exportar energia
            ahorro = (
                ((E_pv[x]-np.ones(E_pv[x].shape)*energy)*bag_price)+
                ((np.ones(E_pv[x].shape)*energy*year_price*0.6))
            )
    return ahorro

def ahorro_estrato_3(matriz_modelo,bag_price,E_pv,year_price,x):
    # Modelo para generar a partir de los datos existentes un consumo mensual
    energy = (np.random.normal(matriz_modelo[x,4],matriz_modelo[x,5]))*365
    while energy < 0:
        energy = (np.random.normal(matriz_modelo[x,4],matriz_modelo[x,5]))*365
    ## Si el consumo es menor al de subsistencia
    ## Consumo de subsistencia al ano es 130*12 para la ciudad de Bogota. 
    ## 130 kWh subsidiados cada mes
    if energy<130*12:
        # Si la generacion mensual es menor a la energia consumida
        if E_pv[x:0]<energy:
            ahorro = ((E_pv[x,:]*year_price*0.85))
        else:
        # En caso de que la generacion mensual es mayor a la energia consumida
            ahorro = (((E_pv[x,:]-np.ones(E_pv[x,:].shape)*energy)*bag_price)+
                                 (np.ones(E_pv[x,:].shape)*(energy*year_price*0.85))
                         )
    ## Si el consumo es mayor al de subsistencia
    else:
        ## Caso donde la generacion no supera el consumo,
        ## pero cubre todo lo no subsidiado y una parte del subsidiado
        if ((E_pv[x,0]<energy) and (energy - E_pv[x,0] <= 130*12)):
            no_subsidiado = energy - 130*12
            subsidiado = E_pv[x,0] - no_subsidiado
            ahorro = (
                (np.ones(E_pv[x].shape)*no_subsidiado)*year_price +
                (np.ones(E_pv[x].shape)*subsidiado)*year_price*0.85
            )
        ## Caso donde la generacion no supera el consumo y no cubre lo subsidiado
        elif ((E_pv[x,0]<energy) and (energy - E_pv[x,0] > 130*12)):
            ahorro = (
                (E_pv[x]*year_price)
            )
        else:
        ## Caso donde la generacion cubre todo lo consumido y puede o no exportar energia
            ahorro = (
                ((E_pv[x]-np.ones(E_pv[x].shape)*energy)*bag_price)+
                ((np.ones(E_pv[x].shape)*energy*year_price*0.85))
            )
    return ahorro

def ahorro_estrato_4(matriz_modelo,bag_price,E_pv,year_price,x):
    energy = (np.random.normal(matriz_modelo[x,4],matriz_modelo[x,5]))*365
    while energy < 0:
        energy = (np.random.normal(matriz_modelo[x,4],matriz_modelo[x,5]))*365
    if E_pv[x,0] <= energy:
        ahorro = (E_pv[x,:]*year_price)
    else:
        ahorro = (
            (E_pv[x,:]-np.ones(E_pv[x,:].shape)*energy)*bag_price+
            (np.ones(E_pv[x,:].shape)*energy*year_price)
            )
    return ahorro

def ahorro_estrato_5_6(matriz_modelo,bag_price,E_pv,year_price,x, Invest):
    energy = (np.random.normal(matriz_modelo[x,4],matriz_modelo[x,5]))*365
    while energy < 0:
        energy = (np.random.normal(matriz_modelo[x,4],matriz_modelo[x,5]))*365
    if E_pv[x,0] <= energy:
        ahorro = (E_pv[x,:]*year_price*1.2)
    else:
        ahorro = (
            (E_pv[x,:]-np.ones(E_pv[x,:].shape)*energy)*bag_price+
            (np.ones(E_pv[x,:].shape)*energy*year_price*1.2)
    )
    ## Incentivo ley 1715 se devuelve en declaracion de renta el 50% de una inversion en PV
    Invest[x] = Invest[x]/2.  
    return ahorro, Invest

def ahorro_usuario_comercial(matriz_modelo,bag_price,E_pv,year_price,x, Invest):
    energy = (np.random.normal(matriz_modelo[x,4],matriz_modelo[x,5]))*365
    while energy < 0:
        energy = (np.random.normal(matriz_modelo[x,4],matriz_modelo[x,5]))*365
    ahorro = (
        (E_pv[x,:]-np.ones(E_pv[x,:].shape)*energy)*bag_price+
        (np.ones(E_pv[x,:].shape)*energy*year_price*1.2)
        )
    ## Por economia de escala el precio del sistema es menor ($/W)
    if matriz_modelo[x,4]>1900: # Se escoge 1900 como limite a partir de los resultados de clustering.
        print(u'Por economia de escala al cliente {0} se reduce el costo en 34%'.format(x))
        Invest[x] = Invest[x]*0.66
    ## Incentivo ley 1715 se devuelve en declaracion de renta el 50% de una inversion en PV  
    ## Invest[x] = Invest[x]/2. # Comentar esta linea para quitar el incentivo de Ley 
    return ahorro, Invest

def calculo_ahorro_PV(year_eval,E_pv,matriz_modelo,Invest,bag_price,year_price):
    R_save =[]
    for x in xrange(E_pv.shape[0]):
        # ESTRATO 1
        if matriz_modelo[x,0]==1:
            ahorro = ahorro_estrato_1(matriz_modelo,bag_price,E_pv,year_price,x)
            R_save.append(ahorro)
        # ESTRATO 2
        elif matriz_modelo[x,0]==2:
            ahorro = ahorro_estrato_2(matriz_modelo,bag_price,E_pv,year_price,x)
            R_save.append(ahorro)
        # ESTRATO 3
        elif matriz_modelo[x,0]==3:
            ahorro = ahorro_estrato_3(matriz_modelo,bag_price,E_pv,year_price,x)
            R_save.append(ahorro)
        # ESTRATO 4
        elif matriz_modelo[x,0]==4:
            ahorro = ahorro_estrato_4(matriz_modelo,bag_price,E_pv,year_price,x)
            R_save.append(ahorro)
        # ESTRATO 5 y ESTRATO 6
        elif matriz_modelo[x,0]==5 or matriz_modelo[x,0]==6:
            [ahorro, Invest] = ahorro_estrato_5_6(matriz_modelo,bag_price,E_pv,year_price,x, Invest)
            R_save.append(ahorro)
        # USUARIO COMERCIAL
        elif matriz_modelo[x,0]==0:
            [ahorro, Invest]=ahorro_usuario_comercial(matriz_modelo,bag_price,E_pv,year_price,x, Invest)
            R_save.append(ahorro)
        else:
            R_save.append(np.zeros(20))
    R_save = np.concatenate(R_save).reshape([E_pv.shape[0],20])
    return R_save

### Funciones solo para comerciales

def cargar_perfiles_demanda_comercial():
    profiles_strata = pd.read_pickle("C:\\Users\\Administrador\\Datos_Consumo_Energia_PAIS"+
                                     "\\medicion_inteligente\\04_EPSA\\var\\july_profiles")
    return profiles_strata
def consumo_promedio_diario_comercial(profiles_strata):
    july_user = pd.read_pickle("C:\\Users\\Administrador\\Datos_Consumo_Energia_PAIS"+
                                     "\\medicion_inteligente\\04_EPSA\\var\\july_user")
    july_user = np.array(july_user)
    consumo = []
    desv_consumo = []
    estrato_modelo = []
    for p,x in enumerate(july_user):
        if ((x[1] != 'Residencial Estrato 1') and 
            (x[1] != 'Residencial Estrato 2') and 
            (x[1] != 'Residencial Estrato 3') and
            (x[1] != 'Residencial Estrato 4') and
            (x[1] != 'Residencial Estrato 5') and
            (x[1] != 'Residencial Estrato 6') and
            (x[1] != 'nan') and
            (x[1] != 'ELIMINAR')
           ):
            try:
                n = np.where(x[0]==np.array(profiles_strata['X_idx']))[0][0]
                estrato_modelo.append(0)
                consumo.append(np.mean(np.sum(profiles_strata['X_train'][n],axis=1)))
                desv_consumo.append(np.std(np.sum(profiles_strata['X_train'][n],axis=1)))
            except:
                print("El usuario {0} no se encuentra dentro de las medidas".format(x[0]))
    consumo = np.array(consumo)
    desv_consumo = np.array(desv_consumo)
    estrato_modelo = np.array(estrato_modelo)
    return consumo, desv_consumo, estrato_modelo