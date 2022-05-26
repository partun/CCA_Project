import json
from pprint import pprint
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, time
import matplotlib.pyplot as plt
import re


def calc_stats(folder_path: str, schedule: int, run_cnt: int, mcperf_interval: float, exercise: str, type_A=True):
    """
    calc mean and sdt over the 3 runs
    """

    summaries = []
    for run in range(1, run_cnt + 1):
        with open(f'{folder_path}/summary_{schedule}_{run}.json', 'r') as summary_file:
            summaries.append(json.load(summary_file))

    results = dict()
    for key in summaries[0]:

        durations = [summaries[i][key]['duration'] for i in range(run_cnt)]
        results[key] = {
            'mean_duration': f'{np.mean(durations):.2f}',
            'sdt': f'{np.std(durations):.2f}'
        }

    pprint(results)


def plots43(folder_path: str, schedule: int, run_cnt: int, mcperf_interval: float, exercise: str, type_A=True):

    for run in range(1, run_cnt + 1):
        with open(f'{folder_path}/summary_{schedule}_{run}.json', 'r') as summary_file:
            summary = json.load(summary_file)

        start_time = summary['total']['start']
        end_time = summary['total']['end']
        total_duration = summary['total']['duration']

        with open(f'{folder_path}/mcperf_{schedule}_{run}', 'r') as mcperf_file:
            qps = pd.read_csv(mcperf_file, delim_whitespace=True,
                              skiprows=7, skipfooter=11)

        mode_switching_time = [-100]
        mode_switching_value = [1]
        with open(f'{folder_path}/controller_{schedule}_{run}', 'r') as controller_file:
            for line in controller_file.readlines():
                match_low_qps = re.search(r'(\d+.\d+): low qps mode', line)
                if match_low_qps:
                    mode_switching_time.append(
                        float(match_low_qps.group(1)) - start_time)
                    mode_switching_value.append(1)
                    continue

                match_low_qps = re.search(r'(\d+.\d+): high qps mode', line)
                if match_low_qps:
                    mode_switching_time.append(
                        float(match_low_qps.group(1)) - start_time)
                    mode_switching_value.append(2)
        mode_switching_time.append(1500)
        mode_switching_value.append(1)

        with open(f'{folder_path}/mcperf_{schedule}_{run}', 'r') as mcperf_file:
            for line in mcperf_file.readlines():
                match_start = re.search(r'Timestamp start: (\d+)', line)
                if match_start:
                    mcperf_start_time = int(match_start.group(1)) / 1000
                    break

        print(mcperf_start_time - start_time)
        qps['timestamp'] = pd.Series(
            [mcperf_start_time - start_time +
                (i) * mcperf_interval for i in range(len(qps['QPS']))]
        )

        # remove data after the last parsec job has finished
        needed_data = len(qps['timestamp'][qps['timestamp'] <= total_duration])
        print(qps['timestamp'][needed_data])
        qps = qps.head(needed_data)

        violation_ration = len(
            qps['p95'][qps['p95'] > 1500]) / len(qps['p95']) * 100
        print(
            f'SLO violation ration s{schedule}r{run_cnt} {violation_ration:.3f}%')

        # Setup figure
        fig = plt.figure(figsize=(10, 5))
        fig_ax2 = fig.gca()
        fig_ax = fig_ax2.twinx()
        fig_ax.yaxis.tick_left()
        fig_ax.yaxis.set_label_position("left")
        # fig_ax = fig_ax2.secondary_yaxis('left')
        fig_ax2.yaxis.set_label_position("right")
        fig_ax2.yaxis.tick_right()

        colors = ('blue', 'orange', 'green', 'red', 'purple', 'pink')
        workloads = (
            'parsec_dedup', 'parsec_fft', 'parsec_freqmine', 'parsec_blackscholes',
            'parsec_cannel', 'parsec_ferret'
        )
        for workload, color in zip(workloads, colors):

            # fig_ax.plot(
            #     [workload['start'], workload['start']],
            #     [0, 1000],
            #     label=workload['workload'],
            #     markersize=8,
            #     markerfacecolor="none",
            # )

            fig_ax2.broken_barh(
                [(summary[workload]['start'] - start_time,
                  summary[workload]['duration'])],
                (-5, 5),
                label=workload.replace('parsec_', ''),
                facecolors=color,
                url='adf',
                zorder=9,
            )
            fig_ax2.text(
                summary[workload]['start'] - start_time,
                -2.5,
                f" {summary[workload]['start'] -start_time:.0f}s",
                va='center',
                fontsize=10,
                zorder=10
            )
            pass

        # plot qps
        fig_ax2.bar(
            qps['timestamp'],
            qps['QPS'] / 1000,
            width=mcperf_interval,
            label='QPS',
            # marker="o",
            # markersize=8,
            # markerfacecolor="none",
            color='lightsteelblue',
            zorder=2,
            align='edge'
        )
        # fig_ax2.plot(
        #     qps['timestamp'],
        #     qps['QPS'] / 1000,
        #     # width=10,
        #     label='QPS',
        #     marker="o",
        #     markersize=4,
        #     markerfacecolor="none",
        #     color='grey',
        #     # color='lightsteelblue',
        #     zorder=2,
        #     # align='edge'
        # )

        if type_A:
            # plot p95 latency
            fig_ax.plot(
                [t + mcperf_interval / 2 for t in qps['timestamp']],
                qps['p95'] / 1000,
                label='p95 latency',
                marker="x",
                markersize=4,
                markerfacecolor="none",
                color='tab:blue',
                zorder=3
            )

            fig_ax.plot(
                [0, 1800],
                [1.5, 1.5],
                linestyle=':',
                label='SLO',
                color='tab:grey'
            )

        else:
            fig_ax.plot(
                mode_switching_time,
                mode_switching_value,
                label='memcached\ncores',
                # marker="o",
                drawstyle='steps-post',
                markersize=4,
                lw=0.8,
                markerfacecolor="none",
                color='tab:blue',
                zorder=3
            )

    # workloads = sorted(workload_times.iterrows(),
    #                    key=lambda x: x[1]['end'], reverse=True)

    # labels = (w['workload'] for i, w in workloads)
    # xrow = sorted(
    #     (x for x in chain(workload_times['start'], workload_times['end'])))
    # y = [
    #     [
    #         100 if workload_times['start'][i] <= x <= workload_times['end'][i] else 0
    #         for x in xrow
    #     ]
    #     for i, workload in workloads
    # ]

    # fig_ax.stackplot(xrow, y, labels=labels)

    # # Style figure
    # fig_ax.set_title(
    #     "Response time of System A.\nError bars: $1s$. (10 rep. per point)",
    #     fontsize=16,
    #     fontweight="bold",
    #     pad=10
    # )

        fig_ax.set_title(
            f"{exercise}) {run}{'A' if type_A else 'B'}",
            fontsize=14,
            fontweight="bold",
            pad=10
        )
        # fig.legend(loc='lower right', fontsize=10)
        fig.legend(
            loc='lower right', fontsize=9.5, bbox_to_anchor=(0.92, 0.12))
        fig_ax.grid(True, color='lightgray', linestyle='--', linewidth=1)
        # fig_ax.tick_params(labelsize=12)
        fig_ax2.set_xlim(left=0, right=1800)
        # fig_ax2.set_xticks(range(0, 1801, 300), labels=[f'{i/60:.0f}min' for i in range(0, 1801, 300)])
        # fig_ax2.set_xlabel("Time", fontsize=14)
        fig_ax2.set_xlabel("Time (s)", fontsize=14)
        fig_ax2.set_ylabel("QPS", fontsize=14)

        if type_A:
            fig_ax.set_ylabel("95th %-tile response time (ms)", fontsize=14)

            fig_ax.set_ylim(bottom=0.12, top=1.8)
            fig_ax.set_yticks([i / 5 + 0.2 for i in range(9)])
        else:
            fig_ax.set_ylim(bottom=0.4, top=2.5)
            # fig_ax.set_ylim(bottom=-1.4, top=2)
            fig_ax.set_yticks([0.5, 1, 1.5, 2, 2.5], labels=[
                              '', '1 core', '', '2 cores', ''])

        fig_ax2.set_ylim(bottom=-5, top=100)
        fig_ax2.set_yticks(range(0, 105, 25), labels=(
            f'{i}k' for i in range(0, 105, 25)))

        # fig_ax.set_yticks(range(0, 11, 1))
        # fig_ax.set_xticks(range(0, 80001, 5000), minor=True)

        # Save plot
        plt.tight_layout()
        plt.savefig(f"{folder_path}/plot4_{run:d}{'A' if type_A else 'B'}.pdf")


if __name__ == '__main__':
    # calc_stats('.', 6, 3, 10, '4.3', True)

    plots43('.', 6, 3, 10, '4.3', True)
    plots43('.', 6, 3, 10, '4.3', False)

    plots43('../4.4/5s_interval', 6, 3, 5, '4.4', True)
    plots43('../4.4/5s_interval', 6, 3, 5, '4.4', False)

    plots43('../4.4/3s_interval', 6, 3, 3, '4.4', True)
    plots43('../4.4/3s_interval', 6, 3, 3, '4.4', False)

    plots43('../4.4/2s_interval', 6, 1, 2, '4.4', True)
