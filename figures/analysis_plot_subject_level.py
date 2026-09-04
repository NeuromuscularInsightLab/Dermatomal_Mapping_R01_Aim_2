import os
import pandas as pd
import numpy as np
import argparse
from scipy.stats import ttest_rel
from scipy.stats import linregress
from statsmodels.sandbox.stats.multicomp import multipletests

import matplotlib.pyplot as plt
# Example command:
#python analysis_plot_subject_level.py -metrics ~/Projects/Dermatomal_Mapping_R01/manuscripts/results_n40_spinalcord_Sandrine/subject_metrics.txt -path-out ~/Projects/Dermatomal_Mapping_R01/manuscripts/plots_run-average -metrics-roi ~/Projects/Dermatomal_Mapping_R01/manuscripts/results_n40_spinalcord_Sandrine/subject_metrics_rois.txt

def get_parser():
    parser = argparse.ArgumentParser(description='Create subject level plots for analysis.')
    parser.add_argument('-metrics', type=str, required=True, help='Path to the metrics file')
    #parser.add_argument('-metrics-roi', type=str, required=True, help='Path to the metrics file')
    parser.add_argument('-path-out', type=str, required=True, help='Path to the output directory')
    return parser

def main():
    args = get_parser().parse_args()
    metrics_path = args.metrics
    path_out = args.path_out
    if not os.path.exists(path_out):
        os.makedirs(path_out)
    #metrics_roi_path = args.metrics_roi
    # Load the metrics dataset
    dataset = pd.read_csv(metrics_path, delimiter=" ")
    #dataset_roi = pd.read_csv(metrics_roi_path, delimiter=" ")
    runs= ['rightthumb', 'rightmiddle', 'rightpinky', 'leftthumb', 'leftmiddle', 'leftpinky']

    #Create subject level plots for each finger 
    dataset = dataset[(dataset.run == 'rightthumb') | (dataset.run == 'leftthumb') | (dataset.run == 'rightmiddle') | (dataset.run == 'leftmiddle') | (dataset.run == 'rightpinky') | (dataset.run == 'leftpinky')]
    print(dataset)
    measures = ['zscore', 'voxels', 'lr']
    regions = ['sc']
    regions_rois = [
        'left_sc_gm_mask', 'right_sc_gm_mask', "left_sc_mask", 'right_sc_mask',
        'C6_left_sc_gm_mask', 'C6_right_sc_gm_mask', 'C7_left_sc_gm_mask', 'C7_right_sc_gm_mask',
        'C8_left_sc_gm_mask', 'C8_right_sc_gm_mask'
    ]

    for measure in measures:
        for region in regions:
            fig, ax = plt.subplots(figsize=(6,3))
            width=0.50
            color=(255/255, 208/255, 0/255) #yellow

            xlabel = runs

            if (measure == 'zscore') & (region == 'sc'):
                ylabel = 'Z Score'
                ylim = [2.2, 4.0]
                ytickmarks = [2.2, 2.5, 3, 3.5, 4]
            elif (measure == 'voxels') & (region == 'sc'):
                ylabel = 'Voxels'
                ylim = [5000,25000]
                ytickmarks = [5000, 10000, 15000, 20000, 25000]
            elif measure == 'lr':
                ylabel = 'LR Index'
                ylim = [-0.3, 0.3]
                ytickmarks = [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3]
            else:
                measure='Error'

            for subject in dataset.subject.unique():
                print(subject)
                data = dataset[(dataset['subject'] == subject)]
                data = data[measure + '_' + region].values
                print(data, xlabel)
                plt.plot(xlabel, data, width, label=xlabel, color=color, marker=None)

            cope1_mean = dataset[(dataset['run'] == 'rightthumb')][measure + '_' + region].mean()
            cope2_mean = dataset[(dataset['run'] == 'rightmiddle')][measure + '_' + region].mean()
            cope3_mean = dataset[(dataset['run'] == 'rightpinky')][measure + '_' + region].mean()
            cope4_mean = dataset[(dataset['run'] == 'leftthumb')][measure + '_' + region].mean()
            cope5_mean = dataset[(dataset['run'] == 'leftmiddle')][measure + '_' + region].mean()
            cope6_mean = dataset[(dataset['run'] == 'leftpinky')][measure + '_' + region].mean()

            cope1_se = dataset[(dataset['run'] == 'rightthumb')][measure + '_' + region].std()
            cope2_se = dataset[(dataset['run'] == 'rightmiddle')][measure + '_' + region].std()
            cope3_se = dataset[(dataset['run'] == 'rightpinky')][measure + '_' + region].std()
            cope4_se = dataset[(dataset['run'] == 'leftthumb')][measure + '_' + region].std()
            cope5_se = dataset[(dataset['run'] == 'leftmiddle')][measure + '_' + region].std()
            cope6_se = dataset[(dataset['run'] == 'leftpinky')][measure + '_' + region].std()
            plt.errorbar(
                xlabel,
                [cope1_mean, cope2_mean, cope3_mean, cope4_mean, cope5_mean, cope6_mean],
                yerr=[cope1_se, cope2_se, cope3_se, cope4_se, cope5_se, cope6_se],
                label=xlabel,
                color=(0/255, 0/255, 0/255),
                marker=None,
                linewidth=3,
                elinewidth=3,
                capsize=5,
                markeredgewidth=3
            )
            # Fit linear regression (1st degree polynomial) to all data points (not just the means)
            x_all = dataset['run'].map({'rightthumb': 1, 'leftthumb': 4, 'rightmiddle': 2, 'leftmiddle': 5, 'rightpinky': 3, 'leftpinky': 6}).values
            y_all = dataset[measure + '_' + region].values
            slope, intercept, r_value, p_value, std_err = linregress(x_all, y_all)
            fit_line = slope * np.arange(1, 7) + intercept

            ax.text(
                0.05, 0.1,
                f'Linear fit: p={p_value:.3g}',
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment='top',
                color='black'
            )
            ax.set_ylim(ylim)
            ax.set_yticks(ytickmarks)
            ax.set_ylabel(ylabel,fontsize=16, color=(0/255, 0/255, 0/255))
            ax.tick_params(labelsize=8, width=1.5, colors=(0/255, 0/255, 0/255))

            for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_linewidth(1.5)
                ax.spines[axis].set_color((0/255, 0/255, 0/255))
            for axis in ['top','right']:
                ax.spines[axis].set_linewidth(0)

            plt.ticklabel_format(axis='y', style='sci', scilimits=(-3,3))
            ax.tick_params(bottom = False)

            plt.subplots_adjust(wspace = 0.5)
            plt.show()

            fig.savefig(os.path.join(path_out, measure + '_' + region + '_subject.png'),  dpi=600, bbox_inches='tight', pad_inches = 0, transparent = True)

            plt.close()
            # Paired t-tests between all pairs of copes (cope1, cope2, cope3, cope4)

            cope_labels = ['rightthumb', 'leftthumb', 'rightmiddle', 'leftmiddle', 'rightpinky', 'leftpinky']
            n_copes = len(cope_labels)

            for i in range(n_copes):
                for j in range(i + 1, n_copes):
                    cope_i = cope_labels[i]
                    cope_j = cope_labels[j]
                    data_i = dataset[dataset['run'] == cope_i][measure + '_' + region]
                    data_j = dataset[dataset['run'] == cope_j][measure + '_' + region]
                    # Align by subject
                    merged = pd.merge(
                        dataset[dataset['run'] == cope_i][['subject', measure + '_' + region]],
                        dataset[dataset['run'] == cope_j][['subject', measure + '_' + region]],
                        on='subject',
                        suffixes=('_' + cope_i, '_' + cope_j)
                    )
                    if not merged.empty:
                        stat, pval = ttest_rel(merged[measure + '_' + region + '_' + cope_i], merged[measure + '_' + region + '_' + cope_j])
                        result = f"Paired t-test {cope_i} vs {cope_j}: t={stat:.4f}, p={pval:.4g}, n={len(merged)}"
                    else:
                        result = f"No paired data for {cope_i} vs {cope_j}"
                    outname = f"{measure}_{region}_subject_{cope_i}_{cope_j}.txt"
                    with open(os.path.join(path_out, outname), "w") as text_file:
                        print(result, file=text_file)

    # Create subject level plots for each ROI region for 4 amps
    # for measure in ['zscore_sc', 'voxels_sc']:
    #     for region in regions_rois:
    #         fig, ax = plt.subplots(figsize=(4,3))
    #         width = 0.50
    #         color = (255/255, 208/255, 0/255)  # yellow
    #         xlabel = ['Amp1', 'Amp2', 'Amp3', 'Amp4']

    #         # Set y-label and limits based on measure
    #         if measure == 'voxels_sc':
    #             ylabel = 'Voxels'
    #             if region in ['left_sc_gm_mask', 'right_sc_gm_mask', "left_sc_mask", 'right_sc_mask']:
    #                 ylim = [0, 1500]
    #                 ytickmarks = [0, 200, 400, 600, 800, 1000, 1200, 1400]
    #             else:
    #                 ylim = [0, 800]
    #                 ytickmarks = [0, 100, 200, 300, 400, 500, 600, 700, 800]

    #         elif measure == 'zscore_sc':
    #             ylabel = 'Z Score'
    #             ylim = [1, 5]
    #             ytickmarks = [1, 2, 3, 4, 5]
    #         print(dataset_roi.head())
    #         for subject in dataset_roi.subject.unique():
    #             data = dataset_roi[
    #                 (dataset_roi['subject'] == subject) &
    #                 (dataset_roi['cope'].isin(['cope1', 'cope2', 'cope3', 'cope4'])) &
    #                 (dataset_roi['region'] == region)
    #             ]
    #             data = data.sort_values('cope')
    #             print(data)
    #             ydata = data[measure].values
    #             print(ydata)
    #             plt.plot(xlabel, ydata, width, color=color, marker=None)

    #         # Means and SDs for each amp
    #         means = []
    #         sds = []
    #         for cope in ['cope1', 'cope2', 'cope3', 'cope4']:
    #             vals = dataset_roi[(dataset_roi['cope'] == cope) & (dataset_roi['region'] == region)][measure]
    #             means.append(vals.mean())
    #             sds.append(vals.std())
    #         plt.errorbar(xlabel, means, yerr=sds, color=(0,0,0), marker=None, linewidth=3, elinewidth=3, capsize=5, markeredgewidth=3)

    #         # Linear regression
            
    #         x_all = dataset_roi[dataset_roi['region'] == region]['cope'].map({'cope1': 1, 'cope2': 2, 'cope3': 3, 'cope4': 4}).values
    #         y_all = dataset_roi[dataset_roi['region'] == region][measure].values
    #         slope, intercept, r_value, p_value, std_err = linregress(x_all, y_all)
    #         fit_line = slope * np.arange(1, 5) + intercept
    #         if p_value < 0.05:
    #             bold=True
    #         else:
    #             bold=False

    #         if p_value < 0.001:
    #              p_value_text =  'p<0.001'
    #         else:
    #             p_value_text = f'p={p_value:.3f}'
    #         ax.text(
    #             0.05, 0.08,
    #             f'Linear fit: {p_value_text}',
    #             transform=ax.transAxes,
    #             fontsize=10,
    #             verticalalignment='top',
    #             color='black',
    #             fontweight='bold' if bold else 'normal'
    #         )
    #         if ylim is not None:
    #             ax.set_ylim(ylim)
    #         if ytickmarks is not None:
    #             ax.set_yticks(ytickmarks)
    #             ax.set_ylabel(ylabel, fontsize=16, color=(0,0,0))
    #             ax.tick_params(labelsize=12, width=1.5, colors=(0,0,0))
    #         for axis in ['top','bottom','left','right']:
    #             ax.spines[axis].set_linewidth(1.5)
    #             ax.spines[axis].set_color((0,0,0))
    #         for axis in ['top','right']:
    #             ax.spines[axis].set_linewidth(0)
    #         plt.ticklabel_format(axis='y', style='sci', scilimits=(-3,3))
    #         ax.tick_params(bottom=False)
    #         plt.subplots_adjust(wspace=0.5)
    #         plt.show()
    #         fig.savefig(os.path.join(path_out, f"{measure}_{region}_subject.png"), dpi=600, bbox_inches='tight', pad_inches=0, transparent=True)
    #         plt.close()

    #         # Paired t-tests between all pairs of copes for this ROI
    #         cope_labels = ['cope1', 'cope2', 'cope3', 'cope4']
    #         n_copes = len(cope_labels)
    #         pvals = []
    #         pairs = []

    #         for i in range(n_copes):
    #             for j in range(i + 1, n_copes):
    #                 cope_i = cope_labels[i]
    #                 cope_j = cope_labels[j]
    #                 merged = pd.merge(
    #                     dataset_roi[(dataset_roi['cope'] == cope_i) & (dataset_roi['region'] == region)][['subject', measure]],
    #                     dataset_roi[(dataset_roi['cope'] == cope_j) & (dataset_roi['region'] == region)][['subject', measure]],
    #                     on='subject',
    #                     suffixes=('_' + cope_i, '_' + cope_j)
    #                 )
    #                 if not merged.empty:
    #                     stat, pval = ttest_rel(merged[measure + '_' + cope_i], merged[measure + '_' + cope_j])
    #                     result = f"Paired t-test {cope_i} vs {cope_j}: t={stat:.4f}, p={pval:.4g}, n={len(merged)}"
    #                 else:
    #                     result = f"No paired data for {cope_i} vs {cope_j}"
    #                 pvals.append(pval)
    #                 pairs.append((cope_i, cope_j))
    #                 outname = f"{measure}_{region}_subject_{cope_i}_{cope_j}.txt"
    #                 with open(os.path.join(path_out, outname), "w") as text_file:
    #                     print(result, file=text_file)
    #         outname = f'paired_test_Bonferroni_{measure}_{region}.txt'
    #         p_adjusted = multipletests(pvals, method='bonferroni', alpha=0.05)
    #         pvals_corr = f"Adjusted p-values for multiple comparisons (Bonferroni): {p_adjusted} for pairs {pairs}"
    #         with open(os.path.join(path_out, outname), "w") as text_file:
    #                     print(pvals_corr, file=text_file)

if __name__ == "__main__":
    main()
