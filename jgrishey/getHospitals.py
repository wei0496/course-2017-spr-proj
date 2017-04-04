import urllib.request
import json
import sodapy
import dml
import prov.model
import datetime
import uuid
import math

class getHospitals(dml.Algorithm):
    contributor = 'jgrishey'
    reads = []
    writes = ['jgrishey.hospitals']

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('jgrishey', 'jgrishey')

        url = "http://datamechanics.io/data/hospitalsgeo.json"
        data = urllib.request.urlopen(url).read().decode("utf-8")

        response = json.loads(data)

        hospitals = []
        ID = 0

        for hospital in response:
            lat = hospital['latitude']
            lon = hospital['longitude']
            name = hospital['name']
            sqft = hospital['sqft']
            hospitals.append({'_id': ID, 'lat': lat, 'long': lon, 'name': name, 'sqft': sqft})
            ID += 1

        repo.dropCollection("hospitals")
        repo.createCollection("hospitals")

        for hospital in hospitals:
            repo['jgrishey.hospitals'].insert(hospital)

        repo.logout()

        endTime = datetime.datetime.now()

        return {"start":startTime, "end":endTime}

    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
            '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('jgrishey', 'jgrishey')
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('cdp', 'http://data.cambridgema.gov/')

        this_script = doc.agent('alg:jgrishey#getTickets', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        resource = doc.entity('cdp:vnxa-cuyr', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        get_tickets = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_tickets, this_script)
        doc.usage(get_tickets, resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval',})
        doc.usage(get_tickets, resource, startTime, None,
                    {prov.model.PROV_TYPE:'ont:DataSet',
                    'ont:Computation': 'Apply ID, get latitude, and get longitude'})
        tickets = doc.entity('dat:jgrishey#tickets', {prov.model.PROV_LABEL:'Cambridge Parking Tickets', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(tickets, this_script)
        doc.wasGeneratedBy(tickets, get_tickets, endTime)
        doc.wasDerivedFrom(tickets, resource, get_tickets, get_tickets, get_tickets)

        repo.logout()

        return doc

getHospitals.execute()

## eof
