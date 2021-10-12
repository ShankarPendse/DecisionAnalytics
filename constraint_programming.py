import pandas as pd
import numpy as np
from ortools.sat.python import cp_model
import copy


def logical_puzzle():
    names = ["Carol", "Elisa", "Oliver", "Lucas"]
    nationalities = ["Australia", "USA", "SouthAfrica", "Canada"]
    universities = ["London", "Cambridge", "Oxford", "Edinburgh"]
    subjects = ["History", "Law", "Medicine", "Architecture"]
    genders = ["Boy", "Girl"]

    class SolutionPrinter(cp_model.CpSolverSolutionCallback):
        def __init__(self, gender, university, subject, nationality):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.gender_ = gender
            self.university_ = university
            self.subject_ = subject
            self.nationality_ = nationality

            self.solutions_ = 0

        def OnSolutionCallback(self):
            self.solutions_ = self.solutions_ + 1
            print("solution", self.solutions_)

            for name in names:
                print(" - " + name + ":")
                for gender in genders:
                    if self.Value(self.gender_[name][gender]):
                        print("    gender - ", gender)
                for nationality in nationalities:
                    if self.Value(self.nationality_[name][nationality]):
                        print("    nationality - ", nationality)
                for university in universities:
                    if self.Value(self.university_[name][university]):
                        print("    university - ", university)
                for subject in subjects:
                    if self.Value(self.subject_[name][subject]):
                        print("    subject - ", subject)

    model = cp_model.CpModel()
    # Decision variables creation
    student_nationality = {}
    for name in names:
        variables = {}
        for nationality in nationalities:
            variables[nationality] = model.NewBoolVar(name + nationality)
        student_nationality[name] = variables

    student_university = {}
    for name in names:
        variables = {}
        for university in universities:
            variables[university] = model.NewBoolVar(name + university)
        student_university[name] = variables

    student_subject = {}
    for name in names:
        variables = {}
        for subject in subjects:
            variables[subject] = model.NewBoolVar(name + subject)
        student_subject[name] = variables

    student_gender = {}
    for name in names:
        variables = {}
        for gender in genders:
            variables[gender] = model.NewBoolVar(name + gender)
        student_gender[name] = variables

    # Let's assign genders for students
    model.AddBoolAnd([student_gender["Carol"]["Girl"],
                      student_gender["Elisa"]["Girl"],
                      student_gender["Carol"]["Boy"].Not(),
                      student_gender["Elisa"]["Boy"].Not(),
                      student_gender["Oliver"]["Boy"],
                      student_gender["Lucas"]["Boy"],
                      student_gender["Oliver"]["Girl"].Not(),
                      student_gender["Lucas"]["Girl"].Not()
                      ])

    # Constraints based on given sentences
    '''
    1: One of them (students) is going to London: This can be formulated later when we specify exactly one value of 
    each property to each student
    
    '''
    # 2: Exactly one boy and one girl chose a university in a city with the same initial of their names
    model.AddBoolXOr([student_university["Carol"]["Cambridge"], student_university["Elisa"]["Edinburgh"]])
    model.AddBoolXOr([student_university["Lucas"]["London"], student_university["Oliver"]["Oxford"]])

    # 3: A boy is from Australia, the other studies History
    '''
    From assumption, We know that Lucas and Oliver are boys, above sentence implies:
    1) If lucas is from australia, oliver studies history
    2) If Oliver is from australia, Lucas studies history
    3) No girl studies history and No girl is from australia
    '''

    model.AddBoolXOr([student_nationality["Lucas"]["Australia"],
                      student_nationality["Oliver"]["Australia"]])

    model.AddBoolAnd([student_subject["Lucas"]["History"]]). \
        OnlyEnforceIf(student_nationality["Lucas"]["Australia"].Not())

    model.AddBoolAnd([student_subject["Oliver"]["History"]]). \
        OnlyEnforceIf(student_nationality["Oliver"]["Australia"].Not())

    # 4: A girl goes to Cambridge, the other studies Medicine
    '''
    # From assumption, we know that Elisa and Carol are girls, above sentence implies:
    1) Girl who is going to Cambridge is not studying medicine
    2) Girl who is studying medicine is not going to cambridge 
    3) Boys (Lucas and Oliver) do not go to cambridge
    4) Boys (Lucas and Oliver) do not study medicine
    '''
    model.AddBoolXOr([student_university["Carol"]["Cambridge"],
                      student_subject["Carol"]["Medicine"]])

    model.AddBoolAnd([student_university["Elisa"]["Cambridge"]]). \
        OnlyEnforceIf(student_subject["Carol"]["Medicine"])

    model.AddBoolAnd([student_university["Carol"]["Cambridge"]]). \
        OnlyEnforceIf(student_subject["Elisa"]["Medicine"])

    model.AddBoolAnd([student_university["Lucas"]["Cambridge"].Not(),
                      student_university["Oliver"]["Cambridge"].Not(),
                      student_subject["Lucas"]["Medicine"].Not(),
                      student_subject["Oliver"]["Medicine"].Not()])

    # 5: Oliver studies Law or is from USA; He is not from South Africa
    model.AddBoolAnd([student_nationality["Oliver"]["SouthAfrica"].Not()])

    model.AddBoolXOr([student_subject["Oliver"]["Law"],
                      student_nationality["Oliver"]["USA"]])

    model.AddBoolAnd([student_subject["Oliver"]["Law"]]).OnlyEnforceIf(student_nationality["Oliver"]["USA"].Not())

    model.AddBoolAnd([student_nationality["Oliver"]["USA"]]).OnlyEnforceIf(student_subject["Oliver"]["Law"].Not())

    # 6: The student from Canada is a historian or will go to Oxford
    for name in names:
        model.AddBoolOr([student_subject[name]["History"], student_university[name]["Oxford"]]). \
            OnlyEnforceIf(student_nationality[name]["Canada"])

    # 7: The student from South Africa is going to Edinburgh or will study Law
    for name in names:
        model.AddBoolOr([student_subject[name]["Law"], student_university[name]["Edinburgh"]]). \
            OnlyEnforceIf(student_nationality[name]["SouthAfrica"])

    # Every student has at least one property value
    for name in names:
        # every student has a nationality
        variables = []
        for nationality in nationalities:
            variables.append(student_nationality[name][nationality])
        model.AddBoolOr(variables)

        # every student has a university
        variables = []
        for university in universities:
            variables.append(student_university[name][university])
        model.AddBoolOr(variables)

        # every student has a subject
        variables = []
        for subject in subjects:
            variables.append(student_subject[name][subject])
        model.AddBoolOr(variables)

    # Every student has no more than one nationality/university/subject
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            # Since we have 4 different values for nationality, subject and university, we can do it in single for loop
            for k in range(4):
                model.AddBoolOr([student_nationality[names[i]][nationalities[k]].Not(),
                                 student_nationality[names[j]][nationalities[k]].Not()
                                 ])
                model.AddBoolOr([student_subject[names[i]][subjects[k]].Not(),
                                 student_subject[names[j]][subjects[k]].Not()
                                 ])
                model.AddBoolOr([student_university[names[i]][universities[k]].Not(),
                                 student_university[names[j]][universities[k]].Not()
                                 ])

    # All students have different nationality/university/subject
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            # All students have different nationality/university/subject, and we have 4 unique values for each
            # If there are different number of values for each property, then the below for loop will be split/repeated
            for k in range(4):
                model.AddBoolOr([student_nationality[names[i]][nationalities[k]].Not(),
                                 student_nationality[names[j]][nationalities[k]].Not()
                                 ])
                model.AddBoolOr([student_university[names[i]][universities[k]].Not(),
                                 student_university[names[j]][universities[k]].Not()
                                 ])
                model.AddBoolOr([student_subject[names[i]][subjects[k]].Not(),
                                 student_subject[names[j]][subjects[k]].Not()
                                 ])

    solver = cp_model.CpSolver()
    solver.SearchForAllSolutions(model, SolutionPrinter(student_gender, student_university, student_subject,
                                                        student_nationality))
    print()
    for name in names:
        for subject in subjects:
            if solver.Value(student_subject[name][subject]):
                for nationality in nationalities:
                    if solver.Value(student_nationality[name][nationality]):
                        print("The student named " + name + " with NATIONALITY " + nationality + " takes " + subject +
                              " as a SUBJECT")
        if solver.Value(student_subject[name]["Architecture"]):
            for nationality in nationalities:
                if solver.Value(student_nationality[name][nationality]):
                    print("\n")
                    print("*************************ARCHITECTURE STUDENT**************************************")
                    print("The STUDENT named " + name + " with NATIONALITY " + nationality + " Studies ARCHITECTURE")


def solve_sudoku():
    class SolutionPrinter(cp_model.CpSolverSolutionCallback):
        def __init__(self, sudoku_size, sudoku):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.solutions_ = 0
            self.sudoku_ = sudoku
            self.sudoku_size_ = sudoku_size

        def OnSolutionCallback(self):
            sudoku_result = np.zeros((self.sudoku_size_, self.sudoku_size_)).astype(np.int)
            self.solutions_ = self.solutions_ + 1
            print("\nsolution", self.solutions_)

            for i in range(9):
                for j in range(9):
                    sudoku_result[i, j] = int(self.Value(self.sudoku_[i, j]))

            print(sudoku_result)

    sudoku_size = 9
    sub_grid_size = 3
    model = cp_model.CpModel()
    sudoku_grid = np.zeros((sudoku_size, sudoku_size), int)

    print("sudoku grid initialization: \n")
    print(sudoku_grid)

    # Assign the given values at their respective positions in the sudoku grid
    sudoku_grid[1, 0] = 7
    sudoku_grid[1, 2] = 5
    sudoku_grid[2, 1] = 9
    sudoku_grid[2, 6] = 4
    sudoku_grid[1, 4] = 2
    sudoku_grid[0, 7] = 3

    sudoku_grid[3, 5] = 4
    sudoku_grid[3, 8] = 2
    sudoku_grid[4, 1] = 5
    sudoku_grid[4, 2] = 9
    sudoku_grid[4, 3] = 6
    sudoku_grid[4, 8] = 8
    sudoku_grid[5, 0] = 3
    sudoku_grid[5, 4] = 1
    sudoku_grid[5, 7] = 5

    sudoku_grid[6, 0] = 5
    sudoku_grid[6, 1] = 7
    sudoku_grid[6, 4] = 6
    sudoku_grid[6, 6] = 1
    sudoku_grid[7, 3] = 3
    sudoku_grid[8, 0] = 6
    sudoku_grid[8, 3] = 4
    sudoku_grid[8, 8] = 5

    print("\nAfter assigning the given values to the grid: \n")
    print(sudoku_grid)

    '''Dictionary to hold the given values at their respective positions and a new intvar is created for all other 
    positions of sudoku grid'''
    sudoku = {}
    for i in range(sudoku_size):
        for j in range(sudoku_size):
            if sudoku_grid[i, j] != 0:
                sudoku[(i, j)] = sudoku_grid[i, j]
            else:
                sudoku[(i, j)] = model.NewIntVar(1, sudoku_size, 'sudoku[{},{}]'.format(i, j))

    # Constraint to have all different numbers across the rows (all columns)
    for i in range(sudoku_size):
        model.AddAllDifferent([sudoku[i, j] for j in range(sudoku_size)])

    # Constraint to have all different numbers across the columns (all rows)
    for j in range(sudoku_size):
        model.AddAllDifferent([sudoku[i, j] for i in range(sudoku_size)])

    # Constraint to have all different numbers within all the sub grids of sudoku grid
    for grid_row in range(0, sudoku_size, sub_grid_size):
        for grid_col in range(0, sudoku_size, sub_grid_size):
            model.AddAllDifferent(
                [sudoku[grid_row + i, j] for j in range(grid_col, (grid_col + sub_grid_size)) for i in
                 range(sub_grid_size)])

    solver = cp_model.CpSolver()

    solver.SearchForAllSolutions(model, SolutionPrinter(sudoku_size, sudoku))


def project_planning():
    project_jobs_df = pd.read_excel("../Assignment_DA_1_data.xlsx", sheet_name="Projects")
    contractor_job_quotes = pd.read_excel("../Assignment_DA_1_data.xlsx", sheet_name="Quotes")
    project_dependencies = pd.read_excel("../Assignment_DA_1_data.xlsx", sheet_name="Dependencies")
    project_value = pd.read_excel("../Assignment_DA_1_data.xlsx", sheet_name="Value")

    project_jobs_df.rename(columns={"Unnamed: 0": "Projects"}, inplace=True)
    contractor_job_quotes.rename(columns={"Unnamed: 0": "Contractors"}, inplace=True)
    project_value.rename(columns={"Unnamed: 0": "Projects"}, inplace=True)

    project_jobs_df.set_index("Projects", inplace=True)
    contractor_job_quotes.set_index("Contractors", inplace=True)
    project_value.set_index("Projects", inplace=True)

    # Below dictionary stores the month and job for each project
    # each project is a key, and for each project key, there is a dictionary where month is a key and job is a value
    project_jobs_dict = {ind: project_jobs_df.loc[ind].dropna().to_dict() for ind in project_jobs_df.index}

    # Below dictionary stores the list of jobs that each contractor can do
    contractor_job_quotes_dict = {ind: contractor_job_quotes.loc[ind].dropna().to_dict()
                                  for ind in contractor_job_quotes.index}

    # List of projects
    projects = list(project_jobs_dict.keys())
    # List of contractors
    contractors = list(contractor_job_quotes_dict.keys())
    # List of months
    months = list(project_jobs_df.columns)

    project_month_contractor_value_dict = {}  # For each valid contractor project and month combination, store the cost

    # Below dictionary stores the project dependencies if any
    project_dependencies_dict = {}
    for row in range(len(projects)):
        record = project_dependencies.iloc[row, :]
        project_dependent_on = []
        for project in projects:
            if not (record[project] != record[project]):
                project_dependent_on.append(project)
        project_dependencies_dict[record[0]] = project_dependent_on

    project_values_dict = {ind: project_value.loc[ind][0] for ind in project_value.index}

    # Below dictionary stores the list of jobs each contractor can do
    contractor_jobs_dict = {}
    for contractor, job_quote in contractor_job_quotes_dict.items():
        jobs = []
        for job, quote in job_quote.items():
            jobs.append(job)
        contractor_jobs_dict[contractor] = jobs

    # below variable is to hold the values for each project and each job/month which contractors can work
    # Basically holds all the valid combinations for each project and month/job who all can work
    # This will help in deciding who can be allowed further to work on each job of each project
    project_month_contractor = {}
    for proj in project_jobs_dict:
        month_contractor = {}
        for month in project_jobs_dict[proj].keys():
            contractor_list = []
            for contractor in contractors:
                if project_jobs_dict[proj][month] in contractor_jobs_dict[contractor]:
                    contractor_list.append(contractor)
            month_contractor[month] = contractor_list
        project_month_contractor[proj] = month_contractor

    print("\n\nConstructed dictionaries from the given data are: \n")
    print("Project jobs dict: ")
    print(project_jobs_dict)

    print("\nContractor_job_quotes_dict: ")
    print(contractor_job_quotes_dict)

    print("\nProject_dependencies_dict: ")
    print(project_dependencies_dict)

    print("\nproject_values_dict: ")
    print(project_values_dict)

    print("\nProject month/job contractor dict: ")
    for project in project_month_contractor:
        print(project)
        for month in project_month_contractor[project]:
            print("\t", month, ":", project_month_contractor[project][month])

    class SolutionPrinter(cp_model.CpSolverSolutionCallback):
        '''This class is just for printing all possible solutions'''

        def __init__(self, projects, project_month_contractor):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.solutions_ = 0
            self.projects_ = projects
            self.contractor_project_selection = project_month_contractor

        def OnSolutionCallback(self):
            self.solutions_ = self.solutions_ + 1
            print("\nsolution", self.solutions_)
            print("___________________________\n")

            # Sum of valuations for all selected projects.
            projectValuation = 0

            # Sum of contractors valuations that are working for projects.
            totalCost = 0

            # List of projects selected
            projects_selected = []

            for project in project_month_contractor:
                if self.Value(self.projects_[project]):
                    print(project)
                    projects_selected.append(project)
                    projectValuation += project_values_dict[project]
                    for month in project_month_contractor[project]:
                        for contractor in project_month_contractor[project][month]:
                            if self.Value(self.contractor_project_selection[(contractor, project, month)]):
                                print("\t", month, contractor)
                                totalCost += project_month_contractor_value_dict[(contractor, project, month)]

            # Calculating profit margin
            profit_margin = projectValuation - totalCost
            print("\nprofit margin: ", profit_margin)

    model = cp_model.CpModel()

    # Decision variables for what projects to take on
    project_taken_dict_bool_vars = {}
    for project in project_jobs_dict.keys():
        project_taken_dict_bool_vars[project] = model.NewBoolVar(project)

    # Decision variables for Which contractor works on which project and when
    contractor_selection_bool_vars = {}  # Bool variables to decide which valid contractor project month combination to select

    for contractor in contractors:
        jobs = contractor_jobs_dict[contractor]
        temp_project_jobs_dict = copy.deepcopy(project_jobs_dict)  # For every contractor we need to iterate over all projects
        for project, job_month in temp_project_jobs_dict.items():
            for job in list(job_month.values()):
                if job in jobs:
                    m = list(job_month.keys())[list(job_month.values()).index(job)]
                    contractor_project_when = (contractor, project, m, contractor_job_quotes_dict[contractor][job])
                    contractor_selection_bool_vars[contractor_project_when[:-1]] = model. \
                        NewBoolVar(contractor_project_when[0] + contractor_project_when[1] + contractor_project_when[2])
                    project_month_contractor_value_dict[contractor_project_when[:-1]] = contractor_project_when[-1]
                    job_month.pop(m)  # To avoid duplicate entries in the dictionary

    # Contractor can not work on two projects simultaneously
    for contractor in contractors:
        for month in months:
            ''' for each month, contractor project combination must be only one'''
            model.Add(sum(
                [contractor_selection_bool_vars.get((contractor, projects[i], month), False)
                 for i in range(len(projects))]) <= 1
                      )

    # If Project is accepted to be delivered, then exactly one contractor per job of the project needs to work on it
    for project in project_month_contractor:
        for month in project_month_contractor[project]:
            model.Add(sum([contractor_selection_bool_vars[(contractor, project, month)]
                           for contractor in project_month_contractor[project][month]]) == 1). \
                OnlyEnforceIf(project_taken_dict_bool_vars[project])

    # If Project is not taken, then no one should be contracted to work on it
    for project in project_month_contractor:
        for month in project_month_contractor[project]:
            for contractor in project_month_contractor[project][month]:
                model.AddBoolAnd([contractor_selection_bool_vars[(contractor, project, month)].Not()]). \
                    OnlyEnforceIf(project_taken_dict_bool_vars[project].Not())

    # Project Dependency constraint:
    for project in project_dependencies_dict:
        if len(project_dependencies_dict[project]) != 0:
            model.AddBoolAnd(
                [project_taken_dict_bool_vars[project_name] for project_name in project_dependencies_dict[project]]). \
                OnlyEnforceIf(project_taken_dict_bool_vars[project])

    # Profit margin >= 2500
    model.Add(sum([
        (project_values_dict[project] * project_taken_dict_bool_vars[project]) -
        sum([
            int(project_month_contractor_value_dict[(contractor, project, month)])
            * contractor_selection_bool_vars[(contractor, project, month)]
            for month in project_month_contractor[project]
            for contractor in project_month_contractor[project][month]
        ])
        for project in projects
    ]) >= 2500
              )

    solver = cp_model.CpSolver()
    status = solver.SearchForAllSolutions(model, SolutionPrinter(project_taken_dict_bool_vars,
                                                                 contractor_selection_bool_vars))
    print(solver.StatusName(status))


if __name__ == "__main__":
    print("\nTASK1: Logical Puzzle\n")
    logical_puzzle()
    print("_________________________________________________________________________________________________________")

    print("\nTASK2: SUDOKU\n")
    solve_sudoku()
    print("_________________________________________________________________________________________________________")

    print("\nTASK3: Project Planning\n")
    project_planning()
    print("_________________________________________________________________________________________________________")

