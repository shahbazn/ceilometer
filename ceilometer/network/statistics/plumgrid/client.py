from ceilometer.openstack.common import log
import httplib
import json

LOG = log.getLogger(__name__)

class Client(object):

    def __init__(self, server, user, password, port='443'):
        self.server = server
        self.user = user
        self.password = password
        self.port = port
        self.headers = {}
        self.session = httplib.HTTPSConnection(self.server, self.port)

    def pg_login(self, user, password, tenant_id=''):
        conn = self.session
        login_data = {'userName': user, 'password': password,
                    'tenant_id': tenant_id, 'lib_tocken': None}
        login_url = '/0/login'
        conn.request('POST', login_url, json.dumps(login_data), self.headers)        
        resp = conn.getresponse()
        pg_cookie = resp.getheader('Set-Cookie')
        if pg_cookie is None:
            log.error('Authorization Failed!')
            raise Exception('Authorization Denied!')
        self.headers['cookie'] = pg_cookie
        conn.close()

    def get_data(self, tenant_id, config_only = True):
        conn = self.session
        conn.connect()

        self.headers['Content-type'] = 'application/json'
        self.headers['Accept'] = 'application/json'
        self.headers['Plumgrid-Client'] = 'true'
        
        pg_url = '/0/connectivity/domain?configonly=false'
        conn.request('GET', pg_url, None, self.headers)
        resp = conn.getresponse()
        resp_str = resp.read()

        if resp.status is httplib.OK:
            conn.close()
            data = json.loads(resp_str)
            return data[tenant_id]

        elif resp.status == 403:
            self.pg_login(self.user, self.password)
            conn.request('GET', pg_url, None, self.headers)
            resp = conn.getresponse()
            resp_str = resp.read()
            conn.close()
            data = json.loads(resp_str)
            return data[tenant_id]

        elif resp.status == 502:
            raise Exception('PLUMgrid services seems to be down!')

        else:
            err_str = 'HTTP error: ' + str(resp.status)
            raise Exception(err_str)

    def get_vm_stats(self, port_uuid, tenant_id):
        data = self.get_data(tenant_id)
        for ne in data['ne']:
            if ne.startswith('bridge_'):
                for ifc in data['ne'][ne]['ifc']:
                    ifc_arr  = ifc.split('_')
                    if len(ifc_arr) > 1 and ifc_arr[1] == port_uuid:
                        packets_rx = data['ne'][ne]['ifc'][ifc]['packets_rx']
                        packets_tx = data['ne'][ne]['ifc'][ifc]['packets_tx']
                        bytes_rx = data['ne'][ne]['ifc'][ifc]['bytes_rx']
                        bytes_tx  = data['ne'][ne]['ifc'][ifc]['bytes_tx']
                        port_stats = {'packets_rx': packets_rx, 'packets_tx': packets_tx,
                                   'bytes_rx': bytes_rx, 'bytes_tx': bytes_tx}
                        return port_stats
        return  
