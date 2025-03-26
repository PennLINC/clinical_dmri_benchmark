# This script requires the csv files containing the dice sores between any two scans
# These csvs are generated using the following script: analysis/dice_scores/calculate_dice_scores.sh
# Since there are very many dice scores per bundle per reconstruction method,
# this script takes quite long to run and requires a lot (~20GB) of memory

import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt

# Define reconstruction
# This code needs to be run for all three reconstruction methods: GQI, CSD and SS3T
RECONSTRUCTION = "SS3T"


def read_bundle_txt(path_to_bundle_list: str) -> list:
    """Reads a text file of all reconstructed bundle names and returns a python list

    Args:
    path_to_bundle_list: Path to the txt file containing names from reconstructed bundles
                         Each bundle name is expected to be in a new line
    Returns:
    List of bundle names
    """
    bundle_names = []
    with open(path_to_bundle_list, "r") as bundle_list:
        # Iterate over the lines of the file
        for line in bundle_list:
            # Remove the newline character at the end of the line
            bundle_name = line.strip()

            # Append the line to the list
            bundle_names.append(bundle_name)
    return bundle_names


# Read bundle names
bundle_names = read_bundle_txt("../../data/bundle_names.txt")

# Read all intra and inter subject dice scores from the CSVs and write to one large dataframe
sep = "_"
intra_dice_list, inter_dice_list = [], []
for bundle_name in bundle_names:
    bundle_name_short = bundle_name.split(sep=sep, maxsplit=1)[1]
    bundle_file = f"/Users/amelie/Datasets/clinical_dmri_benchmark/dice_scores/{RECONSTRUCTION}/" + \
        bundle_name.replace("_", "").replace("-", "") + ".csv"

    # Load CSV as numpy array for efficiency
    bundle_array = pd.read_csv(bundle_file, index_col=0, na_values=[""]).values

    # Process intra-dices
    intra_dices = np.diag(bundle_array, k=1)[::2]
    intra_dice_list.extend(zip(intra_dices, [
                           bundle_name_short] * len(intra_dices), ["within subject"] * len(intra_dices)))

    # Process inter-dices
    inter_dices_1 = np.diag(bundle_array, k=1)[1::2]
    inter_dices_2 = bundle_array[np.triu_indices_from(bundle_array, k=2)]
    inter_dice_list.extend(zip(np.hstack((inter_dices_1, inter_dices_2)), [bundle_name_short] * (len(
        inter_dices_1) + len(inter_dices_2)), ["between subjects"] * (len(inter_dices_1) + len(inter_dices_2))))

dice_list = intra_dice_list + inter_dice_list
# Convert to DataFrame after processing all bundles
dice_df = pd.DataFrame(dice_list, columns=[
                       "dice score", "bundle", "inter vs. intra"])

# Plot
# Set font, figure size and colors
mpl.rcParams["font.family"] = "Arial"
color_dict = {
    "GQI": [(0, 84/255, 159/255), (142/255, 186/255, 229/255)],
    "CSD": [(189/255, 205/255, 0), (184/255, 214/255, 152/255)],
    "SS3T": [(161/255, 16/255, 53/255), (205/255, 139/255, 135/255)]
}
custom_palette = sns.color_palette(color_dict[RECONSTRUCTION])
sns.set_palette(custom_palette)
plt.rcParams["figure.figsize"] = [15, 8]

bp = sns.boxplot(data=dice_df, x="bundle", y="dice score", hue="inter vs. intra", flierprops={
                 "marker": "D", "markersize": 0.1}, boxprops={"edgecolor": "none"})
bp.tick_params(axis="x", labelrotation=90)
plt.legend(loc="lower left")
plt.tight_layout()
for spine in plt.gca().spines.values():
    spine.set_visible(False)
plt.gca().spines["left"].set_visible(True)
plt.ylim(0, 1)
# saving as svg is not possible due to large file size
# Save png in repro and larger PDF externally
plt.savefig(f"/Users/amelie/Datasets/clinical_dmri_benchmark/dice_scores/dice_scores_{RECONSTRUCTION}.pdf",
            bbox_inches="tight")
plt.savefig(
    f"../../figures/dice_scores_{RECONSTRUCTION}.png", bbox_inches="tight", dpi=300)
plt.show()
