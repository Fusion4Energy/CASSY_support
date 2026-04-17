from ansys.mapdl.core import launch_mapdl
from ansys.mapdl.core.mapdl_grpc import MapdlGrpc as Mapdl
import pandas as pd
from pathlib import Path
import logging

# -------------------
# --- User inputs ---
# -------------------

# Dictionary of analyses to process. Key is the name of the analysis (e.g. "Mech")
# and value is the path to the .rst file for that analysis
ANALYSES = {
    "Analysis1": (r"path/to/file.rst", r"path/to/file.cdb"),
}
# path where to dump the final .csv file and APDL log
OUTFOLDER = r"out"

# define the nodes for each path {ID_path: (node1, node2)}
PATH_NODES = {
    1: (4360324, 4358864),
    2: (6645804, 6481684),
}

# number of path points
NDIV = 20

# --------------------------
# --- End of user inputs ---
# --------------------------


def _count_loadsteps(mapdl_instance: Mapdl) -> int:
    """Return the number of load steps (integers) in the analysis"""
    counter = 0
    for time in mapdl_instance.post_processing.time_values:
        # check if integer
        if time.is_integer():
            counter += 1
    return counter


def select_3D_elements_nodes(mapdl: Mapdl) -> None:
    """Selects only 3D elements in a mechanical model and associated nodes"""
    mapdl.esel("NONE")
    for etype in [185, 186, 187]:
        mapdl.esel("A", "ENAME", "", str(etype))
    mapdl.nsle("S")
    logging.info(f"Number of selected nodes: {mapdl.get('_', 'NODE', 0, 'COUNT')}")


def extract_stress_linearization(
    mapdl: Mapdl,
) -> pd.DataFrame:
    """Extract linearized stress data for all loadsteps from the current .rst results

    Parameters
    ----------
    mapdl : Mapdl
        Instance of Mapdl where an .rst file has been already loaded.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the extracted data, with columns: path, loadstep, path_point,
        stress_type, Sx, Sy, Sz, Sxy, Sxz, Syz
    """
    # Enter POST1 for postprocessing
    # mapdl.post1()

    # Delete existing paths
    mapdl.padele("ALL")

    # Define paths
    logging.info("Defining paths...")
    for i_pth, (node1, node2) in PATH_NODES.items():
        # Create path
        mapdl.path(str(i_pth), str(2), str(30), str(NDIV))
        mapdl.ppath(str(1), str(node1))
        mapdl.ppath(str(2), str(node2))

    nsets = _count_loadsteps(mapdl)
    # select nodes
    select_3D_elements_nodes(mapdl)
    # loop through all steps and paths
    dfs = []
    for step in range(1, nsets + 1):
        logging.info(f"Processing load step {step}/{nsets}...")
        for path_id in PATH_NODES.keys():
            # extract the stress components
            mapdl.path(str(path_id))
            mapdl.set(step)
            mapdl.prsect()
            df = _get_lin_stress_components(mapdl, step)
            df["path"] = path_id
            df["loadstep"] = step
            dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def validate_mech_model(mapdl: Mapdl) -> None:
    "Check if model is mechanical, if not, try to convert a thermal into a mech one"
    SOLID_ETYPES = [185, 186, 187]
    # get a list of the element types:
    mapdl.allsel("ALL")
    etypes = set(mapdl.mesh.etype)

    found = False
    for etype in SOLID_ETYPES:
        if etype in etypes:
            found = True
            logging.info(".cdb recognized as a mech model")
            break

    if not found:
        logging.warning("no mech elem type found, trying conversion using ETCHG,TTS")
        mapdl.etchg("TTS")


def _get_lin_stress_components(mapdl: Mapdl, step: int) -> pd.DataFrame:
    """get the linearized stress components for the current path and load step.
    and organize them into a DataFrame"""
    # Get stress components for MEMBRANE
    mx = mapdl.get("MX", "SECTION", "MEMBRANE", "INSIDE", "S", "X")
    my = mapdl.get("MY", "SECTION", "MEMBRANE", "INSIDE", "S", "Y")
    mz = mapdl.get("MZ", "SECTION", "MEMBRANE", "INSIDE", "S", "Z")
    mxy = mapdl.get("MXY", "SECTION", "MEMBRANE", "INSIDE", "S", "XY")
    mxz = mapdl.get("MXZ", "SECTION", "MEMBRANE", "INSIDE", "S", "XZ")
    myz = mapdl.get("MYZ", "SECTION", "MEMBRANE", "INSIDE", "S", "YZ")

    # Get stress components for BENDING INSIDE
    bx_i = mapdl.get("BX_I", "SECTION", "BENDING", "INSIDE", "S", "X")
    by_i = mapdl.get("BY_I", "SECTION", "BENDING", "INSIDE", "S", "Y")
    bz_i = mapdl.get("BZ_I", "SECTION", "BENDING", "INSIDE", "S", "Z")
    bxy_i = mapdl.get("BXY_I", "SECTION", "BENDING", "INSIDE", "S", "XY")
    bxz_i = mapdl.get("BXZ_I", "SECTION", "BENDING", "INSIDE", "S", "XZ")
    byz_i = mapdl.get("BYZ_I", "SECTION", "BENDING", "INSIDE", "S", "YZ")

    # Get stress components for BENDING OUTSIDE
    bx_o = mapdl.get("BX_O", "SECTION", "BENDING", "OUTSIDE", "S", "X")
    by_o = mapdl.get("BY_O", "SECTION", "BENDING", "OUTSIDE", "S", "Y")
    bz_o = mapdl.get("BZ_O", "SECTION", "BENDING", "OUTSIDE", "S", "Z")
    bxy_o = mapdl.get("BXY_O", "SECTION", "BENDING", "OUTSIDE", "S", "XY")
    bxz_o = mapdl.get("BXZ_O", "SECTION", "BENDING", "OUTSIDE", "S", "XZ")
    byz_o = mapdl.get("BYZ_O", "SECTION", "BENDING", "OUTSIDE", "S", "YZ")

    # Get stress components for PEAK INSIDE
    fx_i = mapdl.get("FX_I", "SECTION", "PEAK", "INSIDE", "S", "X")
    fy_i = mapdl.get("FY_I", "SECTION", "PEAK", "INSIDE", "S", "Y")
    fz_i = mapdl.get("FZ_I", "SECTION", "PEAK", "INSIDE", "S", "Z")
    fxy_i = mapdl.get("FXY_I", "SECTION", "PEAK", "INSIDE", "S", "XY")
    fxz_i = mapdl.get("FXZ_I", "SECTION", "PEAK", "INSIDE", "S", "XZ")
    fyz_i = mapdl.get("FYZ_I", "SECTION", "PEAK", "INSIDE", "S", "YZ")

    # Get stress components for PEAK OUTSIDE
    fx_o = mapdl.get("FX_O", "SECTION", "PEAK", "OUTSIDE", "S", "X")
    fy_o = mapdl.get("FY_O", "SECTION", "PEAK", "OUTSIDE", "S", "Y")
    fz_o = mapdl.get("FZ_O", "SECTION", "PEAK", "OUTSIDE", "S", "Z")
    fxy_o = mapdl.get("FXY_O", "SECTION", "PEAK", "OUTSIDE", "S", "XY")
    fxz_o = mapdl.get("FXZ_O", "SECTION", "PEAK", "OUTSIDE", "S", "XZ")
    fyz_o = mapdl.get("FYZ_O", "SECTION", "PEAK", "OUTSIDE", "S", "YZ")

    data = [
        [1, "Pm", mx, my, mz, mxy, mxz, myz],
        [2, "Pm", mx, my, mz, mxy, mxz, myz],
        [1, "Pb", bx_i, by_i, bz_i, bxy_i, bxz_i, byz_i],
        [2, "Pb", bx_o, by_o, bz_o, bxy_o, bxz_o, byz_o],
        [1, "F", fx_i, fy_i, fz_i, fxy_i, fxz_i, fyz_i],
        [2, "F", fx_o, fy_o, fz_o, fxy_o, fxz_o, fyz_o],
    ]

    return pd.DataFrame(
        data,
        columns=["path_point", "stress_type", "Sx", "Sy", "Sz", "Sxy", "Sxz", "Syz"],
    )


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # connect to MAPDL instance
    # launching and connecting to and ASNYS MAPDL instance
    print("Launching MAPDL...")
    mapdl: Mapdl = launch_mapdl(
        run_location=OUTFOLDER,
        # loglevel="INFO",  # decomment in case of errors
        override=True,
    )
    print(mapdl)

    try:
        dfs = []
        for analysis, (rst_file, cdb_file) in ANALYSES.items():
            logging.info(f"Processing analysis {analysis}...")
            logging.info(f"Reading .cdb file {cdb_file}...")

            mapdl.clear()
            mapdl.prep7()
            mapdl.cdread("DB", cdb_file)
            validate_mech_model(mapdl)

            mapdl.finish()

            logging.info(f"Extracting data from {rst_file}...")

            mapdl.post1()
            mapdl.file(rst_file)
            df = extract_stress_linearization(mapdl)
            df["analysis"] = analysis
            dfs.append(df)
        df = pd.concat(dfs, ignore_index=True)
        df.to_csv(Path(OUTFOLDER) / "model.csv", index=False)
    finally:
        # be sure to exit MAPDL even if an error occurs
        print("Closing MAPDL session...")
        mapdl.exit()
