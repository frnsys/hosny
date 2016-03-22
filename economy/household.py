import math


class Household():
    def __init__(self, people, consumer_good_utility):
        self.people = people
        self.goods = 0
        self.health = 1
        self.good_utility = consumer_good_utility

        for p in self.people:
            p.household = self

    def step(self):
        self.goods = 0

    @property
    def quality_of_life(self):
        """pretty simple - should also incorporate leisure time"""
        return ((self.goods * self.good_utility) + sum(p.health_utility(p._state['health']) for p in self.people)/len(self.people)) * self.health

    @property
    def min_consumption(self):
        return sum(p.min_consumption for p in self.people)

    def excess_consumption(self, price):
        i = 0
        while self.marginal_utility(price, self.min_consumption + i) > 0:
            i += 1
        return i

    def marginal_utility(self, n_goods, price):
        return sum(round(p.cash_change_utility(-price)
                   + p.purchasing_utility(self.good_utility, price)
                   + self.consumer_good_utility_change(n_goods), 4)
                   for p in self.people)

    def consumer_good_utility_change(self, n_goods):
        """marginal utility"""
        u = self.consumer_good_utility(n_goods)
        u_ = self.consumer_good_utility(n_goods + 1)
        return round(u_ - u, 4)

    def consumer_good_utility(self, n_goods):
        # sigmoid
        return 1/(1 + math.exp(-n_goods)) - 0.5

    @property
    def cash(self):
        return sum(p._state['cash'] for p in self.people)

    def purchase_goods(self, supplier):
        desired_goods = max(0, (self.min_consumption + self.excess_consumption(supplier.price)) - self.goods)

        if not supplier.price:
            to_purchase = desired_goods
        else:
            can_afford = max(0,  math.floor(self.cash/supplier.price))
            desired_goods = min(can_afford, desired_goods)
            to_purchase = min(desired_goods, supplier.supply)
        cost = to_purchase * supplier.price
        supplier.sell(to_purchase)
        self.goods += to_purchase

        # subtract cash from members
        for p in self.people:
            spent = min(cost, p._state['cash'])
            p._state['cash'] -= spent
            cost -= spent

        return desired_goods - to_purchase, to_purchase

    def check_goods(self):
        if self.goods < self.min_consumption:
            self.health -= ((self.min_consumption - self.goods)/self.min_consumption) * 0.1
        else:
            self.health += (self.goods - self.min_consumption) * 0.1
            self.health = min(1, self.health)
        return self.health > 0
