from ortools.linear_solver import pywraplp
import itertools
import pandas as pd


def task1():
    solver = pywraplp.Solver('LPWrapper', pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
    # A) Load the data
    task1_df = pd.read_excel("../Assignment_DA_2_Task_1_data.xlsx", sheet_name=None)

    supplier_stock = task1_df['Supplier stock']
    raw_material_costs = task1_df['Raw material costs']
    raw_material_shipping = task1_df['Raw material shipping']
    product_requirements = task1_df['Product requirements']
    production_capacity = task1_df['Production capacity']
    production_cost = task1_df['Production cost']
    customer_demand = task1_df['Customer demand']
    shipping_costs = task1_df['Shipping costs']

    supplier_stock.rename(columns={"Unnamed: 0": "suppliers"}, inplace=True)
    raw_material_costs.rename(columns={"Unnamed: 0": "suppliers"}, inplace=True)
    raw_material_shipping.rename(columns={"Unnamed: 0": "suppliers"}, inplace=True)
    product_requirements.rename(columns={"Unnamed: 0": "products"}, inplace=True)
    production_capacity.rename(columns={"Unnamed: 0": "products"}, inplace=True)
    production_cost.rename(columns={"Unnamed: 0": "products"}, inplace=True)
    customer_demand.rename(columns={"Unnamed: 0": "products"}, inplace=True)
    shipping_costs.rename(columns={"Unnamed: 0": "factories"}, inplace=True)

    supplier_stock.set_index('suppliers', inplace=True)
    raw_material_costs.set_index('suppliers', inplace=True)
    raw_material_shipping.set_index('suppliers', inplace=True)
    product_requirements.set_index('products', inplace=True)
    production_capacity.set_index('products', inplace=True)
    production_cost.set_index('products', inplace=True)
    customer_demand.set_index('products', inplace=True)
    shipping_costs.set_index('factories', inplace=True)

    # Get the list of suppliers, materials, factories, products and customers
    suppliers = list(supplier_stock.index)
    materials = list(supplier_stock.columns)
    factories = list(raw_material_shipping.columns)
    products = list(product_requirements.index)
    customers = list(customer_demand.columns)

    print("Supplier Stock: \n", supplier_stock)
    print("\nRaw material cost: \n", raw_material_costs)
    print("\nraw_material_shipping: \n", raw_material_shipping)
    print("\nproduct_requirements: \n", product_requirements)
    print("\nproduction_capacity: \n", production_capacity)
    print("\nproduction_cost: \n", production_cost)
    print("\ncustomer_demand: \n", customer_demand)
    print("\nshipping_costs: \n", shipping_costs)

    # B) Decision variables for orders from factories (Factories can order raw materials from multiple suppliers)
    # From the data, we can clearly see that every factory needs all raw materials
    order_from_factory_to_supplier = {}
    for supplier in suppliers:
        for material in materials:
            if not pd.isnull(supplier_stock.loc[supplier, material]):
                # E) Define and implement the constraints that ensure suppliers have all ordered items in stock (add constraint)
                c = solver.Constraint(0, supplier_stock.loc[supplier, material])
                for factory in factories:
                    order_from_factory_to_supplier[(material, factory, supplier)] = solver.NumVar(0, solver.infinity(), material+'_'+factory+'_'+supplier)
                    # E) Define and implement the constraints that ensure suppliers have all ordered items in stock (add coeff)
                    c.SetCoefficient(order_from_factory_to_supplier[(material, factory, supplier)], 1)

    print("len of order dec variable: ", len(order_from_factory_to_supplier))
    # print("\n order dec variables: ", order_from_factory_to_supplier)

    # B) Decision variables for production volume, each factory has its own capacity to produce the products
    production_volume = {}
    for factory in factories:
        for product in products:
            if not pd.isnull(production_capacity.loc[product, factory]):
                production_volume[(product, factory)] = solver.NumVar(0, solver.infinity(), factory+'_'+product)
                # G) Define and implement the constraint that ensures manufacturing capacities are not exceeded
                c = solver.Constraint(0, production_capacity.loc[product, factory])
                c.SetCoefficient(production_volume[(product, factory)], 1)

    print("len of production_volume dec variable: ", len(production_volume))

    # print("\n production volume dec vars: ", production_volume)

    # B) Decision variables for delivery to customers
    deliver_products_from_factories_to_customers = {}
    for customer in customers:
        for product in products:
            if not pd.isnull(customer_demand.loc[product, customer]):
                # D) Define and implement the constraint that ensures customer demand is met (add constraint)
                c = solver.Constraint(int(customer_demand.loc[product, customer]), int(customer_demand.loc[product, customer]))
                for factory in factories:
                    if not pd.isnull(production_capacity.loc[product, factory]):
                        deliver_products_from_factories_to_customers[(product, factory, customer)] = solver.NumVar(0, solver.infinity(), product+'_'+factory+'_'+customer)
                        # D) Define and implement the constraint that ensures customer demand is met (set the coeff)
                        c.SetCoefficient(deliver_products_from_factories_to_customers[(product, factory, customer)], 1)

                        # c) Define and implement the constraint that ensures factories produce more than they ship to customers
                        # Factories have the limit on production capacity, so we have to do it the other way round
                        # Factories should deliver less than what their production capacity is
                        d = solver.Constraint(1, solver.infinity())
                        d.SetCoefficient(production_volume[(product, factory)], 1)
                        d.SetCoefficient(deliver_products_from_factories_to_customers[(product, factory, customer)], -1)

    print("len of delivery dec variable: ", len(deliver_products_from_factories_to_customers))
    # print("\n deliver dec variable: ", deliver_products_from_factories_to_customers)


    # F) Define and implement constraint that ensures factories order enough material to be able to manufacture all items
    for factory in factories:
        for material in materials:
            c = solver.Constraint(0, solver.infinity())
            for supplier in suppliers:
                if not pd.isnull(supplier_stock.loc[supplier, material]):
                    c.SetCoefficient(order_from_factory_to_supplier[(material, factory, supplier)], 1)
            for product in products:
                if not pd.isnull(product_requirements.loc[product, material]):
                    if not pd.isnull(production_capacity.loc[product, factory]):
                        # After producing the required quantity utilizing 'n' units of respective raw materials, factories should not run out of materials in -ve quantity, so we are adding the utilized quantities and subtracting it from the ordered stock of raw materials
                        c.SetCoefficient(production_volume[(product, factory)], -product_requirements.loc[product, material])

    # H) Define and implement the objective function. Make sure to consider the supplier bills comprising shipping and material costs the production cost of each factory and the cost of delivery to each customer
    cost = solver.Objective()

    # Cost to factory (Raw material cost + shipping cost)
    for supplier in suppliers:
        for material in materials:
            if not pd.isnull(supplier_stock.loc[supplier, material]):
                for factory in factories:
                    cost.SetCoefficient(order_from_factory_to_supplier[(material, factory, supplier)],
                                        raw_material_costs.loc[supplier, material] + raw_material_shipping.loc[supplier, factory])

    # Cost to factory (Production cost)
    for factory in factories:
        for product in products:
            if not pd.isnull(production_capacity.loc[product, factory]):
                cost.SetCoefficient(production_volume[(product, factory)], production_cost.loc[product, factory])

    # Cost on shipping to customers
    for customer in customers:
        for product in products:
            if not pd.isnull(customer_demand.loc[product, customer]):
                for factory in factories:
                    if not pd.isnull(production_capacity.loc[product, factory]):
                        cost.SetCoefficient(deliver_products_from_factories_to_customers[(product, factory, customer)], int(shipping_costs.loc[factory, customer]))

    # I) Solve linear program and determine the overall optimal cost
    print("\nSolving the objective function")
    cost.SetMinimization()
    status = solver.Solve()
    if status == solver.OPTIMAL:
        print("Optimal solution found")
        print("Total cost: ", solver.Objective().Value(), "\n")
    else:
        print("Failed to find the solution")
        exit()

    # J) Determine for each factory how much material has to be ordered from each individual supplier
    print("SUB TASK J: Below guidelines must be followed to achieve the minimum cost: ")
    print("*******************************************************************************")
    for key, value in order_from_factory_to_supplier.items():
        if order_from_factory_to_supplier[key].solution_value() > 0:
            print("For factory {},  {} units of {} needs to be ordered from {}".format(key[1], int(order_from_factory_to_supplier[key].solution_value()), key[0], key[-1]))
    print("\n")

    # K) Determine for each factory what the supplier bill comprising material cost and delivery will be from each supplier
    print("SUB TASK K: Bill for each factory from suppliers:")
    print("****************************************")
    for factory in factories:
        for supplier in suppliers:
            supplier_bill = 0
            for material in materials:
                if not pd.isnull(supplier_stock.loc[supplier, material]):
                    if order_from_factory_to_supplier[(material, factory, supplier)].solution_value() > 0:
                        supplier_bill += order_from_factory_to_supplier[(material, factory, supplier)].solution_value() * raw_material_costs.loc[supplier, material]
                        supplier_bill += order_from_factory_to_supplier[(material, factory, supplier)].solution_value() * raw_material_shipping.loc[supplier, factory]
            if supplier_bill:
                print("For {} total bill from {} is : {}".format(factory, supplier, supplier_bill))
        print("\n")

    # L) Determine for each factory, how many units of each product are being manufactured and total manufacturing cost for each factory
    print("SUB TASK L: Determine for each factory, how many units of each product are being manufactured and total manufacturing cost for each factory")
    print("******************************************************************************************************************************************")
    for factory in factories:
        manufacturing_cost = 0
        for product in products:
            if not pd.isnull(production_capacity.loc[product, factory]):
                if production_volume[(product, factory)].solution_value() > 0:
                    print(factory, "produces", int(production_volume[(product, factory)].solution_value()), "units of ", product)
                    manufacturing_cost += int(production_volume[(product, factory)].solution_value()) * production_cost.loc[product, factory]
        print("Total manufacturing cost for {} is: {}".format(factory, manufacturing_cost))
        print("\n")

    # M) Determine for each customer how many units of each product are being shipped from each factory and also determine the total shipping cost per customer
    print("SUB TASK M: Determine for each customer how many units of each product are being shipped from each factory and also determine the total shipping cost per customer")
    print("****************************************************************************************************************************************************************************************")
    for customer in customers:
        print("For ", customer, end='\n')
        shipping_cost = 0
        for product in products:
            if not pd.isnull(customer_demand.loc[product, customer]):
                print("\t", product, "is being delivered ", end="\n")
                for factory in factories:
                    # product_count_for_each_factory = 0
                    if not pd.isnull(production_capacity.loc[product, factory]):
                        # product_count_for_each_factory += deliver_products_from_factories_to_customers[(product, factory, customer)].solution_value()
                        if deliver_products_from_factories_to_customers[(product, factory, customer)].solution_value() > 0:
                            shipping_cost += int(deliver_products_from_factories_to_customers[(product, factory, customer)].solution_value()) * shipping_costs.loc[factory, customer]
                            print("\t\tin ", int(deliver_products_from_factories_to_customers[(product, factory, customer)].solution_value()), " units from ", factory)
        print("\nTotal shipping cost for {} is: {}".format(customer, shipping_cost))
        print("\n")

    # N) Determine for each customer the fraction of each material each factory has to order for manufacturing products delivered to that particular customer
    print("SUB TASK N: Determine for each customer the fraction of each material each factory has to order for manufacturing products delivered to that particular customer")
    print("********************************************************************************************************************************************************************************************")
    for customer in customers:
        print("For ", customer, end="\n")
        for product in products:
            if not pd.isnull(customer_demand.loc[product, customer]):
                print("\t on ", product, end='\n')
                for factory in factories:
                    if not pd.isnull(production_capacity.loc[product, factory]):
                        if deliver_products_from_factories_to_customers[(product, factory, customer)].solution_value() > 0:
                            print("\t\t", factory, "has to order ", end='\n')
                            for material in materials:
                                if not pd.isnull(product_requirements.loc[product, material]):
                                    print("\t\t\t", int(deliver_products_from_factories_to_customers[(product, factory, customer)].solution_value()) * product_requirements.loc[product, material], "units of ", material)

    # N) calculate the overall unit cost of each product per customer including the raw materials used for the manufacturing of the customer’s specific product, the cost of manufacturing for the specific customer and all relevant shipping costs
    print("\nSUB TASK N: unit cost of each product per customer")
    print("************************************************")
    for customer in customers:
        print("For ", customer, end='\n')
        # shipping_cost = 0
        for product in products:
            if not pd.isnull(customer_demand.loc[product, customer]):
                print("\tFor ", product, end='\n')
                # unit_cost = 0
                for factory in factories:
                    unit_cost = 0
                    # product_count_for_each_factory = 0
                    if not pd.isnull(production_capacity.loc[product, factory]):
                        if deliver_products_from_factories_to_customers[(product, factory, customer)].solution_value() > 0:
                            for material in materials:
                                if not pd.isnull(product_requirements.loc[product, material]):
                                    for supplier in suppliers:
                                        if not pd.isnull(supplier_stock.loc[supplier, material]):
                                            if order_from_factory_to_supplier[(material, factory, supplier)].solution_value() > 0:
                                                unit_cost += product_requirements.loc[product, material] * raw_material_costs.loc[supplier, material]
                                                unit_cost += raw_material_shipping.loc[supplier, factory]
                            unit_cost += production_cost.loc[product, factory]
                            unit_cost += shipping_costs.loc[factory, customer]
                            print("\t\tUnit cost from {} is: {}".format(factory, unit_cost))
        print("\n")


def task2():
    task2_df = pd.read_excel("../Assignment_DA_2_Task_2_data.xlsx", sheet_name=None)
    solver = pywraplp.Solver('TSPSolver', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    distances = task2_df['Distances']
    distances.rename(columns={'Unnamed: 0': 'city'}, inplace=True)
    distances.set_index('city', inplace=True)

    start_city = 'Cork'
    end_city = start_city
    cities_to_visit = ['Cork', 'Athlone', 'Belfast', 'Dublin', 'Galway', 'Limerick', 'Rosslare', 'Waterford', 'Wexford', 'Wicklow']

    # A) For each pair of towns that need to be visited create a decision variable to decide if this leg should be included into the route
    city_pair = {}
    for i in range(len(cities_to_visit)):
        for j in range(len(cities_to_visit)):
            if i == j:
                continue
            city_pair[(cities_to_visit[i], cities_to_visit[j])] = solver.IntVar(0, 1, cities_to_visit[i]+'_'+cities_to_visit[j])

    city_variable = {}
    for city in cities_to_visit:
        city_variable[city] = solver.IntVar(0, 1, city)

    # B) Define and implement the constraints that ensure that the delivery driver arrives in each of the towns that need to be visited
    for i in range(len(cities_to_visit)):
        solver.Add(sum([city_pair[(cities_to_visit[i], cities_to_visit[j])] for j in range(len(cities_to_visit)) if i != j]) == 1)

    # C) Define and implement the constraints that ensure that the driver departs each of the towns that need to be visited
    for j in range(len(cities_to_visit)):
        solver.Add(sum([city_pair[(cities_to_visit[i], cities_to_visit[j])] for i in range(len(cities_to_visit)) if j != i]) == 1)

    # D) Define and implement the constraints that ensure that there are no disconnected self-contained circles in the route
    for i in range(1, len(cities_to_visit)):
        for j in range(1, len(cities_to_visit)):
            if i == j:
                continue
            solver.Add(((city_variable[cities_to_visit[i]] - city_variable[cities_to_visit[j]]) + (len(cities_to_visit)*city_pair[(cities_to_visit[i], cities_to_visit[j])])) <= (len(cities_to_visit) - 1))

    for j in range(1, len(cities_to_visit)):
        for i in range(1, len(cities_to_visit)):
            if i == j:
                continue
            solver.Add(((city_variable[cities_to_visit[i]] - city_variable[cities_to_visit[j]]) + (len(cities_to_visit)*city_pair[(cities_to_visit[i], cities_to_visit[j])])) <= (len(cities_to_visit) - 1))

    # Define and solve the objective
    cost = solver.Objective()
    for i in range(len(cities_to_visit)):
        for j in range(len(cities_to_visit)):
            if i == j:
                continue
            cost.SetCoefficient(city_pair[cities_to_visit[i], cities_to_visit[j]],
                                int(sum([distances.loc[cities_to_visit[i], cities_to_visit[j]]])))

    cost.SetMinimization()
    status = solver.Solve()

    print(status)
    if status == solver.OPTIMAL:
        print("Optimal solution found")
        print("Total cost: ", solver.Objective().Value(), "\n")

    if status != solver.OPTIMAL:
        print("Failed to find solution")


def task3():
    task3_df = pd.read_excel("../Assignment_DA_2_Task_3_data.xlsx", sheet_name=None)
    flight_schedule = task3_df['Flight schedule']
    taxi_distances = task3_df['Taxi distances']
    terminal_capacity = task3_df['Terminal capacity']

    flight_schedule.rename(columns={"Unnamed: 0": "flights"}, inplace=True)
    taxi_distances.rename(columns={"Unnamed: 0": "runway"}, inplace=True)
    terminal_capacity.rename(columns={"Unnamed: 0": "terminal"}, inplace=True)

    flight_schedule.set_index('flights', inplace=True)
    taxi_distances.set_index('runway', inplace=True)
    terminal_capacity.set_index('terminal', inplace=True)

    print("Flight schedule: \n")
    print(flight_schedule)
    print("\ntaxi distances: \n")
    print("\n", taxi_distances)
    print("\nterminal capacity: \n")
    print("\n", terminal_capacity)

    flights = list(flight_schedule.index)
    terminals = list(terminal_capacity.index)
    runways = list(taxi_distances.index)

    arrival_times = list(set(flight_schedule['Arrival']))
    departure_times = list(set(flight_schedule['Departure']))

    solver = pywraplp.Solver('AirportTaxiway', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    # B) Identify and create the decision variables for the arrival runway allocation, departure allocation and terminal allocation
    arrival_runway_allocation_dec_var = {}
    departure_runway_allocation_dec_var = {}
    terminal_allocation_dec_var = {}
    for flight in flights:
        for runway in runways:
            arrival_runway_allocation_dec_var[(flight, runway)] = solver.IntVar(0, 1, "arr_"+flight+"_"+runway)
            departure_runway_allocation_dec_var[(flight, runway)] = solver.IntVar(0, 1, "dep_"+flight+"_"+runway)
        for terminal in terminals:
            terminal_allocation_dec_var[(flight, terminal)] = solver.IntVar(0, 1, flight+"_"+terminal)

    print("\nno of arr run alloc dec vars: ", len(arrival_runway_allocation_dec_var))
    print("no of dep run alloc dec vars: ", len(departure_runway_allocation_dec_var))
    print("no of term alloc dec vars: ", len(terminal_allocation_dec_var))

    # C) Define and create auxiliary variables for the taxi movements between runways and terminals for each flight
    runway_to_terminal = {}
    terminal_to_runway = {}
    for flight in flights:
        for runway in runways:
            # F) Define and implement the constraints that ensure that the taxi movements of a flight includes the allocated arrival and departure runways
            c = solver.Constraint(0, 0)
            d = solver.Constraint(0, 0)

            c.SetCoefficient(arrival_runway_allocation_dec_var[(flight, runway)], 1)
            d.SetCoefficient(departure_runway_allocation_dec_var[(flight, runway)], 1)

            for terminal in terminals:
                runway_to_terminal[(flight, runway, terminal)] = solver.IntVar(0, 1, flight+"_"+runway+"_to_"+terminal)
                terminal_to_runway[(flight, terminal, runway)] = solver.IntVar(0, 1, flight+"_"+terminal+"_to_"+runway)

                # F) Define and implement the constraints that ensure that the taxi movements of a flight includes the allocated arrival and departure runways
                c.SetCoefficient(terminal_to_runway[(flight, terminal, runway)], -1)
                d.SetCoefficient(runway_to_terminal[(flight, runway, terminal)], -1)

    # D) Define and implement the constraints that ensure that every flight has exactly two taxi movements
    # Sum of runway to terminal and terminal to runway variables for each flight must be equal to 2
    for flight in flights:
        solver.Add(sum(runway_to_terminal[(flight, runway, terminal)] for runway in runways for terminal in terminals) == 1)
        solver.Add(sum(terminal_to_runway[(flight, terminal, runway)] for terminal in terminals for runway in runways) == 1)

    # E) Define and implement the constraints that ensure that the taxi movements of a flight are to and from the allocated terminal
    for flight in flights:
        # G) Define and implement the constraints that ensure that each flight has exactly one allocated arrival runway and exactly one allocated departure runway
        solver.Add(sum(arrival_runway_allocation_dec_var[(flight, runway)] for runway in runways) == 1)
        solver.Add(sum(departure_runway_allocation_dec_var[(flight, runway)] for runway in runways) == 1)
        for terminal in terminals:
            c = solver.Constraint(0, 0)
            d = solver.Constraint(0, 0)

            # arriving to terminal
            c.SetCoefficient(terminal_allocation_dec_var[(flight, terminal)], 1)

            # departing from terminal
            d.SetCoefficient(terminal_allocation_dec_var[(flight, terminal)], -1)

            for runway in runways:
                # depart from terminal
                c.SetCoefficient(terminal_to_runway[(flight, terminal, runway)], -1)

                # arrive at terminal
                d.SetCoefficient(runway_to_terminal[(flight, runway, terminal)], 1)

        # H) Define and implement the constraints the ensure that each flight is allocated to exactly one terminal
        solver.Add(sum(terminal_allocation_dec_var[(flight, terminal)] for terminal in terminals) == 1)

    # I) Define and implement the constraints that ensure that no runway is used by more than one flight during each timeslot
    time_slots = arrival_times + departure_times
    for runway in runways:
        for time in time_slots:
            c = solver.Constraint(0, 1)
            for flight in flights:
                if time == flight_schedule.loc[flight, 'Arrival']:
                    c.SetCoefficient(arrival_runway_allocation_dec_var[(flight, runway)], 1)
                    c.SetCoefficient(departure_runway_allocation_dec_var[(flight, runway)], 0)
                elif time == flight_schedule.loc[flight, 'Departure']:
                    c.SetCoefficient(arrival_runway_allocation_dec_var[(flight, runway)], 0)
                    c.SetCoefficient(departure_runway_allocation_dec_var[(flight, runway)], 1)

    # J) Define and implement the constraints that ensure that the terminal capacities are not exceeded
        # We have to ensure that for each terminal at any given point of time, only those many number of flights are allotted as much as its capacity
    for terminal in terminals:
        for time in time_slots:
            c = solver.Constraint(0, int(terminal_capacity.loc[terminal, 'Gates']))
            for flight in flights:
                # if flight has already arrived and if there is still time for flight to depart, then we have to allot a terminal to it
                if flight_schedule.loc[flight, 'Arrival'] <= time < flight_schedule.loc[flight, 'Departure']:
                    c.SetCoefficient(terminal_allocation_dec_var[(flight, terminal)], 1)
                else:
                    c.SetCoefficient(terminal_allocation_dec_var[(flight, terminal)], 0)

    # K) Define and implement the objective function, Solve the linear program and determine the optimal total taxi distances for all flights
    distance = solver.Objective()
    for flight in flights:
        for runway in runways:
            for terminal in terminals:
                distance.SetCoefficient(runway_to_terminal[(flight, runway, terminal)], int(taxi_distances.loc[runway, terminal]))
                distance.SetCoefficient(terminal_to_runway[(flight, terminal, runway)], int(taxi_distances.loc[runway, terminal]))

    distance.SetMinimization()
    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print("\nOptimal solution found and objective value (total taxi distance for all flights) = ", solver.Objective().Value())
    else:
        print("Failed to find the solution")
        exit()

    # L) Determine arrival runway allocation for each flight
    print("\nArrival Runway allocations: ")
    print("***********************************************\n")
    for key in arrival_runway_allocation_dec_var.keys():
        if arrival_runway_allocation_dec_var[key].solution_value() > 0:
            print(key[0], "is permitted to land on : ", key[1])

    # L) Determine departure runway allocation for each flight
    print("\nDeparture Runway allocations: ")
    print("***********************************************\n")
    for key in departure_runway_allocation_dec_var.keys():
        if departure_runway_allocation_dec_var[key].solution_value() > 0:
            print(key[0], "takes off from : ", key[1])

    # L) Determine terminal allocation for each flight
    print("\nTerminal allocations: ")
    print("***********************************************\n")
    for key in terminal_allocation_dec_var.keys():
        if terminal_allocation_dec_var[key].solution_value() > 0:
            print(key[1], "has been allotted to : ", key[0])

    # L) Determine taxi distance for each flight
    print("\nTaxi distances for each flight: ")
    print("***********************************************\n")
    tot_taxi_distance = 0       # This should match the value of solver objective
    for flight in flights:
        taxi_distance = 0
        print("Total Taxi distance for ", flight, "is = ", end='\t')
        for runway in runways:
            for terminal in terminals:
                if runway_to_terminal[(flight, runway, terminal)].solution_value() > 0:
                    taxi_distance += taxi_distances.loc[runway, terminal]
                if terminal_to_runway[(flight, terminal, runway)].solution_value() > 0:
                    taxi_distance += taxi_distances.loc[runway, terminal]
        print(taxi_distance)
        tot_taxi_distance += taxi_distance

    assert tot_taxi_distance == solver.Objective().Value()
    print("\nTotal taxi distance for all flights: ", tot_taxi_distance)

    # M) Determine for each time of the day how many gates are occupied at each terminal
    print("\nGates occupancy at each terminal: ")
    print("***********************************************\n")
    for time in time_slots:
        print("@ ", time)
        for terminal in terminals:
            print("\t", terminal, "has ", end='\t')
            no_of_occupied_gates = 0
            for flight in flights:
                if terminal_allocation_dec_var[(flight, terminal)].solution_value() > 0:
                    if flight_schedule.loc[flight, 'Arrival'] <= time < flight_schedule.loc[flight, 'Departure']:
                        no_of_occupied_gates += 1
            print(no_of_occupied_gates, "occupied")


if __name__ == "__main__":
    print("Solving Supplier chain management problem: \n")
    print("___________________________________________________________________________________________________________")
    task1()
    task2()
    print("Solving Airport Taxiway Minimization problem: \n")
    print("___________________________________________________________________________________________________________")
    task3()
