from ansys.mapdl.core import launch_mapdl, Mapdl
from pathlib import Path
import pandas as pd

# --- User inputs ---
# Dictionary of analyses to process. Key is the name of the analysis (e.g. "Mech")
# and value is the path to the .rst file for that analysis
ANALYSES = {
    "Mech": r"path/to/rstfile1",
    "Analysis2": r"path/to/rstfile2",
}
# path where to dump the final .csv file
OUTFOLDER = r"path/to/output/folder"

# Dictionary of beam element IDs to process. Key is the ID number of the beam
# and value is the mesh element ID
Beam_IDs = {1: 14684, 2: 14676}
# --- End of user inputs ---


# --- Code ---
def count_loadsteps(mapdl_instance: Mapdl) -> int:
    """Retunn the number of load steps (integers) in the analysis"""
    counter = 0
    for time in mapdl_instance.post_processing.time_values:
        # check if integer
        if time.is_integer():
            counter += 1
    return counter


def get_actions(mapdl_instance: Mapdl, elem_id: int, loadstep: int) -> dict:
    """Extract forces and moments acting on a beam element

    Parameters
    ----------
    mapdl_instance : Mapdl
        connection to the MAPDL instance/license
    elem_id : int
        ID of the element for which to extract forces and moments
    loadstep : int
        step number for which to extract forces and moments

    Returns
    -------
    dict
        dictionary containing the extracted forces and moments
    """
    mapdl_instance.set(loadstep)
    fz = mapdl_instance.get_value(
        entity="ELEM", entnum=elem_id, item1="SMISC", it1num=1
    )
    mx = mapdl_instance.get_value(
        entity="ELEM", entnum=elem_id, item1="SMISC", it1num=2
    )
    my = mapdl_instance.get_value(
        entity="ELEM", entnum=elem_id, item1="SMISC", it1num=3
    )
    mz = mapdl_instance.get_value(
        entity="ELEM", entnum=elem_id, item1="SMISC", it1num=4
    )
    fx = mapdl_instance.get_value(
        entity="ELEM", entnum=elem_id, item1="SMISC", it1num=5
    )
    fy = mapdl_instance.get_value(
        entity="ELEM", entnum=elem_id, item1="SMISC", it1num=6
    )
    row = {"Fz": fz, "Mx": mx, "My": my, "Mz": mz, "Fx": fx, "Fy": fy}
    return row


# connect to MAPDL instance
# launching and connecting to and ASNYS MAPDL instance
print("Launching MAPDL...")
mapdl = launch_mapdl()
print(mapdl)


# Enter POST1 and read results file
try:
    mapdl.post1()
    all_results = []
    for analysis, rst_file in ANALYSES.items():
        print(f"Processing {analysis}...")
        mapdl.file(rst_file)

        # Get number of load steps
        nsets = count_loadsteps(mapdl)

        for step in range(1, nsets + 1):
            for beam_id, elem_id in Beam_IDs.items():
                row = get_actions(mapdl, elem_id, step)
                row["boltID"] = beam_id
                row["loadstep"] = step
                row["analysis"] = analysis
                all_results.append(row)

    df = pd.DataFrame(all_results)
    outfile = Path(OUTFOLDER) / "beam_actions.csv"
    df.to_csv(outfile, index=False)
    print("All done!")
finally:
    # be sure to exit MAPDL even if an error occurs
    print("Closing MAPDL session...")
    mapdl.exit()
