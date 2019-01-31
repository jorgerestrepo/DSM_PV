import sys
sys.path.append("C:\\Program Files (x86)\\DIgSILENT\\PowerFactory 15.1\\python")
import pickle as pkl
#import matplotlib
#import matplotlib.pyplot as plt
import powerfactory
app=powerfactory.GetApplication()
user = app.GetCurrentUser()
project=app.ActivateProject('SA15')
prj = app.GetActiveProject()

#scenary = app.GetActiveScenario()
#print(scenary.loc_name)
#active_grid = app.GetActiveGrids()
#print(active_grid.loc_name)
#elemento_area = app.GetCalcRelevantObjects("*.ElmArea")
#for x in elemento_area:
#    print(x.loc_name)

ldf=app.GetFromStudyCase("ComLdf")
Lines=app.GetCalcRelevantObjects("*.ElmLne")
cargas = app.GetCalcRelevantObjects("*.ElmLod")
ldf.Execute()
datos = {}
datos['Name_Line'] = []
datos['Value_Line'] = []
datos['Name_Trafo_Tri']=[]
datos['Value_Trafo_Tri']=[]
for Line in Lines:
    try:
        value = Line.c.loading
        name=Line.loc_name
        datos['Name_Line'].append(name)
        datos['Value_Line'].append(value)
    except:
        continue

for carga in cargas:
    try:
        value = carga.c.plini
        name=carga.loc_name
        app.PrintPlain('Loading of the load: %s = %.2f %%' %(name,value))
    except:
        continue