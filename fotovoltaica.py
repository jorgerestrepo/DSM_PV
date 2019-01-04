## Pendiente incluir la curva de carga en funciones fotovoltaica para poder colocar precios diferentes en las 24 horas
## Escenario inicial de comercial bajar el precio de energia a grandes comerciales ya que ellos tienen precios preferenciales
## Descomentar linea del incentivo ley 1715

import win32com.client
from numpy import *
from pylab import *
import matplotlib as mlp
#import pickle as pkl
#import requests as req
from datetime import datetime
#import json
import pylab as pl
import pandas as pd
from sklearn.utils import resample
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ColorConverter
import matplotlib.text as text
colorConverter = ColorConverter()
import re
from rpy2.robjects import r, pandas2ri
from funciones_fotovoltaica import *

mlp.style.use('ggplot')
mlp.rcParams['lines.linewidth'] = 2
mlp.rcParams['font.size'] = 12
mlp.rcParams['axes.facecolor'] = 'white'
mlp.rcParams['axes.grid'] = True
mlp.rcParams['grid.color'] = 'grey'


#CASO = 'RESIDENCIAL'
CASO = 'COMERCIAL'

# Encuesta Calidad de Vida 2015
[estrato_encuesta,estrato_percapita,tipo_vivienda,posesion_vivienda]=datos_encuesta_CV_2015()
print("SE PROCESARON LOS DATOS DE ENCUESTA DE CALIDAD DE VIDA")

if CASO == 'RESIDENCIAL':
    load_profiles = cargar_perfiles_demanda()
    df_agosto_nonduplicated = cargar_df_consumo()
    print("DATOS CARGADOS")
    clientes = df_agosto_nonduplicated.drop_duplicates(subset=['cliente'],keep='last')
    print(u'Indeces de clientes obtenidos')
    estrato_clientes = np.array([clientes['cliente'],clientes['estrato']])
    estrato_clientes = estrato_clientes.transpose()
    print(u'Estrato de los clientes obtenidos')
    # Se obtiene matrix unificada de id_cliente, perfil y estrato por día
    profiles_strata = matrix_id_cliente_profile_estrato(load_profiles,estrato_clientes)
    print(u'Se obtuvieron datos unificados de id_cliente, perfil y estrato')
    # Consumo promedio kWh/dia por estrato
    [consumo,desv_consumo,estrato_modelo] = consumo_promedio_diario(profiles_strata) ## Corregir porque la distribución de 
                                                                                     ## probabilidad no es normal
    # Se uso el promedio y la desviación estandar para considerar las variaciones entre diferentes clientes
    [consumo_medio_estrato,desv_consumo] = consumo_medio_estrato_func(estrato_modelo,consumo,desv_consumo,CASO)
elif CASO == 'COMERCIAL':
    load_profiles = cargar_perfiles_demanda_comercial()
    [consumo,desv_consumo,estrato_modelo] = consumo_promedio_diario_comercial(load_profiles)
    print(u'Se obtuvieron datos unificados de id_cliente, perfil y estrato')
    [consumo_medio_estrato,desv_consumo] = consumo_medio_estrato_func(estrato_modelo,consumo,desv_consumo,CASO)
    estrato_encuesta = np.zeros(estrato_encuesta.shape)
    

# Creación de matriz para el modelo de agentes
# |Estrato|Ingreso per capita|Tipo de vivienda|Tenencia Vivienda|Consumo_kWh_dia|
matriz_modelo = modelo_agentes(estrato_encuesta,
                               estrato_percapita,
                               tipo_vivienda,
                               posesion_vivienda,
                               consumo_medio_estrato,
                               desv_consumo,
                              CASO)
'''
energy = []
for n,x in enumerate(matriz_modelo[:,0]):
    if x==0:
        matriz_modelo[n,1]=float('inf')
        matriz_modelo[n,2]=0
        matriz_modelo[n,3]=1
    energy.append((np.random.normal(matriz_modelo[n,4],matriz_modelo[n,5]))*365)
    while energy[n] < 0:
        energy.append((np.random.normal(matriz_modelo[n,4],matriz_modelo[n,5]))*365)
'''     
## Se guarda la matriz modelo
matriz_modelo_original = matriz_modelo

if CASO == 'RESIDENCIAL':
    ## Se remuestrea para tener datos suficientes para ingresar a la simulación de OpenDSS
    matriz_modelo = resample(matriz_modelo, replace=True, n_samples=8500, random_state=1)

# Utility income modelo propio modificado
u_inc = []
for x in matriz_modelo[:,1]:
    u_inc.append((np.exp((x-np.mean(matriz_modelo[:,1]))/(10**3)))
                 /
                 (1+np.exp((x-np.mean(matriz_modelo[:,1]))/(10**3)))
                )
u_inc = np.array(u_inc)

# No existe un indicativo en las encuestas del tamaño de las viviendas de las personas, por lo que se considerara que desde que tenga vivienda propia, tipo casa el cliente buscara tener un balance de 0 kWh al mes
# Se usaron los datos de radiación solar de la Universidad Nacional de Colombia - LABI
## Promedio de radiación solar para generación fotovoltaica

radiacion = obtener_radiacion()
R_escenario  = np.mean(escenario_radiacion(radiacion,escenario='medio')) ## Calcula la radiación promedio
        
## Peak Power to be installed 
n_panel = (matriz_modelo[:,4]*1000)/(0.17*2*12*R_escenario) 
P_mpp = np.round(n_panel)*0.320 

## Potencia a instalar por cliente
#plt.plot(P_mpp);
#plt.ylim([0,5]);


# Años a evaluar 20
total_usuarios_pv = []
matriz_modelo_final = matriz_modelo
usuario_pv = np.zeros([matriz_modelo.shape[0],1])
user_pv_year=[]
for year_eval in xrange(20):
    print(u"EVALUANDO PERIODO {0}".format(year_eval))
    inflacion = 0.04
    ## Inversion = Potencia_instalar*(precio_kW_pv + precio_kw_inverter
    ## + Estructura + precio_adicionales_breakers_cable_etc +  mano_obra_utilidad)
    precio_kW_pv = 2300000*(1./(1+0.01*year_eval)) # Reducción en precio de los paneles cada año
    precio_kW_inverter = 1000000*(1-0.01*year_eval) # Reducción en precio de los inversores cada año
    precio_estructura = 350000*(1 + inflacion*year_eval) # Sube lo de la inflación
    precio_accesorios = 500000*(1 + inflacion*year_eval) # Sube lo de la inflación
    mano_obra_utilidad = 1000000*(1 + inflacion*year_eval) # Sube lo de la inflación
    Invest = P_mpp*(precio_kW_pv + precio_kW_inverter + precio_estructura + precio_accesorios + mano_obra_utilidad)

    abrasion = 1.2/100;
    E_pv = []
    for t in xrange(20):
        E_pv.append(1085.541*P_mpp*((1-abrasion)**t))
    E_pv = np.transpose(np.array(E_pv))

    # Precio completo a usuarios

    ## Precio energía por estrato
    ## Year es el año que se quiere evaluar
    ## Subsidy es el subsidio que depende de cada estrato y del consumo. Con E4 subsidy = 0
    ## La formula de precio se obtuvo mediante una regresión lineal usa la fecha en el formato entero de excel
    
    year_price = year_price_anual(year_eval,CASO)

    #Precio de bolsa para venta de excedentes de generación
    ## Se dejo un valor que va aumentando proporcionalmente 5% cada año
    bag_price = precio_bolsa(year_eval)
    

    # Calculo del ahorro por estrato al tener PV
    R_save = calculo_ahorro_PV(year_eval,E_pv,matriz_modelo,Invest,bag_price,year_price)

    # Incentivos Guvernamentales a consumo energía PV
    # Se asume un pago de un 5% extra por consumir su propia energía como incentivo por usar PV
    R_gov = E_pv*(0.05)*year_price

    # Se asumira la posibilidad de tener costos administrativos debido a la necesidad de actores
    # que permitan integrar los equipos de    generación en la red de distribución. Se dejara como un valor fijo

    # Se dejo como valor de administración un costo dependiendo de la producción de energía
    R_adm = E_pv*0.03*year_price

    # Costos de mantenimiento: Costo fijo anua

    ## Los costos de mantenimiento se expresan como un porcentaje de la inversión.
    R_man = []
    for x in Invest:
        R_man.append(np.ones(20)*x*0.015)
    R_man = np.concatenate(R_man).reshape(E_pv.shape[0],20)

    #Depreciacion anual

    ## Se deprecia un valor fijo anualmente hasta que el sistema alcanza un valor de cero despues de 20 años
    R_dep = []
    for x in Invest:
        R_dep.append(np.ones(20)*x/20.)
    R_dep = np.concatenate(R_dep).reshape(E_pv.shape[0],20)

    ## Con incentivos a pago por generación PV
    R = R_save + R_gov - R_adm - R_man - R_dep

    ## Sin incentivos a pago por generación PV
    R_ni = R_save - R_adm - R_man - R_dep

    # Se definio la tasa al mismo porcentaje que la inflación puede ser cambiada
    tasa = []
    for x in xrange(20):
        tasa.append((1+inflacion)**x)
    tasa = np.array(tasa)

    # Valor presente neto sin incentivos por consumir generación PV
    NPV = -Invest + np.sum(R_ni/tasa,axis=1)

    ## Se hallan los usuarios con un tiempo de retorno menor o igual a 10 años y se considera que estos instalaran paneles solares.
    ## Adicionalmente deben tener casa propia o estar pagando la casa propia (Se puede modificar solo para los de casa propia)
    ##        
#    usuario_pv = []
    #lista_borrar = []
    for y in xrange(Invest.shape[0]):
        for n,x in enumerate(np.cumsum(R_ni[y])):
            if matriz_modelo[y,3]==1: ## Si el usuario tiene casa propia. Si es comercial se considera que el valor es True
                if (x > Invest[y]) and (n <= 10) and (Invest[y] < matriz_modelo[y,1]*12): # Si la inversión retorna en 10 años o menos 
                    usuario_pv[y] = 1                                                  # y si se tiene la capacidad de inversión
                    #lista_borrar.append(y)
                    #matriz_modelo = np.delete(matriz_modelo, (y), axis=0)
                    #n_panel = (matriz_modelo[:,4]*1000)/(0.17*2*12*R_escenario) 
                    #P_mpp = np.round(n_panel)*0.320 
                    break
#        try:
#            usuario_pv[y]
#        except:
#            usuario_pv.append(0)
            
    #for x in lista_borrar:
    #    matriz_modelo = np.delete(matriz_modelo, (x), axis=0)
    usuario_pv = np.array(usuario_pv)
    print("El numero de usuarios en el año {0} que adoptan PV son {1}".format(year_eval,np.sum(usuario_pv)))
    user_pv_year.append(usuario_pv)
    

matriz_modelo_final = np.concatenate([matriz_modelo_final,usuario_pv.reshape(8500,1)],axis=1) ## Retorna el modelo con los que en 20 años o menos instalaran paneles fotovoltaicos

