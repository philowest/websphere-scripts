#TODO: chuck this in an external file and include here. Should make the script easier to handle. 
#global params
target = '''target/${project.name}-${project.version}.${project.packaging}'''
appId = '''${app.uid}'''
webappUid = '${webapp.uid}'
ejbUid = '${ejb.uid}'
warModuleMap = '["${webapp.uid}" ${webapp.uid}.war,WEB-INF/web.xml ${was.server}+${was.cluster}]'
ejbModuleMap = '["${ejb.uid}" ${ejb.uid}.jar,META-INF/ejb-jar.xml ${ejb.cluster}]'
contextRoot = '${context.root}'
moduleMapOptions = ''
mapModules = ''
#end global params

def setVirtualHost ():
    if len('${virtual.host}') > 0:
        AdminApp.edit("${app.uid}", '[-MapWebModToVH [["${webapp.uid}" ${webapp.uid}.war,WEB-INF/web.xml ${virtual.host}]]]')
#endDef

def referenceSharedLib ():
    AdminApp.edit('${app.uid}', ['-MapSharedLibForMod', [['${app.uid}', 'META-INF/application.xml', '${shared.library.name}']]])    
#endDef

def startApplication ():
    serverProcesses = '${server.process}'.split(',')
    for x in range(0, len(serverProcesses), 2):
        appManager=AdminControl.queryNames('cell=${was.cell},node=${server.node.one},type=ApplicationManager,process=' + serverProcesses[x] + ',*' )  
        AdminControl.invoke(appManager, 'startApplication', '${app.uid}')
        AdminConfig.save()
        appManager=AdminControl.queryNames('cell=${was.cell},node=${server.node.two},type=ApplicationManager,process=' + serverProcesses[x + 1] + ',*' )  
        AdminControl.invoke(appManager, 'startApplication', '${app.uid}')
        AdminConfig.save()
#endDef

#DEPRECATED - define in the ibm-ejb-jar-bnd.xml file instead
def setEJBJNDINames ():
    modules = '${ejb.name}'.split(',')
    ejbJNDIName = '${ejb.jndi.name}'.split(',')
    for x in range(0, len(modules)):
        AdminApp.edit("${app.uid}", '[-BindJndiForEJBNonMessageBinding [[${ejb.uid} ' + modules[x] + ' ${ejb.uid}.jar,META-INF/ejb-jar.xml ' + ejbJNDIName[x] + ']]]') 
#endDef

def initParams ():
    #if we have a web module...
    global contextRoot
    global warModuleMap
    global ejbModuleMap
    if contextRoot.find('${') == -1 :
        contextRoot = '-contextroot /${context.root}'
    else:
        warModuleMap = ''
    if ejbModuleMap.find('${') != -1 :
        ejbModuleMap = ''
    moduleMapOptions = '-usedefaultbindings ' + contextRoot  + ' -appname ${app.uid}'
    mapModules = '-MapModulesToServers [' + warModuleMap + ejbModuleMap + ']' + moduleMapOptions
#endDef

#installation template
initParams()
application = AdminConfig.getid('/Deployment:${app.uid}/')
#update if exists
if len(application) > 0:
    AdminApp.update('${app.uid}', 'app', '[-operation update -contents target/${project.name}-${project.version}.${project.packaging} -MapModulesToServers [' + warModuleMap + ejbModuleMap + '] -defaultbinding.virtual.host ${virtual.host} -usedefaultbindings -contextroot /${context.root} -appname ${app.uid}]')
    setVirtualHost()
    AdminConfig.save()
#install if new
else:
    AdminApp.install('target/${project.name}-${project.version}.${project.packaging}', '[-MapModulesToServers [' + warModuleMap + ejbModuleMap + '] -defaultbinding.virtual.host ${virtual.host} -usedefaultbindings -contextroot /${context.root} -appname ${app.uid}]')
    #map vh
    setVirtualHost()
    AdminConfig.save()
    #wait for app to be ready before we start it
    app = AdminApp.isAppReady('${app.uid}')
    while (app == 'false'):
        app = AdminApp.isAppReady('${app.uid}')
    startApplication()
referenceSharedLib()
#setEJBJNDINames()
AdminConfig.save()
#sync
AdminNodeManagement.syncActiveNodes()
AdminConfig.save()