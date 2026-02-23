# CASSY Support

These scripts are used to extract inputs needed for CASSY assessments from FEM simulations. More info on CASSY [here](https://eng-gitlab.f4e.europa.eu/f4e-projects/cassy/-/wikis/home).

Table of contents:

- [Paths](#paths)
    - [APDL](#apdl)
    - [MECHANICAL](#mechanical)
    - [ABAQUS](#abaqus)
- [Bolts](#bolts)
    - [APDL](#apdl-1)
    - [MECHANICAL](#mechanical-1)
    - [ABAQUS](#abaqus-1)


## Paths

The typical CASSY format folderpath for a path assessment is:

```
root
│           
├───config
│       model.xlsx
│                  
└───stresses
        model.csv
```

The file ``model.csv`` is expected to contain the linearized stress tensors at different paths and timesteps to be later used in CASSY. The following scripts help bridging FEM simulations with this kind of input format.

### APDL
An [APDL macro](/paths/SCLs_CASSY.mac) is available to extract linearized stresses in CASSY format. TODO: Improve documentation of the macro, original author: Emilio Garcia.

### MECHANICAL

The script [extract_paths_mechanical.py](/paths/extract_paths_mechanical.py) is meant to be read in the ACT Python console of ANSYS Mechanical and executed (Scripting tab).

Before running:
- ensure to have solved all the analyses/solution combinations you need.
- define your paths by naming them: "path_1", "path_2", etc. **Use this simple "path_<number>" format or the chain will break down the line**.
- define a named selection containing only solid 3D bodies. Needed for the scoping of the paths.

The script will generate linearized stress objects, retrieve the result and
export the stresses automatically for all paths defined by the user.

The following parameters control the script execution:
- ``EXTRACT_FOLDER``: root path to where data should be exported.
- ``TO_EXTRACT``: list of analyses name (i.e. the one in the mechanical tree) where results have to be extracted. Solution combinations objects are accepted.
- ``PATHS_NAMES``: list of names of paths to be extracted. If None, all paths will be automatically detected.
- ``BODIES_SELECTION_NAME``: name of the bodies named selection. This named selection is needed because in case the model has beams or shells, the automatic definition of linearized stress objects would fail.

After the script is executed, the following folder structure should appear:

```
---root
    |---analysis 1
    │   |---Loadstep1
    │       |---Path 1
    │       │     |---Stresses.txt
    ...     ....
```

At this point the various Stresses.txt files will need to be combined to produce the model.csv file in a 
proper CASSY format using [mechanical_to_cassy_paths_format.py](/paths/mechanical_to_cassy_paths_format.py).

This script can be executed from any python environment that has ``pandas`` installed and requires as input parameters only the path to the root folder. A ``model.csv`` file will be dumped in the root folder, ready to be used as CASSY input.

### ABAQUS
TODO

## Bolts
The default CASSY folder structure for bolts assessment is:

```
root.     
├───actions
│       main_bolts.csv
│          
├───config
│       main_bolts.xlsx
│       
├───geometries
│       M12_bolt.xlsx
│       M12_insert.xlsx
│       M3_bolt.xlsx
│       M3_insert.xlsx
│       M5_bolt.xlsx
│       M5_insert.xlsx
│       M8_bolt.xlsx
│       M8_insert.xlsx
```

### APDL
TODO

Until a pure APDL script is uploaded, the one of [beam bolts](#beam-bolts) can be used.

### MECHANICAL
#### beam bolts
For beam bolts a simple [script](/bolts/extract_from_rst.py) is provided that levarages pyMAPDL to read .rst files and extract data trough APDL commands.
This can be used both in Workbench and APDL workflows. It needs to be executed in an environment that has ``pandas`` and ``ansys-mapdl-core`` python package installed. The following inputs are expected from the user:

- *ANALYSES*: a dictionary mapping the names of the different analyses to their .rst file.
- *Beam_IDs*: dictionary mapping each bolt ID to the correspondent mesh element ID where actions need to be extracted.
- *OUTFOLDER*: folder where to dump the resulting .csv file ready for cassy usage.

#### 3D bolts
For a given analysis in ANSYS Mechanical is possible to export a csv file that summarize
all bolts reaction forces at all time steps. By using the ANSYS Mechanical Bolt Tool,
use the reaction probes wizard to select all your bolts, then select the analyses
from which reaction forces have to be extracted, select ALL time points.

![alt text](/readme_pictures/ANSYS_reaction_probes_wizard.png)

After some time, in the SYS-XX/MECH folders of your analyses a csv file will appear with the
following format:

![alt text](/readme_pictures/csv.png)

For each analysis, rename the csv file as Bolt Reactions.csv and organize them in the following
folder structure in root/actions folder:

root.     
├───actions
│   │   
│   ├───THBSL1
│   │       Bolt Reactions.csv
│   │       
│   ├───THOMDSL1
│   │       Bolt Reactions.csv
│   │       
│   └───THONIS
│           Bolt Reactions.csv
│          
├───config
│       main_bolts.xlsx
│       
├───geometries
│       M12_bolt.xlsx
│       M12_insert.xlsx
│       M3_bolt.xlsx
│       M3_insert.xlsx
│       M5_bolt.xlsx
│       M5_insert.xlsx
│       M8_bolt.xlsx
│       M8_insert.xlsx

Now, the script [mechanical_to_cassy_bolts_format.py](/bolts/mechanical_to_cassy_bolts_format.py) will create a proper main_bolts.csv
file in CASSY format, in the actions folder. First, ensure you set your config file name
correctly. The script will ask for the root folder and for all model.xlsx file in 
the config folder, it will extract a model.csv file in actions folder and another file
to associate ANSYS Bolt name to CASSY ID.

### ABAQUS
TODO




