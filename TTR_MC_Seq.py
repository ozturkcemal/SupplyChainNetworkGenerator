from pyomo.environ import *
import random
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Mont_carlo simulation.
Lostmargin_values = []
PGHG_values = []
TGHG_values = []
SI_values = []

confidence_level = 0.95   # confidence level
Epsilon = 1-confidence_level
Initial_iterations = 20
Step_size = 5
tolerance = 0.3
max_iterations = 50  # Set a maximum to avoid infinite loops
Total_iterations = 0


while Total_iterations < max_iterations:
    Current_Lostmargin_values = []
    Current_PGHG_values = []
    Current_TGHG_values = []
    Current_SI_values = []
    for iter in range(Initial_iterations):
        # IMPORTANT: we should generate random valuse and for each time these value are fixed for all 3 run of objective functions so
        #  we can use random.seed(i) which i is iteration
        random.seed(iter)
        # Create a Concrete Model
        m = ConcreteModel()

        # Sets
        # Input from the user
        num_products = 20
        num_factories = 15

        # Generate product and factory names
        products = [f'P{i}' for i in range(1, num_products + 1)]
        factories = [f'F{i}' for i in range(1, num_factories + 1)]

        # set of All products
        m.Products = Set(initialize=products)
        # set of all factories
        m.Factories = Set(initialize=factories)

        # set of final products
        m.Final_Products = Set(initialize=['P18', 'P19', 'P20'])

        # BOM relationship
        BOM = {('P1', 'P9'): 4, ('P1', 'P19'): 11, ('P2', 'P9'): 2, ('P2', 'P15'): 8, ('P2', 'P20'): 16, ('P3', 'P10'): 4,
             ('P3', 'P16'): 6, ('P4', 'P11'): 2,('P5', 'P11'): 3, ('P6', 'P11'): 2, ('P6', 'P17'): 12, ('P7', 'P12'): 1, ('P7', 'P13'): 1, ('P7', 'P14'): 5,
             ('P7', 'P18'): 15,('P8', 'P13'): 4,('P9', 'P14'): 1, ('P9', 'P19'): 3, ('P10', 'P14'): 1, ('P10', 'P15'): 2, ('P10', 'P20'): 4, ('P11', 'P14'): 1,
             ('P11', 'P16'): 1,('P12', 'P15'): 2, ('P12', 'P16'): 1, ('P12', 'P17'): 3, ('P13', 'P17'): 4, ('P13', 'P18'): 10, ('P14', 'P18'): 2,
             ('P15', 'P18'): 1,('P15', 'P19'): 1, ('P16', 'P19'): 2, ('P16', 'P20'): 1, ('P17', 'P20'): 2}

        # Factory_Product: Each factory can produce 1 to 3 products, each product can be produced in 1 to 3 factories
        factory_product = [('F12', 'P15'), ('F12', 'P11'), ('F6', 'P6'), ('F14', 'P7'), ('F6', 'P11'), ('F11', 'P1'), ('F5', 'P9'), ('F1', 'P17'), ('F6', 'P4'), ('F12', 'P13'), ('F1', 'P19'), ('F8', 'P6'), ('F5', 'P8'), ('F15', 'P11'), ('F7', 'P1'), ('F7', 'P16'), ('F5', 'P14'), ('F5', 'P3'), ('F14', 'P6'), ('F11', 'P8'), ('F2', 'P9'), ('F1', 'P12'), ('F15', 'P5'), ('F7', 'P7'), ('F7', 'P8'), ('F9', 'P3'), ('F8', 'P19'), ('F3', 'P2'), ('F9', 'P6'), ('F14', 'P10'), ('F12', 'P1'), ('F12', 'P20'), ('F1', 'P9'), ('F11', 'P15'), ('F13', 'P7'), ('F7', 'P3'), ('F5', 'P10'), ('F1', 'P8'), ('F7', 'P18'), ('F14', 'P19'), ('F10', 'P20'), ('F2', 'P6'), ('F2', 'P15'), ('F6', 'P9'), ('F15', 'P1'), ('F4', 'P3'), ('F8', 'P12'), ('F11', 'P5'), ('F10', 'P7'), ('F9', 'P17'), ('F15', 'P7'), ('F3', 'P13'), ('F14', 'P16'), ('F10', 'P8'), ('F11', 'P19'), ('F4', 'P4'), ('F3', 'P5'), ('F14', 'P1'), ('F8', 'P9'), ('F5', 'P16'), ('F6', 'P18')]
        m.Factory_Product =Set(dimen=2, initialize=factory_product)

        flows = set()
        for (child, parent) in BOM.keys():
            factories_b = {factory for factory, product in factory_product if product == child}
            factories_d = {factory for factory, product in factory_product if product == parent}
            factories_b_list = list(factories_b)
            factories_d_list = list(factories_d)
            if factories_b_list and factories_d_list:
                for a in factories_b_list:
                    for c in factories_d_list:
                        flows.add((a, child, c, parent))
        # set of Flows
        m.Flows = Set(dimen=4, initialize=flows)

        # Create Factory_Relations by eliminating (b, d) from Flows
        factory_relations = set((a, c) for (a, b, c, d) in flows)
        m.Factory_Relation = Set(dimen=2, initialize=factory_relations)

        # Parameters
        # Deterministic parameters

        # parameters-Time to recover (Optimistic: the larsgest TTR in disruption Sc, Pessimistic: the Lowest TTR in the sc,
        # Most likely velue: Average on all TTRs in the scenarion)
        TTR = 6

        # parameters-profit margin
        profitmargin={'P18': 669,'P19': 630,'P20': 428}
        m.Profitmargin = Param(m.Final_Products,initialize=profitmargin)

        # parameters-GHG at each node
        pghg={('F12', 'P15'): 33, ('F12', 'P11'): 29, ('F6', 'P6'): 27, ('F14', 'P7'): 23, ('F6', 'P11'): 26, ('F11', 'P1'): 30, ('F5', 'P9'): 26, ('F1', 'P17'): 35, ('F6', 'P4'): 24, ('F12', 'P13'): 23, ('F1', 'P19'): 32, ('F8', 'P6'): 31, ('F5', 'P8'): 27, ('F15', 'P11'): 30, ('F7', 'P1'): 21, ('F7', 'P16'): 35, ('F5', 'P14'): 27, ('F5', 'P3'): 26, ('F14', 'P6'): 32, ('F11', 'P8'): 29, ('F2', 'P9'): 33,
         ('F1', 'P12'): 31, ('F15', 'P5'): 21, ('F7', 'P7'): 27, ('F7', 'P8'): 27, ('F9', 'P3'): 28, ('F8', 'P19'): 32, ('F3', 'P2'): 31, ('F9', 'P6'): 30, ('F14', 'P10'): 31, ('F12', 'P1'): 31, ('F12', 'P20'): 20, ('F1', 'P9'): 30, ('F11', 'P15'): 35, ('F13', 'P7'): 33, ('F7', 'P3'): 23, ('F5', 'P10'): 20, ('F1', 'P8'): 26, ('F7', 'P18'): 28, ('F14', 'P19'): 22, ('F10', 'P20'): 28, ('F2', 'P6'): 26,
         ('F2', 'P15'): 34, ('F6', 'P9'): 34, ('F15', 'P1'): 33, ('F4', 'P3'): 22, ('F8', 'P12'): 30, ('F11', 'P5'): 35, ('F10', 'P7'): 27, ('F9', 'P17'): 31, ('F15', 'P7'): 33, ('F3', 'P13'): 31, ('F14', 'P16'): 31, ('F10', 'P8'): 30, ('F11', 'P19'): 23, ('F4', 'P4'): 31, ('F3', 'P5'): 31, ('F14', 'P1'): 31, ('F8', 'P9'): 30, ('F5', 'P16'): 21, ('F6', 'P18'): 24}
        m.PGHG = Param(m.Factory_Product, initialize=pghg)

        # parameters-TGHG in flow between nodes for transporting one unit per kilometer
        TGHG=5
        distance={('F15', 'F11'): 295, ('F15', 'F14'): 129, ('F1', 'F8'): 186, ('F13', 'F8'): 214, ('F8', 'F15'): 58, ('F10', 'F8'): 145, ('F8', 'F2'): 78, ('F8', 'F9'): 56, ('F5', 'F8'): 141, ('F9', 'F10'): 279, ('F3', 'F8'): 138, ('F7', 'F2'): 90, ('F8', 'F11'): 162, ('F8', 'F14'): 294, ('F2', 'F6'): 226, ('F7', 'F11'): 69, ('F14', 'F3'): 63, ('F7', 'F14'): 136, ('F12', 'F8'): 231, ('F15', 'F8'): 108, ('F6', 'F6'): 0, ('F11', 'F6'): 113, ('F2', 'F7'): 241, ('F5', 'F10'): 216, ('F3', 'F10'): 94, ('F12', 'F14'): 230, ('F8', 'F8'): 0, ('F1', 'F3'): 266, ('F10', 'F3'): 162, ('F14', 'F6'): 218, ('F9', 'F6'): 274, ('F7', 'F8'): 80, ('F5', 'F3'): 294, ('F14', 'F10'): 171, ('F11', 'F3'): 52, ('F11', 'F7'): 120, ('F6', 'F7'): 255, ('F2', 'F1'): 105, ('F2', 'F5'): 264, ('F15', 'F3'): 216, ('F14', 'F7'): 61, ('F9', 'F7'): 257, ('F13', 'F6'): 183, ('F10', 'F6'): 90, ('F4', 'F6'): 211, ('F5', 'F6'): 273, ('F7', 'F10'): 240, ('F3', 'F6'): 294, ('F1', 'F10'): 153, ('F2', 'F15'): 60,
         ('F2', 'F12'): 78, ('F11', 'F1'): 241, ('F6', 'F1'): 131, ('F2', 'F9'): 209, ('F7', 'F3'): 50, ('F2', 'F11'): 69, ('F6', 'F5'): 278, ('F11', 'F5'): 118, ('F13', 'F3'): 93, ('F12', 'F6'): 254, ('F14', 'F1'): 83, ('F1', 'F7'): 254, ('F9', 'F1'): 149, ('F13', 'F7'): 172, ('F10', 'F7'): 130, ('F15', 'F6'): 100, ('F4', 'F12'): 111, ('F4', 'F7'): 275, ('F14', 'F5'): 189, ('F9', 'F5'): 156, ('F5', 'F7'): 271, ('F3', 'F7'): 227, ('F3', 'F12'): 82, ('F11', 'F2'): 208, ('F6', 'F15'): 265, ('F11', 'F12'): 74, ('F6', 'F12'): 87, ('F11', 'F15'): 130, ('F6', 'F9'): 158, ('F8', 'F6'): 293, ('F6', 'F11'): 114, ('F11', 'F11'): 0, ('F12', 'F7'): 135, ('F14', 'F2'): 75, ('F14', 'F12'): 130, ('F14', 'F15'): 147, ('F7', 'F6'): 293, ('F9', 'F15'): 209, ('F9', 'F12'): 172, ('F14', 'F9'): 72, ('F9', 'F9'): 0, ('F1', 'F1'): 0, ('F15', 'F7'): 132, ('F14', 'F11'): 170, ('F13', 'F1'): 117, ('F2', 'F8'): 250, ('F10', 'F1'): 66, ('F14', 'F14'): 0, ('F1', 'F5'): 100, ('F9', 'F14'): 66,
         ('F5', 'F1'): 297, ('F10', 'F5'): 249, ('F13', 'F5'): 195, ('F3', 'F1'): 141, ('F4', 'F5'): 153, ('F5', 'F5'): 0, ('F3', 'F5'): 208, ('F8', 'F7'): 249, ('F8', 'F12'): 266, ('F2', 'F14'): 254, ('F7', 'F7'): 0, ('F7', 'F12'): 270, ('F12', 'F1'): 96, ('F1', 'F2'): 262, ('F1', 'F12'): 171, ('F13', 'F12'): 206, ('F10', 'F12'): 194, ('F4', 'F15'): 169, ('F11', 'F8'): 72, ('F6', 'F8'): 78, ('F12', 'F5'): 117, ('F1', 'F9'): 228, ('F15', 'F1'): 186, ('F1', 'F11'): 250, ('F5', 'F2'): 109, ('F5', 'F12'): 167, ('F3', 'F2'): 262, ('F3', 'F15'): 223, ('F1', 'F14'): 172, ('F15', 'F5'): 62, ('F3', 'F9'): 237, ('F5', 'F11'): 202, ('F4', 'F14'): 99, ('F3', 'F11'): 182, ('F14', 'F8'): 230, ('F5', 'F14'): 144, ('F8', 'F1'): 93, ('F11', 'F14'): 299, ('F12', 'F2'): 98, ('F6', 'F14'): 241, ('F8', 'F5'): 261, ('F12', 'F9'): 152, ('F7', 'F1'): 195, ('F15', 'F2'): 168, ('F15', 'F15'): 0, ('F12', 'F11'): 120, ('F15', 'F12'): 177, ('F7', 'F5'): 59}
        m.Distance = Param(m.Factory_Relation, initialize=distance)

        # parameters-Initial Inventory
        inventory={('F12', 'P15'): 607.0, ('F12', 'P11'): 671.0, ('F6', 'P6'): 1019.0, ('F14', 'P7'): 585.0, ('F6', 'P11'): 636.0, ('F11', 'P1'): 726.0, ('F5', 'P9'): 506.0, ('F1', 'P17'): 706.0, ('F6', 'P4'): 889.0, ('F12', 'P13'): 607.0, ('F1', 'P19'): 574.0, ('F8', 'P6'): 671.0, ('F5', 'P8'): 684.0, ('F15', 'P11'): 979.0, ('F7', 'P1'): 988.0, ('F7', 'P16'): 535.0, ('F5', 'P14'): 854.0, ('F5', 'P3'): 530.0, ('F14', 'P6'): 491.0, ('F11', 'P8'): 570.0, ('F2', 'P9'): 1049.0, ('F1', 'P12'): 532.0, ('F15', 'P5'): 924.0, ('F7', 'P7'): 455.0, ('F7', 'P8'): 715.0, ('F9', 'P3'): 1058.0, ('F8', 'P19'): 878.0, ('F3', 'P2'): 453.0, ('F9', 'P6'): 884.0, ('F14', 'P10'): 691.0, ('F12', 'P1'): 1032.0, ('F12', 'P20'): 453.0, ('F1', 'P9'): 587.0, ('F11', 'P15'): 887.0, ('F13', 'P7'): 1089.0, ('F7', 'P3'): 471.0, ('F5', 'P10'): 876.0, ('F1', 'P8'): 915.0, ('F7', 'P18'): 1091.0, ('F14', 'P19'): 744.0, ('F10', 'P20'): 623.0, ('F2', 'P6'): 889.0, ('F2', 'P15'): 818.0, ('F6', 'P9'): 997.0, ('F15', 'P1'): 1065.0, ('F4', 'P3'): 640.0, ('F8', 'P12'): 693.0, ('F11', 'P5'): 1005.0, ('F10', 'P7'): 689.0, ('F9', 'P17'): 880.0, ('F15', 'P7'): 702.0, ('F3', 'P13'): 574.0, ('F14', 'P16'): 565.0, ('F10', 'P8'): 961.0, ('F11', 'P19'): 750.0, ('F4', 'P4'): 563.0, ('F3', 'P5'): 726.0, ('F14', 'P1'): 770.0, ('F8', 'P9'): 647.0, ('F5', 'P16'): 561.0, ('F6', 'P18'): 634.0}
        m.Inventory = Param(m.Factory_Product, initialize= inventory)

        # parameters-Societal impact of each node
        si={'F1': 5, 'F2': 9, 'F3': 3, 'F4': 10, 'F5': 1, 'F6': 4, 'F7': 7, 'F8': 4, 'F9': 4, 'F10': 6, 'F11': 8, 'F12': 8, 'F13': 10, 'F14': 7, 'F15': 9}
        m.SI = Param(m.Factories, initialize= si)

        # Uncertain parametsrs
        # parameters-Processing time
        processtime={('F12', 'P15'): 3, ('F12', 'P11'): 4, ('F6', 'P6'): 1, ('F14', 'P7'): 2, ('F6', 'P11'): 4, ('F11', 'P1'): 1, ('F5', 'P9'): 3, ('F1', 'P17'): 4, ('F6', 'P4'): 4, ('F12', 'P13'): 4, ('F1', 'P19'): 4, ('F8', 'P6'): 4, ('F5', 'P8'): 4, ('F15', 'P11'): 3, ('F7', 'P1'): 3, ('F7', 'P16'): 1, ('F5', 'P14'): 4, ('F5', 'P3'): 2, ('F14', 'P6'): 2, ('F11', 'P8'): 4, ('F2', 'P9'): 4,
         ('F1', 'P12'): 2, ('F15', 'P5'): 4, ('F7', 'P7'): 1, ('F7', 'P8'): 1, ('F9', 'P3'): 3, ('F8', 'P19'): 3, ('F3', 'P2'): 1, ('F9', 'P6'): 4, ('F14', 'P10'): 4, ('F12', 'P1'): 4, ('F12', 'P20'): 3, ('F1', 'P9'): 1, ('F11', 'P15'): 2, ('F13', 'P7'): 2, ('F7', 'P3'): 1, ('F5', 'P10'): 4, ('F1', 'P8'): 2, ('F7', 'P18'): 3, ('F14', 'P19'): 4, ('F10', 'P20'): 4, ('F2', 'P6'): 1,
         ('F2', 'P15'): 4, ('F6', 'P9'): 2, ('F15', 'P1'): 2, ('F4', 'P3'): 1, ('F8', 'P12'): 1, ('F11', 'P5'): 4, ('F10', 'P7'): 1, ('F9', 'P17'): 2, ('F15', 'P7'): 1, ('F3', 'P13'): 1, ('F14', 'P16'): 3, ('F10', 'P8'): 2, ('F11', 'P19'): 3, ('F4', 'P4'): 2, ('F3', 'P5'): 2, ('F14', 'P1'): 3, ('F8', 'P9'): 3, ('F5', 'P16'): 3, ('F6', 'P18'): 1}
        m.Process_Time = Param(m.Factory_Product, initialize= processtime,mutable=True)

        # parameters-capacity
        capacity={'F1': 13778, 'F2': 5264, 'F3': 10875, 'F4': 9395, 'F5': 12438,'F6': 9828, 'F7': 9885, 'F8': 14140, 'F9': 9347, 'F10': 9125,
         'F11': 6081, 'F12': 11444, 'F13': 10010, 'F14': 6245, 'F15': 13652}
        m.Capacity = Param(m.Factories, initialize=capacity,mutable=True)

        #parameter Demand for final products
        demand={'P18': 578,'P19': 569,'P20': 504}
        m.Demand = Param(m.Final_Products, initialize=demand,mutable=True)

        #m.Disruption_Rate = {i: (random.uniform(0, 1) if i in m.Disrupted_Factories else 0)  for i in m.Factories}
        disruptionrate={i:0 for i in m.Factories}
        m.Disruption_Rate = Param(m.Factories, initialize=disruptionrate,mutable=True)

        # Apply perturbation to uncertain parameters (10% perturbation)
        m.Disruption_Rate['F3']= random.uniform(0.22,0.28)
        m.Disruption_Rate['F7']= 1

        for key in m.Process_Time:
            original_value = processtime.get(key, m.Process_Time[key])
            m.Process_Time[key] = original_value * random.uniform(0.9, 1.1)

        for key in m.Capacity:
            original_value = capacity.get(key, m.Capacity[key])
            m.Capacity[key] = int(round(original_value * random.uniform(0.9, 1.1)))

        # Apply perturbation to Demand
        for key in m.Demand:
            original_value = demand.get(key, m.Demand[key])
            m.Demand[key] = int(round(original_value * random.uniform(0.9, 1.1)))

        # Variables
        m.u = Var(m.Factory_Product, within=NonNegativeReals)
        m.y = Var(m.Flows, within=NonNegativeReals)
        m.l = Var(m.Final_Products, within=NonNegativeReals)

        # Objective functions
        Obj1 = sum(m.Profitmargin[i] * m.l[i] for i in m.Final_Products)
        m.obj1 = Objective(expr=Obj1, sense=minimize)

        Obj2 = sum(m.PGHG[i,j] * m.u[i,j] for i,j in m.Factory_Product) +sum(TGHG * m.Distance[f1, f2] * m.y[f1, p1, f2, p2] for (f1, p1, f2, p2) in m.Flows if (f1, f2) in m.Distance)
        m.obj2 = Objective(expr=Obj2, sense=minimize)

        Obj3 = sum(m.SI[f] * m.u[f, i] for (f,i) in m.Factory_Product)
        m.obj3 = Objective(expr=Obj3, sense=maximize)

        # constraints
        m.Constraints = ConstraintList()

        # BOM constraints
        for (i, j) in BOM.keys():
            for h in m.Factories:
                for f in m.Factories:
                    if (f, i, h, j) in m.Flows:
                        m.Constraints.add(m.u[h, j] * BOM[i, j] <= sum(m.y[f, i, h, j] for f in m.Factories if (f, i, h, j) in m.Flows))

        #Production and Inventory constraint
        for f in m.Factories:
            for i in m.Products:
                if (f,i) in m.Factory_Product:
                    m.Constraints.add(sum(m.y[f, i, h, j] for h in m.Factories for j in m.Products if (f, i, h, j) in m.Flows)<= m.u[f, i] + m.Inventory[f, i])

        # Demand satisfying
        for i in m.Final_Products:
            m.Constraints.add(m.l[i] + sum(m.u[f,i] + m.Inventory[f,i] for f in m.Factories if (f,i) in m.Factory_Product) >= m.Demand[i] * TTR)

        # solver# Upper bound for lost sales
        for i in m.Final_Products:
            m.Constraints.add(m.l[i] <= m.Demand[i] * TTR)

        # Capacity constraint
        for f in m.Factories:
            m.Constraints.add(sum(m.Process_Time[f,i] * m.u[f,i] for i in m.Products if (f,i) in m.Factory_Product) <= m.Capacity[f] * TTR *(1 - m.Disruption_Rate[f]))

        solver = SolverFactory('cbc')
        # m.display()
        # m.pprint()

        # Step 1: Optimize the first objective
        m.obj2.deactivate()
        m.obj3.deactivate()
        # Since we dont need the detailed solver log. this help pyomo to clear space.In the provided code, tee=False is used to avoid cluttering the console with solver output, making it easier to focus on the results of the optimization rather than the solver's progress messages. If you prefer to see the solver's output for each solve step, you can set tee=True.
        results = solver.solve(m, tee=False)
        opt_value_obj1 = m.obj1()
        Current_Lostmargin_values.append(opt_value_obj1)

        # Step 2: Optimize the second objective
        # Fixing optimal value for the first objective function
        m.Constraints.add((sum(m.Profitmargin[i] * m.l[i] for i in m.Final_Products)) <= 1.001*opt_value_obj1)
        m.obj2.activate()
        m.obj1.deactivate()
        results = solver.solve(m, tee=False)
        opt_value_obj2 = m.obj2()
        pghgvalue = sum(m.PGHG[i, j] * m.u[i, j] for i, j in m.Factory_Product)
        tghgvalue = sum(TGHG * m.Distance[f1, f2] * m.y[f1, p1, f2, p2] for (f1, p1, f2, p2) in m.Flows if (f1, f2) in m.Distance)
        Current_PGHG_values.append(pghgvalue)
        Current_TGHG_values.append(tghgvalue)

        # Step 3: Optimize the third objective
        # Fixing optimal value for the second objective function
        m.Constraints.add((sum(m.PGHG[i,j] * m.u[i,j] for i,j in m.Factory_Product) +sum(TGHG * m.Distance[f1, f2] * m.y[f1, p1, f2, p2] for (f1, p1, f2, p2) in m.Flows if (f1, f2) in m.Distance))  <= 1.001*opt_value_obj2)
        m.obj3.activate()
        m.obj2.deactivate()
        results = solver.solve(m, tee=False)
        opt_value_obj3 = m.obj3()
        Current_SI_values.append(opt_value_obj3)



    # Calculate the 95% confidence interval
    mean_obj1 = np.mean(Current_SI_values)
    confidence_interval1 = stats.t.interval(confidence_level, len(Current_SI_values) - 1, loc=mean_obj1, scale=stats.sem(Current_SI_values))
    margin_of_error1 = (confidence_interval1[1] - confidence_interval1[0]) / 2

    Current_PGHG_values1 = [value(expr) for expr in Current_PGHG_values]
    Current_TGHG_values1 = [value(expr) for expr in Current_TGHG_values]

    mean_obj2 = np.mean(Current_PGHG_values1)
    confidence_interval2 = stats.t.interval(confidence_level, len(Current_PGHG_values1) - 1, loc=mean_obj2, scale=stats.sem(Current_PGHG_values1))
    margin_of_error2 = (confidence_interval2[1] - confidence_interval2[0]) / 2

    mean_obj3 = np.mean(Current_TGHG_values1)
    confidence_interval3 = stats.t.interval(confidence_level, len(Current_TGHG_values1) - 1, loc=mean_obj2,scale=stats.sem(Current_TGHG_values1))
    margin_of_error3 = (confidence_interval3[1] - confidence_interval3[0]) / 2

    mean_obj4 = np.mean(Current_Lostmargin_values)
    confidence_interval4 = stats.t.interval(confidence_level, len(Current_Lostmargin_values) - 1, loc=mean_obj2,scale=stats.sem(Current_Lostmargin_values))
    margin_of_error4 = (confidence_interval4[1] - confidence_interval4[0]) / 2

    # Check if the margin of error is within 5% of the mean objective value
    if (margin_of_error1 <= tolerance * mean_obj1) and (margin_of_error2 <= tolerance * mean_obj2) and (margin_of_error3 <= tolerance * mean_obj3) and (margin_of_error4 <= tolerance * mean_obj4):
        print(f"95% confidence level achieved within 5% tolerance after {Initial_iterations} simulations.")
        Lostmargin_values = Current_Lostmargin_values
        PGHG_values = Current_PGHG_values1
        TGHG_values = Current_TGHG_values1
        SI_values = Current_SI_values
        # break is within the while loop not for loop 
        break
    else:
        Initial_iterations += Step_size
        Total_iterations += 1


print("Lostmargin_values:", Lostmargin_values)
print("PGHG_values:", PGHG_values)
print("TGHG_values:", TGHG_values)
print("SI_values:", SI_values)


#Results in box plot
# Combine all data sets into a list
data = [Lostmargin_values, PGHG_values, TGHG_values, SI_values]

# Create a figure with 4 subplots (1 row, 4 columns)
plt.figure(figsize=(16, 6))

# Define colors for each box plot
colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33A1']

# Loop through data and create a box plot for each data set
for i, dataset in enumerate(data):
    plt.subplot(1, 4, i + 1)
    sns.boxplot(data=dataset, color=colors[i])
    plt.title(['Lostmargin (€)', 'PGHG (ton CO2)', 'TGHG (ton CO2)', 'SI'][i], fontsize=18, fontweight='bold')
    #plt.xlabel(f'Set {i + 1}')
    plt.ylabel('Values' if i == 0 else '')

# Adjust layout for better spacing
plt.tight_layout()

# Show the plot
plt.show()








