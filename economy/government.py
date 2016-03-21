from cess.util import random_choice
from .firms import ConsumerGoodFirm, CapitalEquipmentFirm, RawMaterialFirm
from people import MIN_BUSINESS_CAPITAL


class Government():
    def __init__(self):
        self.cash = 0

    def start_business(self, world, buildings):
        # can only have one of each business
        # must be able to find a place with affordable rent
        buildings = [b for b in buildings if b.available_space]
        if not buildings:
            return False, None, None

        denom = sum(1/b.rent for b in buildings)
        building = random_choice([(b, 1/(b.rent*denom)) for b in buildings])

        # must be able to hire at least one employee
        min_cost = MIN_BUSINESS_CAPITAL + building.rent + world['mean_wage']

        if self._state['cash'] < min_cost:
            return False, None, None

        industries = ['equip', 'material', 'consumer_good']
        total_mean_profit = sum(world['mean_{}_profit'.format(name)] for name in industries)
        industry_dist = [(name, world['mean_{}_profit'.format(name)]/total_mean_profit) for name in industries]
        industry = random_choice(industry_dist)

        # choose an industry (based on highest EWMA profit)
        self.twoot('i\'m starting a BUSINESS in {}!'.format(industry), world)
        return True, industry, building
