import numpy as np
import pulp
import scipy
from scipy.interpolate import interp1d

#------------------First--------------------
#Using scipy to create a fuel model based on road grade(Steepness)
#Data:[Grade (%), Fuel Burn(Liters/hr)]

rise = float(input("Enter the vertical rise (meter): "))
run = float(input("Enter the horizontal distance (meters): "))
hours = float(input("Enter travel time (hours): "))

# Grade calculation
Grade = (rise/run)*100

Grade_used = max(Grade, 0) #To prevent negative grade

# Fuel burn
Fuel_Burn = 180 + (25 * Grade_used) + (8 *(Grade_used**2))

# Total Fuel
Total_Fuel = Fuel_Burn * hours

# OUTPUTS
print(" RESULTS ")
print (f" RoadGrade: {Grade: .2f}%")
print(f" Fuel Burn rate: {Fuel_Burn: .2f}L/h")
print(f" Total fuel used : {Total_Fuel : .2f}L")



#----------------- Second ---------- ---

def opt_Fleet_dispatch(trucks, shovels):
    "Assign trucks to shovels to minimize TOTAL fleet fuel consumption."
    print("\n" + "="*30)

 #1. first setup the linear Programming Problem
    prob = pulp.LpProblem("Minimize_Fuel_Consumption",pulp.LpMinimize)

 #2. Create a Decision Variable
 # x[(truck_id, shovel_id)] = 1 if truck goes to shovel, 0 otherwise 

    routes = [(t['id'], s['id']) for t in trucks for s in shovels]
    x = pulp.LpVariable.dicts("Routes", routes, cat='Binary')

 #3. Calculate cost of fuel for every possible assignment
    costs = {}
    for t in trucks:
        for s in shovels: 
        #simulate static route data 
            fuel_cost = calculate_route_cost(s['Distance_from_trucks'][t['id']], s['grade to reach'])

        costs[(t['id'], s['id'])] = fuel_cost

 #4. Define Object Function: Sum of (Decision * Cost)
    prob += pulp.lpSum([x[(t['id'], s['id'])] * costs[(t['id'], s['id'])] for t in trucks for s in shovels])


 #5. Define constraints

 # A. Every truck must go to exactly one shovel
    for t in trucks :
        prob += pulp.lpSum(x[(t['id'], s['id'])] for s in shovels) == 1

    # B. Shovel capacity (Load Balancing)
    # A shovel cannot handle more trucks than its queue limit(2)

    for s in shovels:
        prob += pulp.lpSum([x[(t['id'], s['id'])] for t in trucks]) <= s['max_queue']

        #6. solution
        prob.solve()

        #7. Output Results
        print(f"Status: {pulp.LpStatus[prob.status]}")
        print(f"Total Fuel Projected: {pulp.value(prob.objective): .2f}")
        print("_" * 30)
        for t in trucks:
            for s in shovels:
                if x[(t['id'], s['id'])].value()==1:
                    cost = costs[(t['id'], s['id'])]
                    print(f"Truck{t['id']} -> shovel {s['id']} (Cost: {cost: .f}L)")

#3. Simulation data
# 3 trucks and 

    # 1. Define Fleet (Static for now)
    truck_fleet = [
        {'id': 'T1'}, 
        {'id': 'T2'}, 
        {'id': 'T3'}
    ]

    # 2. Define Shovels (Distances are known, but Grade is unknown)
    shovel_data = [
        {'id': 'Shovel_A', 'max_queue': 2, 
         'distance_from_trucks': {'T1': 2.0, 'T2': 5.0, 'T3': 3.0}},
        
        {'id': 'Shovel_B', 'max_queue': 2, 
         'distance_from_trucks': {'T1': 8.0, 'T2': 1.0, 'T3': 9.0}}
    ]

        # 3. ASK USER FOR INPUTS (The Interaction Step)
    print("Please configure the mine environment:")
    for shovel in shovel_data:
        # We ask the user to define the physics for this shovel's location
        user_grade = get_user_grade(shovel['id'])
        shovel['grade_percent'] = user_grade

        # 4. Run Optimization with the user's data
        opt_fleet_dispatch(truck_fleet, shovel_data)