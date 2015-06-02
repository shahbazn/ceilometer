from ceilometer.network.statistics import driver
from ceilometer.network.statistics.plumgrid import client 
from ceilometer import neutron_client
from oslo_utils import timeutils
from ceilometer.openstack.common import log
import json

LOG=log.getLogger(__name__)

class PLUMgridDriver(driver.Driver):

    def __init__(self):
       self.n_client = neutron_client.Client()
       self.pg_client = None

    def get_sample_data(self, meter_name, parse_url, params, cache):
       # Get the function corresponding the meter name
       # to extract Data for that resource from PLUMgrid Platform        
       extractor = self._get_extractor(meter_name)
       if extractor is None:
           # Meter not supported by PLUMgrid Driver
           return

       if self.pg_client is None:
           self.pg_client = client.Client(parse_url.netloc, params['username'][0], params['password'][0])
       
       # Get all the vm ports data from neutron
       ports=self.n_client.port_get_all()
       if not ports:
           return

       timestamp = timeutils.utcnow().isoformat()
       for port in ports:
           yield (extractor(port['id'], port['tenant_id']))+(port, timestamp,)

    def _get_extractor(self,meter_name):
       extractor = '_'+meter_name.replace('.','_')
       return getattr(self,extractor,None) 

    def _vm_recieve_packets(self, port_uuid, tenant_id):
       pg = self.pg_client
       data =  pg.get_vm_stats(port_uuid, tenant_id)              
       return (data['packets_rx'], port_uuid)

    def _vm_recieve_bytes(self, port_uuid, tenant_id):
       pg = self.pg_client
       data =  pg.get_vm_stats(port_uuid, tenant_id)
       return (data['bytes_rx'], port_uuid)

    def _vm_transmit_packets(self, port_uuid, tenant_id):
       pg = self.pg_client
       data =  pg.get_vm_stats(port_uuid, tenant_id)
       return (data['packets_tx'], port_uuid)

    def _vm_transmit_bytes(self, port_uuid, tenant_id):
       pg = self.pg_client
       data =  pg.get_vm_stats(port_uuid, tenant_id)
       return (data['bytes_tx'], port_uuid)
