import pandas as pd
import os
from scipy.stats import wilcoxon
from itertools import combinations
from statsmodels.stats.multitest import multipletests

csv_root = "/Users/amelie/Datasets/clinical_dmri_benchmark/bundle_stats"

results = []
for file_name in ["ICC_dti_fa.csv", "ICC_md.csv", "ICC_total_volume_mm3.csv"]:
    icc_df = pd.read_csv(os.path.join(csv_root, file_name))
    methods = ['ICC_CSD', 'ICC_GQI', 'ICC_SS3T']
    for method1, method2 in combinations(methods, 2):
        # Paired t-test
        stat, p = wilcoxon(icc_df[method1], icc_df[method2])

        results.append({
            'Feature': file_name[4:-4],
            'Comparison': f'{method1} vs {method2}',
            'T-statistic': stat,
            'Raw p-value': p
        })


# Create DataFrame of all results
results_df = pd.DataFrame(results)

# Multiple comparison correction (Bonferroni)
_, corrected_p, _, _ = multipletests(results_df['Raw p-value'], method='fdr_bh')
results_df['Corrected p-value (FDR Benjamini-Hochberg)'] = corrected_p

# Display the result
print(results_df)