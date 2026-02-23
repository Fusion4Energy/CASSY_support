import os

# --- USER INPUTS ---
# Folder where to extract the lin streses
EXTRACT_FOLDER = "C:\\path\\to\\cassy\\assessment\\folder\\stresses\\model"
# List of analyses to extract. If empty, all analyses will be extracted.
TO_EXTRACT = ["Analysis_name_1", "Analysis_name_2"]
# If None, all paths will be extracted.
PATHS_NAMES = None
# Name of path bodies selection
BODIES_SELECTION_NAME = "path_bodies"
# -- END OF USER INPUTS ---


# --- CODE ---
# get paths
paths = ExtAPI.DataModel.Project.Model.GetChildren(DataModelObjectCategory.Path, True)
path_names = []
for j in range(len(paths)):
    path = paths[j]
    path_names.append(path.Name)

if PATHS_NAMES is not None:
    newpaths = []
    for path in paths:
        if path.Name in PATHS_NAMES:
            newpaths.append(path)

    paths = newpaths


# get analyses
analyses = []

sol_comb = ExtAPI.DataModel.Project.Model.GetChildren(
    DataModelObjectCategory.SolutionCombination, True
)
regular_analyses = ExtAPI.DataModel.Project.Model.GetChildren(
    DataModelObjectCategory.Analysis, True
)

for analyses_list in [sol_comb, regular_analyses]:
    for analysis in analyses_list:
        analysis_name = analysis.Name
        if analysis_name in TO_EXTRACT:
            analyses.append(analysis)

# get the named selection for bodies
ns_object = DataModel.GetObjectsByName(BODIES_SELECTION_NAME)[0]
ids = ns_object.Location.Ids
# Create the SelectionInfo and assign
bodies_selection = ExtAPI.SelectionManager.CreateSelectionInfo(
    SelectionTypeEnum.GeometryEntities
)
bodies_selection.Ids = ids

# Linearized Stresses
for analysis in analyses:
    type = analysis.GetType()

    if type == Ansys.ACT.Automation.Mechanical.SolutionCombination:
        loadsteps = [1]  # TODO solution comb may have more than one step?
    else:
        loadsteps = analysis.StepsEndTime
        loadsteps = [int(step) for step in loadsteps]

    for step in loadsteps:
        lin_stress_dict = {}
        for path in paths:
            path_name = path.Name
            if type == Ansys.ACT.Automation.Mechanical.SolutionCombination:
                lin_stress = analysis.AddLinearizedNormalStress()
            else:
                lin_stress = analysis.Solution.AddLinearizedNormalStress()

            lin_stress.NormalOrientation = NormalOrientationType.ZAxis
            lin_stress.Name = path.Name + " Loadstep " + str(step)
            lin_stress.Location = path
            lin_stress.Location = bodies_selection
            # LinStr[j].CoordinateSystem=CSYSs[CSYS_idx[j]]
            if type == Ansys.ACT.Automation.Mechanical.Analysis:
                lin_stress.DisplayTime = Quantity(str(step) + " [sec]")
            lin_stress_dict[path.Name] = lin_stress

        if type == Ansys.ACT.Automation.Mechanical.SolutionCombination:
            analysis.EvaluateAllResults()
        else:
            analysis.Solution.EvaluateAllResults()

        for path in paths:
            directory = os.path.join(EXTRACT_FOLDER, analysis.Name)
            if not os.path.exists(directory):
                os.makedirs(directory)
            directory = os.path.join(directory, "Loadstep" + str(step))
            if not os.path.exists(directory):
                os.makedirs(directory)
            directory = os.path.join(directory, path.Name)
            if not os.path.exists(directory):
                os.makedirs(directory)
            final_path = os.path.join(directory, "Stresses.txt")
            lin_stress_dict[path.Name].ExportToTextFile(True, final_path)
            lin_stress_dict[path.Name].Delete()
