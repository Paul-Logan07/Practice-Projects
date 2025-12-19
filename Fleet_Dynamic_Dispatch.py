import pulp
import numpy as np
from scipy.interpolate import interp1d

# ==========================================
# PART 1: THE PHYSICS ENGINE (Fuel & Speed Models)
# ==========================================

def get_optimal_speed(grade_percent):
    #Using scipy to create a fuel model based on road grade(Steepness)
    # Data Points: [Grade (%), Optimal Speed (km/h)]
    # Steep grades require lower speeds to maintain engine efficiency.
    grades = np.array([0,   5,  10,  15])
    speeds = np.array([40, 25,  12,   8]) # Slower as it gets steeper
    
    # Create an interpolation function (Linear is safer for small datasets)
    speed_curve = interp1d(grades, speeds, kind='linear', fill_value="extrapolate")
    
    return float(speed_curve(grade_percent))

def calculate_fuel_cost(distance_km, grade_percent):

    # 1. Calculate Fuel Burn Rate (Liters/Hour)
    # Using the provided formula 
    grade_used = max(grade_percent, 0) # no negative grades in this simple model
    fuel_burn_rate_lph = 180 + (25 * grade_used) + (8 * (grade_used**2))
    
    # 2. Optimization: Determine Optimal Speed
    # Instead of max speed, we use the efficient speed for this grade
    opt_speed_kmh = get_optimal_speed(grade_used)
    
    # 3. Time Calculation
    if opt_speed_kmh <= 0: return float('inf') # Avoid division by zero
    travel_time_hours = distance_km / opt_speed_kmh
    
    # 4. Total Fuel
    total_fuel_liters = fuel_burn_rate_lph * travel_time_hours
    
    return total_fuel_liters, opt_speed_kmh

def get_user_grade_input(location_id):

    # Ask user for road geometry.

    print(f"\n--- Configure Road to {location_id} ---")
    while True:
        try:
            rise = float(input(f"   Enter vertical rise (m): "))
            run = float(input(f"   Enter horizontal distance (m): "))
            
            if run <= 0:
                print("   Error: Distance must be positive.")
                continue
                
            grade = (rise / run) * 100
            print(f"   -> Calculated Grade: {grade:.2f}%")
            return grade
        except ValueError:
            print("   Invalid input. Please enter numbers.")

# ==========================================
# PART 2: THE DISPATCH OPTIMIZER (PuLP)
# ==========================================

def opt_fleet_dispatch(trucks, shovels):
    print("\n" + "="*40)
    print("      STARTING DISPATCH OPTIMIZATION")
    print("="*40)

    # 1. Setup Linear Programming Problem
    prob = pulp.LpProblem("Minimize_Fuel_Consumption", pulp.LpMinimize)

    # 2. Create Decision Variables
    # Matrix of binary variables: Will Truck T go to Shovel S?
    routes = [(t['id'], s['id']) for t in trucks for s in shovels]
    x = pulp.LpVariable.dicts("Route", routes, cat='Binary')

    # 3. Calculate Cost Matrix (Fuel)
    costs = {}
    speed_log = {} # Just for display purposes
    
    for t in trucks:
        for s in shovels: 
            dist = s['distance_from_trucks'][t['id']]
            grade = s['grade_percent']
            
            # Calculate fuel cost
            fuel_cost, opt_speed = calculate_fuel_cost(dist, grade)
            
            costs[(t['id'], s['id'])] = fuel_cost
            speed_log[(t['id'], s['id'])] = opt_speed

    # 4. Define Objective Function
    # Minimize: Sum of (Selected_Route * Fuel_Cost)
    prob += pulp.lpSum([x[(t['id'], s['id'])] * costs[(t['id'], s['id'])] 
                        for t in trucks for s in shovels])

    # 5. Define Constraints
    # Constraint A: Every truck must be assigned to EXACTLY one shovel
    for t in trucks:
        prob += pulp.lpSum([x[(t['id'], s['id'])] for s in shovels]) == 1

    # Constraint B: Shovel Queue Capacity (Load Balancing)
    # A shovel cannot take more trucks than allowed
    for s in shovels:
        prob += pulp.lpSum([x[(t['id'], s['id'])] for t in trucks]) <= s['max_queue']

    # 6. Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=False)) # msg=False hides solver debug text

    # 7. Output Results
    status = pulp.LpStatus[prob.status]
    print(f"\nOptimization Status: {status.upper()}")
    
    if status == 'Optimal':
        total_fuel = pulp.value(prob.objective)
        print(f"Projected Fleet Fuel Burn: {total_fuel:.2f} Liters")
        print("-" * 40)
        print(f"{'TRUCK':<10} | {'DESTINATION':<15} | {'SPEED':<10} | {'FUEL':<10}")
        print("-" * 40)
        
        for t in trucks:
            for s in shovels:
                if x[(t['id'], s['id'])].value() == 1:
                    cost = costs[(t['id'], s['id'])]
                    spd = speed_log[(t['id'], s['id'])]
                    print(f"{t['id']:<10} | {s['id']:<15} | {spd:.0f} km/h   | {cost:.2f} L")
    else:
        print("No optimal solution found. Check constraints.")

# ==========================================
# PART 3: SIMULATION EXECUTION
# ==========================================

if __name__ == "__main__":
    # 1. Define Resources
    truck_fleet = [
        {'id': 'Truck_1'}, 
        {'id': 'Truck_2'}, 
        {'id': 'Truck_3'}
    ]

    shovel_data = [
        {'id': 'Shovel_A', 'max_queue': 2, 
         'distance_from_trucks': {'Truck_1': 2.0, 'Truck_2': 5.0, 'Truck_3': 3.0}},
        
        {'id': 'Shovel_B', 'max_queue': 2, 
         'distance_from_trucks': {'Truck_1': 8.0, 'Truck_2': 1.0, 'Truck_3': 9.0}}
    ]

    # 2. User Interaction Loop
    print("MINING FLEET DISPATCH SYSTEM")
    print("Configure road conditions for optimization:")
    
    for shovel in shovel_data:
        # Get grade from user
        shovel['grade_percent'] = get_user_grade_input(shovel['id'])

    # 3. Run System
    opt_fleet_dispatch(truck_fleet, shovel_data)
