# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

######################################################################
## Commissions

class Commission:
    def calculate(self, order, price, quantity):
        raise NotImplementedError()

class NoCommission(Commission):
    def calculate(self, order, price, quantity):
        return 0

class FixedCommission(Commission):
    def __init__(self, cost):
        self.__cost = cost

    def calculate(self, order, price, quantity):
        return self.__cost
    
class FuturesCommission(Commission):
    def __init__(self, costpercontract):
        self.__costpercontract = costpercontract
        
    def calculate(self, order, price, quantity):
        return quantity * self.__costpercontract
        