import os
import pandas as pd
import numpy as np
import argparse
from scipy.stats import ttest_rel
from scipy.stats import linregress
from statsmodels.sandbox.stats.multicomp import multipletests
import seaborn as sns

import matplotlib.pyplot as plt
# Example command:
#python analysis_plot_subject_level.py -metrics ~/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/preprocessing_ALL/results/n36/subject_metrics_cope.txt -path-out ~/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/preprocessing_ALL/results/n36/cope -metrics-roi ~/nilab/Dermatomal_Mapping_R01/Aim2/data/BIDS/derivatives/preprocessing_ALL/results/n36/subject_metrics_rois_cope.txt

def get_parser():
    parser = argparse.ArgumentParser(description='Create subject level plots for analysis.')
    parser.add_argument('-metrics', type=str, required=True, help='Path to the metrics file')
    parser.add_argument('-metrics-roi', type=str, required=True, help='Path to the metrics file')
    parser.add_argument('-path-out', type=str, required=True, help='Path to the output directory')
    return parser

def main():
    args = get_parser().parse_args()
    metrics_path = args.metrics
    path_out = args.path_out
    if not os.path.exists(path_out):
        os.makedirs(path_out)
    metrics_roi_path = args.metrics_roi
    # Load the metrics dataset
    dataset = pd.read_csv(metrics_path, delimiter=" ")
    dataset_roi = pd.read_csv(metrics_roi_path, delimiter=" ")
    runs= ['rightthumb', 'rightmiddle', 'rightpinky', 'leftthumb', 'leftmiddle', 'leftpinky']

    #Create subject level plots for each finger 
    dataset = dataset[(dataset.run == 'rightthumb') | (dataset.run == 'leftthumb') | (dataset.run == 'rightmiddle') | (dataset.run == 'leftmiddle') | (dataset.run == 'rightpinky') | (dataset.run == 'leftpinky')]
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
                if len(data) != 6:    
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
            
            means = [cope1_mean, cope2_mean, cope3_mean, cope4_mean, cope5_mean, cope6_mean]

            ses = [cope1_se, cope2_se, cope3_se, cope4_se, cope5_se, cope6_se]

            for x, mean, se in zip(xlabel, means, ses):
                plt.text(
                    x,
                    mean + se,
                    f'{mean:.2f}±{se:.2f}',
                    ha='center',
                    va='bottom',
                    fontsize=8,
                    rotation=45
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

    run_order = [
        'rightthumb',
        'leftthumb',
        'rightmiddle',
        'leftmiddle',
        'rightpinky',
        'leftpinky'
    ]

    for measure in ['zscore_sc', 'voxels_sc']:

        for region in regions_rois:

            fig, ax = plt.subplots(figsize=(6,4))

            for subject in dataset_roi.subject.unique():

                data = dataset_roi[
                    (dataset_roi.subject == subject) &
                    (dataset_roi.region == region)
                ]

                data = data.set_index('run').loc[run_order].reset_index()

                ydata = data[measure].values

                ax.plot(
                    run_order,
                    ydata,
                    color='gold',
                )
            #ylim = [2,6]
            #ylim = [-150, 200]
            #ax.set_ylim(ylim)

            means = []
            sds = []

            for run in run_order:

                vals = dataset_roi[
                    (dataset_roi.run == run) &
                    (dataset_roi.region == region)
                ][measure]

                means.append(vals.mean())
                sds.append(vals.std())
            print(f"Means for {measure} in {region}: {means}")
            print(f"Standard deviations for {measure} in {region}: {sds}")
            ax.errorbar(
                run_order,
                means,
                yerr=sds,
                color='black',
                linewidth=3,
                capsize=5
            )

            plt.xticks(rotation=45)
            plt.ylabel(measure)
            plt.xlabel('Run')
            plt.title(f'{region}')
            plt.tight_layout()
            plt.savefig(os.path.join(path_out, f'{measure}_{region}_subject.png'), dpi=600, bbox_inches='tight', pad_inches = 0, transparent = True)
            plt.close()



    measure = 'zscore_sc'

    runs = [
        'rightthumb',
        'leftthumb',
        'rightmiddle',
        'leftmiddle',
        'rightpinky',
        'leftpinky'
    ]

    segments = ['ALL', 'C6', 'C7', 'C8']

    heat_values = []
    annotations = []

    for run in runs:

        row_values = []
        row_annots = []

        # Whole-cord GM
        left_val = dataset_roi[
            (dataset_roi.run == run)
            & (dataset_roi.region == 'left_sc_gm_mask')
        ][measure].mean()

        right_val = dataset_roi[
            (dataset_roi.run == run)
            & (dataset_roi.region == 'right_sc_gm_mask')
        ][measure].mean()

        if run.startswith('right'):
            color_val = right_val
        else:
            color_val = left_val

        row_values.append(color_val)

        row_annots.append(
            f"{left_val:.1f} | {right_val:.1f}"
        )

        # Segmental ROIs
        for seg in ['C6', 'C7', 'C8']:

            left_roi = f'{seg}_left_sc_gm_mask'
            right_roi = f'{seg}_right_sc_gm_mask'

            left_val = dataset_roi[
                (dataset_roi.run == run)
                & (dataset_roi.region == left_roi)
            ][measure].mean()

            right_val = dataset_roi[
                (dataset_roi.run == run)
                & (dataset_roi.region == right_roi)
            ][measure].mean()

            if run.startswith('right'):
                color_val = right_val
            else:
                color_val = left_val

            row_values.append(color_val)


            row_annots.append(
                f"{left_val:.1f} | {right_val:.1f}"
            )

        heat_values.append(row_values)
        annotations.append(row_annots)

    heat_df = pd.DataFrame(
        heat_values,
        index=runs,
        columns=segments
    )

    plt.figure(figsize=(6, 6))

    sns.heatmap(
        heat_df,
        annot=np.array(annotations),
        fmt="",
        cmap="RdBu_r",
        linewidths=0.5,
        cbar_kws={'label': measure}
    )

    plt.xlabel('Region')
    plt.ylabel('Run')
    plt.title('Segmental activation\n(L GM | R GM)')

    plt.tight_layout()
    plt.savefig(os.path.join(path_out, f'{measure}_segmental_heatmap_subject.png'), dpi=600, bbox_inches='tight', pad_inches = 0, transparent = True)
    plt.close()

if __name__ == "__main__":
    main()
