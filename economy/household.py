import math


class Household():
    def __init__(self, people):
        self.people = people
        self.goods = 0
        self.days_without_goods = 0

    def step(self):
        self.goods = 0

    @property
    def min_consumption(self):
        return sum(p.min_consumption for p in self.people)

    def purchase_goods(self, supplier):
        cash = sum(p.cash for p in self.people)
        desired_goods = self.min_consumption - self.goods

        can_afford = math.floor(cash/supplier.price)
        desired_goods = min(can_afford, desired_goods)
        to_purchase = min(desired_goods, supplier.supply)
        cost = to_purchase * supplier.price

        supplier.sell(to_purchase)
        self.goods += to_purchase

        # subtract cash from members
        for p in self.people:
            spent = min(cost, p.cash)
            p.cash -= spent
            cost -= spent

        return desired_goods - to_purchase, to_purchase

    def check_goods(self):
        if self.goods < self.min_consumption:
            self.days_without_goods += 1
        else:
            self.days_without_goods = 0

        if self.days_without_goods >= 7:
            pass # destitute/dead
