import sys
sys.path.append("C:\\Program Files (x86)\\DIgSILENT\\PowerFactory 15.1\\python")
import powerfactory

app = powerfactory.GetApplication()

FolderWhereStudyCasesAreSaved= app.GetProjectFolder('Study Cases')

app.PrintPlain(FolderWhereStudyCasesAreSaved)

AllStudyCasesInProject= FolderWhereStudyCasesAreSaved.GetContents()

for StudyCase in AllStudyCasesInProject:

   app.PrintPlain(StudyCase)

   StudyCase.Activate()
