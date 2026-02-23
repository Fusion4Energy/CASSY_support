import os
import pandas as pd
import csv


def process_bolt_reactions_file(filepath, analysis_name):
    # Skip the first row (header), use the second row as the actual header
    df = pd.read_csv(filepath, header=1)
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    # Keep Ref. Obj. Name for each Body Id
    ref_obj_map = (
        df.drop_duplicates(subset=["Body Id"])[["Body Id", "Ref. Obj. Name"]]
        .set_index("Body Id")["Ref. Obj. Name"]
        .to_dict()
    )
    # Pivot the data to get Force and Moment in columns
    df_pivot = df.pivot_table(
        index=["Body Id", "Time"], columns="Type", values=["X", "Y", "Z"]
    )
    # Flatten MultiIndex columns
    df_pivot.columns = ["{}_{}".format(t, comp) for comp, t in df_pivot.columns]
    df_pivot = df_pivot.reset_index()
    # Add Ref. Obj. Name column by mapping Body Id
    df_pivot["Ref. Obj. Name"] = df_pivot["Body Id"].map(ref_obj_map)
    # Rename columns as needed
    df_pivot["boltID"] = df_pivot["Body Id"]
    df_pivot["loadstep"] = df_pivot["Time"].astype(int)
    df_pivot["analysis"] = analysis_name
    # Map to output columns, fill missing with 0 if necessary
    out = pd.DataFrame(
        {
            "boltID": df_pivot["boltID"],
            "analysis": df_pivot["analysis"],
            "loadstep": df_pivot["loadstep"],
            "Fx": df_pivot.get("Force_X", 0),
            "Fy": df_pivot.get("Force_Y", 0),
            "Fz": df_pivot.get("Force_Z", 0),
            "Mx": df_pivot.get("Moment_X", 0),
            "My": df_pivot.get("Moment_Y", 0),
            "Mz": df_pivot.get("Moment_Z", 0),
        }
    )
    # Also return the mapping for this file
    return out, ref_obj_map


def collect_all_bolt_reactions(root_folder):
    all_data = []
    all_ref_obj_maps = []
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.lower() == "bolt reactions.csv":
                filepath = os.path.join(dirpath, filename)
                # Use the immediate subfolder as analysis name
                analysis_name = os.path.basename(dirpath)
                df, ref_obj_map = process_bolt_reactions_file(filepath, analysis_name)
                all_data.append(df)
                all_ref_obj_maps.append(ref_obj_map)
    if all_data:
        df_all = pd.concat(all_data, ignore_index=True)
        # Renumber boltIDs starting from 1, incrementally, for each unique boltID
        unique_bolts = {
            orig_id: new_id
            for new_id, orig_id in enumerate(sorted(df_all["boltID"].unique()), start=1)
        }
        df_all["boltID"] = df_all["boltID"].map(unique_bolts)
        # Build the final mapping of new boltID to Ref. Obj. Name
        final_ref_obj_map = {}
        for ref_map in all_ref_obj_maps:
            final_ref_obj_map.update(ref_map)
        boltid_to_refobj = {
            unique_bolts[orig_id]: ref_name
            for orig_id, ref_name in final_ref_obj_map.items()
            if orig_id in unique_bolts
        }
        return df_all, boltid_to_refobj
    else:
        return (
            pd.DataFrame(
                columns=[
                    "boltID",
                    "analysis",
                    "loadstep",
                    "Fx",
                    "Fy",
                    "Fz",
                    "Mz",
                    "Mx",
                    "My",
                ]
            ),
            {},
        )


# --- USAGE ---
# Prompt user for root folder
root_folder = "C:\\path\\to\\cassy\\assessment\\folder\\"  # Change this to your folder
user_input = input(
    f"Enter the root folder path (press Enter for default):\n[{root_folder}] "
)
if user_input.strip():
    root_folder = user_input.strip()

config_dir = os.path.join(root_folder, "config")
config_files = [f for f in os.listdir(config_dir) if f.lower().endswith(".xlsx")]
if not config_files:
    raise FileNotFoundError(f"No .xlsx file found in {config_dir}")

# Set actions directory
actions_dir = os.path.join(root_folder, "actions")
os.makedirs(actions_dir, exist_ok=True)

for config_filename in config_files:
    filename_no_ext = os.path.splitext(config_filename)[0]
    output_csv = os.path.join(actions_dir, f"{filename_no_ext}.csv")

    df_all, boltid_to_refobj = collect_all_bolt_reactions(actions_dir)

    # Save to CSV only in the output directory
    df_all.to_csv(output_csv, index=False)
    print(f"Bolt reactions exported to {output_csv}.")

    # Save boltID to Ref. Obj. Name mapping as a separate CSV
    refobj_csv = os.path.join(actions_dir, f"{filename_no_ext}_boltid_refobj.csv")
    with open(refobj_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["boltID", "Ref. Obj. Name"])
        for boltID, refobj in sorted(boltid_to_refobj.items()):
            writer.writerow([boltID, refobj])
    print(f"boltID to Ref. Obj. Name mapping exported to {refobj_csv}.")
