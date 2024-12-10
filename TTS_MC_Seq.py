from pyomo.environ import *
import random
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Mont_carlo simulation.
TTS_values = []

confidence_level = 0.95   # confidence level
Epsilon = 1-confidence_level
Initial_iterations = 20
Step_size = 5
tolerance = 0.3
max_iterations = 50  # Set a maximum to avoid infinite loops
Total_iterations = 0


while Total_iterations < max_iterations:
    Current_TTS_values = []

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

        # parameters-Initial Inventory
        inventory={('F12', 'P15'): 607.0, ('F12', 'P11'): 671.0, ('F6', 'P6'): 1019.0, ('F14', 'P7'): 585.0, ('F6', 'P11'): 636.0, ('F11', 'P1'): 726.0, ('F5', 'P9'): 506.0, ('F1', 'P17'): 706.0, ('F6', 'P4'): 889.0, ('F12', 'P13'): 607.0, ('F1', 'P19'): 574.0, ('F8', 'P6'): 671.0, ('F5', 'P8'): 684.0, ('F15', 'P11'): 979.0, ('F7', 'P1'): 988.0, ('F7', 'P16'): 535.0, ('F5', 'P14'): 854.0, ('F5', 'P3'): 530.0, ('F14', 'P6'): 491.0, ('F11', 'P8'): 570.0, ('F2', 'P9'): 1049.0, ('F1', 'P12'): 532.0, ('F15', 'P5'): 924.0, ('F7', 'P7'): 455.0, ('F7', 'P8'): 715.0, ('F9', 'P3'): 1058.0, ('F8', 'P19'): 878.0, ('F3', 'P2'): 453.0, ('F9', 'P6'): 884.0, ('F14', 'P10'): 691.0, ('F12', 'P1'): 1032.0, ('F12', 'P20'): 453.0, ('F1', 'P9'): 587.0, ('F11', 'P15'): 887.0, ('F13', 'P7'): 1089.0, ('F7', 'P3'): 471.0, ('F5', 'P10'): 876.0, ('F1', 'P8'): 915.0, ('F7', 'P18'): 1091.0, ('F14', 'P19'): 744.0, ('F10', 'P20'): 623.0, ('F2', 'P6'): 889.0, ('F2', 'P15'): 818.0, ('F6', 'P9'): 997.0, ('F15', 'P1'): 1065.0, ('F4', 'P3'): 640.0, ('F8', 'P12'): 693.0, ('F11', 'P5'): 1005.0, ('F10', 'P7'): 689.0, ('F9', 'P17'): 880.0, ('F15', 'P7'): 702.0, ('F3', 'P13'): 574.0, ('F14', 'P16'): 565.0, ('F10', 'P8'): 961.0, ('F11', 'P19'): 750.0, ('F4', 'P4'): 563.0, ('F3', 'P5'): 726.0, ('F14', 'P1'): 770.0, ('F8', 'P9'): 647.0, ('F5', 'P16'): 561.0, ('F6', 'P18'): 634.0}
        m.Inventory = Param(m.Factory_Product, initialize= inventory)

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
        m.TTS = Var(within=NonNegativeReals)

        Obj = m.TTS
        m.obj = Objective(expr=Obj, sense=maximize)

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
            m.Constraints.add(sum(m.u[f,i] + m.Inventory[f,i] for f in m.Factories if (f,i) in m.Factory_Product) >= m.Demand[i] * m.TTS)

        # Capacity constraint
        for f in m.Factories:
            m.Constraints.add(sum(m.Process_Time[f,i] * m.u[f,i] for i in m.Products if (f,i) in m.Factory_Product) <= m.Capacity[f] * m.TTS *(1 - m.Disruption_Rate[f]))

        solver = SolverFactory('cbc')
        # m.display()
        # m.pprint()

        # Since we dont need the detailed solver log. this help pyomo to clear space.In the provided code, tee=False is used to avoid cluttering the console with solver output, making it easier to focus on the results of the optimization rather than the solver's progress messages. If you prefer to see the solver's output for each solve step, you can set tee=True.
        results = solver.solve(m, tee=False)
        opt_value_obj = m.obj()
        Current_TTS_values.append(opt_value_obj)


    # Calculate the 95% confidence interval
    mean_obj = np.mean(Current_TTS_values)
    confidence_interval = stats.t.interval(confidence_level, len(Current_TTS_values) - 1, loc=mean_obj, scale=stats.sem(Current_TTS_values))
    margin_of_error = (confidence_interval[1] - confidence_interval[0]) / 2


    # Check if the margin of error is within 5% of the mean objective value
    if (margin_of_error <= tolerance * mean_obj):
        print(f"95% confidence level achieved within 5% tolerance after {Initial_iterations} simulations.")
        TTS_values = Current_TTS_values
        # break is within the while loop not for loop
        break
    else:
        Initial_iterations += Step_size
        Total_iterations += 1


print("TTS_values:", TTS_values)

#Results in box plot
# Create a figure with 4 subplots (1 row, 4 columns)
plt.figure(figsize=(4, 8))

#colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33A1', '#FFC300',  '#DAF7A6', '#900C3F', '#581845', '#C70039', '#1F618D']

sns.boxplot(data=TTS_values, color='#1F618D')
plt.title('TTS (Days)', fontsize=18, fontweight='bold')
plt.ylabel('Values' if i == 0 else '')

# Adjust layout for better spacing
plt.tight_layout()

# Show the plot
plt.show()







