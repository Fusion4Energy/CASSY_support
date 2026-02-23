import pandas as pd
import re
import os
import io
from pathlib import Path

# --- USER INPUTS ---
# the root directory where the stresses folders are located
ROOT_DIR = Path(
    r"C:\\path\\to\\cassy\\assessment\\folder\\"
)  # Change this to your folder

# -- END OF USER INPUTS ---


PAT_DIGIT = re.compile(r"\d+")


def _parse_stresses_txt(
    filepath: os.PathLike, analysis: str, loadstep_str: str, path_name: str
):
    loadstep = PAT_DIGIT.search(loadstep_str)
    if loadstep is None:
        raise ValueError(f"Could not extract loadstep number from {loadstep_str}")
    loadstep = int(loadstep.group())

    path_int = PAT_DIGIT.search(path_name)
    if path_int is None:
        raise ValueError(f"Could not extract path number from {path_name}")
    path_int = int(path_int.group())

    with open(filepath, "r") as f:
        lines = []
        for line in f:
            if line.strip() == "":
                break
            lines.append(line)
    if len(lines) < 2:
        return []

    header = lines[0].strip().split("\t")

    df = pd.read_csv(
        io.StringIO("".join(lines[1:])), sep="\t", names=header, index_col=0
    )

    records = []

    # Always add both begin and end for Membrane
    membrane_row = df.loc["Membrane"]
    for pp in ["begin", "end"]:
        records.append(
            {
                "path": path_int,
                "analysis": analysis,
                "loadstep": loadstep,
                "pathpoint": pp,
                "stress_type": "Pm",
                "Sx": membrane_row["SX"],
                "Sy": membrane_row["SY"],
                "Sz": membrane_row["SZ"],
                "Sxy": membrane_row["SXY"],
                "Sxz": membrane_row["SXZ"],
                "Syz": membrane_row["SYZ"],
            }
        )

    # Bending and Peak rows
    for idx in df.index:
        if idx.startswith("Bending"):
            stype = "Pb"
        elif idx.startswith("Peak"):
            stype = "F"
        else:
            continue
        if "(Inside)" in idx:
            pp = "begin"
        elif "(Outside)" in idx:
            pp = "end"
        else:
            continue
        row = df.loc[idx]
        records.append(
            {
                "path": path_int,
                "analysis": analysis,
                "loadstep": loadstep,
                "pathpoint": pp,
                "stress_type": stype,
                "Sx": row["SX"],
                "Sy": row["SY"],
                "Sz": row["SZ"],
                "Sxy": row["SXY"],
                "Sxz": row["SXZ"],
                "Syz": row["SYZ"],
            }
        )
    return records


all_records = []
# Find all Stresses.txt files
for analysis_dir in ROOT_DIR.iterdir():
    if not analysis_dir.is_dir():
        continue
    for loadstep_dir in analysis_dir.iterdir():
        if not loadstep_dir.is_dir():
            continue
        for path_dir in loadstep_dir.iterdir():
            if not path_dir.is_dir():
                continue
            stresses_path = path_dir / "Stresses.txt"
            if not stresses_path.exists():
                raise FileNotFoundError(f"Expected {stresses_path} to exist")

            analysis = analysis_dir.name
            loadstep = loadstep_dir.name
            path_name = path_dir.name
            recs = _parse_stresses_txt(stresses_path, analysis, loadstep, path_name)
            all_records.extend(recs)


df = pd.DataFrame(
    all_records,
    columns=[
        "path",
        "analysis",
        "loadstep",
        "pathpoint",
        "stress_type",
        "Sx",
        "Sy",
        "Sz",
        "Sxy",
        "Sxz",
        "Syz",
    ],
)
out_csv = ROOT_DIR / "model.csv"
df.to_csv(out_csv, index=False)
print(f"Saved {out_csv}")
