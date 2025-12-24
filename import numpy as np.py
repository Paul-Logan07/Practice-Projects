import numpy as np
from scipy.optimize import minimize
import pulp

# Example parameters for trucks
truck_count = 5
routes = 3

# Estimated distance per route (km)
distance = [25, 30, 20]  

# Estimated fuel consumption per km for each truck (liters/km)
fuel_per_km = [0.40, 0.42, 0.39, 0.45, 0.43]

# Truck capacity for each route
route_capacity = [2, 1, 2]  # how many trucks are required per route (could be demand)

# Build the LP problem to assign trucks to routes minimizing total fuel use
prob = pulp.LpProblem("Minimize_Fuel_Consumption", pulp.LpMinimize)

# Decision variable: x[i][j] = 1 if truck i assigned to route j, else 0
x = [[pulp.LpVariable(f"x_{i}_{j}", cat='Binary') for j in range(routes)] for i in range(truck_count)]

# Objective: Minimize total fuel consumption
prob += pulp.lpSum(x[i][j] * fuel_per_km[i] * distance[j] for i in range(truck_count) for j in range(routes)), "Total_Fuel"

# Constraint: For each route, assign the required number of trucks
for j in range(routes):
    prob += pulp.lpSum(x[i][j] for i in range(truck_count)) == route_capacity[j], f"Route_{j}_capacity"

# Constraint: Each truck assigned to at most one route
for i in range(truck_count):
    prob += pulp.lpSum(x[i][j] for j in range(routes)) <= 1, f"Truck_{i}_one_route"

# Solve the problem
prob.solve()

# Output results
print("Truck Assignments:")
for i in range(truck_count):
    for j in range(routes):
        if pulp.value(x[i][j]) == 1:
            print(f"Truck {i+1} assigned to Route {j+1}")
print(f"Minimum Total Fuel Consumption: {pulp.value(prob.objective):.2f} liters")
