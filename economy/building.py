import json
import logging
from uuid import uuid4

STARTING_RENT = 100

logger = logging.getLogger('simulation.buildings')

class Building():
    def __init__(self, max_tenants, rent=STARTING_RENT):
        self.id = uuid4().hex
        self.rent = rent
        self.tenants = []
        self.max_tenants = max_tenants

    def add_tenant(self, tenant):
        if len(self.tenants) >= self.max_tenants:
            return False
        self.tenants.append(tenant)
        tenant.building = self
        self.log({'event': 'added_tenant',
                  'tenant': {
                      'type': type(tenant).__name__,
                      'id': tenant.id
                  }})
        return True

    def remove_tenant(self, tenant):
        if tenant in self.tenants:
            self.tenants.remove(tenant)
            self.log({'event': 'removed_tenant', 'tenant': {'id': tenant.id}})

    def collect_rent(self):
        for tenant in self.tenants:
            tenant.pay(self.rent)

    def log(self, data):
        data['id'] = self.id
        logger.info('buildings:{}'.format(json.dumps(data)))

    @property
    def available_space(self):
        return self.max_tenants - len(self.tenants)
