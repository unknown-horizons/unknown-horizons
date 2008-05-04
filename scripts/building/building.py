
#TODO: Implement selection support over a common interface with Unit
class Building(object):
    def calcBuildingCost():
        #TODO do ground checking and throw exception if blocked
        return (100,  1,  1,  1)

_buildingclasses = {}

def initBuildingClasses(dbreader):
    buildings = dbreader.query("SELECT building_id, classPackage, classType, size_x, size_y, name FROM building")
    for row in buildings.rows:
        building_id,  package,  type,  size_x,  size_y,  name = row
        
        module = __import__(package,  globals(), locals())
        baseclass = getattr(module,  type)
        
        propdict = {}
        propdict['size'] = (size_x,  size_y)
        
        properties = dbreader.query("SELECT key, value FROM building_property WHERE building_id = ?",  str(building_id))
        for row in properties.rows:
            key,  value = row
            propdict[value] = key
            
        _buildingclasses[building_id] = type(name,  (baseclass, ),  propdict)
    
def getBuildingClass(building_id):
    bclass = _buildingclasses[building_id]
    assert (bclass is not None)
    return bclass
