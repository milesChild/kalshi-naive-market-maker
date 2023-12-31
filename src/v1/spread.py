# imports
import numpy as np

class SpreadModule:

    def __init__(self, config: dict):
        self.__spread_width = config["spread_width"]
        self.__i_max = config["i_max"]
        self.__i_a = config["i_a"]
    
    def update_spread(self, last_px: float, cur_inv: int) -> tuple:
        bid = np.floor(last_px - self.__spread_width / 2)
        ask = np.ceil(last_px + self.__spread_width / 2)
        adjustment = self.__calc_inventory_adjustment(cur_inv)
        return bid + adjustment, ask + adjustment
    
    def __calc_inventory_adjustment(self, cur_inv: int) -> int:
        return int(self.__i_max * (1 - np.exp(-self.__i_a * np.abs(cur_inv))) * -np.sign(cur_inv))