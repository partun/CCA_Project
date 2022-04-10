import json
import numpy as np
import matplotlib.pyplot as plt


def part2b():
    with open('measurements_part2b/realtime_results_part2b.json', 'r') as f:
        measurements = json.load(f)

    table = dict()
    for key, value in measurements.items():
        parsec, workload, threads, = key.split('_')
        table.setdefault(workload, dict())[int(threads)] = value

    for workload in table:
        normalized = table[workload][1]


        # for n in table[workload]:
        #     table[workload][n] = table[workload][n] / normalized * n

        for n in table[workload]:
            table[workload][n] = normalized / table[workload][n]

        # thread_count = list(sorted(table[workload].keys(), reverse=True))
        # print(list(zip(thread_count, thread_count[1:])))
        # for c, p in zip(thread_count, thread_count[1:]):
        #     table[workload][c] = (table[workload][c] - table[workload][p]) / (c - p)



    print(table)

    with open('measurements_part2b/relative_results_part2b.json', 'w') as f:
        json.dump(table, f, indent=4)
    return table


def plot(measurements):
    measurements.pop('fft')
    print(measurements)

    # Setup figure
    fig = plt.figure(figsize=(10,5))
    fig_ax = fig.gca()

    # linear scaling
    fig_ax.errorbar(
        x=range(1, 13),
        y=range(1, 13),
        label='linear speedup',
        linestyle='--',
        markersize=8,
        markerfacecolor="grey",
        color='grey',
        capsize=4
    )

    # 50% scaling
    fig_ax.errorbar(
        x=range(1, 13),
        y=[0.5 * i + 0.5 for i in range(1, 13)],
        label='significant speedup',
        linestyle=':',
        markersize=8,
        markerfacecolor="grey",
        color='black',
        capsize=4
    )


    # Plot line
    for workload in measurements:
        x = list(sorted(measurements[workload].keys()))
        y = [measurements[workload][i] for i in x]
        fig_ax.errorbar(
            x=x,
            y=y,
            label=workload,
            marker="o",
            markersize=8,
            markerfacecolor="none",
            capsize=4
        )

    # # Style figure
    fig_ax.set_title(
        "Normalized Speedup of Batch Workloads",
        fontsize=16,
        fontweight="bold",
        pad=10
    )
    fig_ax.set_xlabel("number of threads", fontsize=16)
    fig_ax.set_ylabel("normalized speedup", fontsize=16)
    fig_ax.legend(loc='upper left', fontsize=14)
    fig_ax.grid(True, color='lightgray', linestyle='--', linewidth=1)
    fig_ax.tick_params(labelsize=12)
    fig_ax.set_xlim(left=1, right=13)
    fig_ax.set_ylim(bottom=1, top=12)
    fig_ax.set_yticks(range(1, 13, 1))
    fig_ax.set_xticks([1, 3, 6, 12], labelrotation=45)
    fig_ax.set_xticks(range(1, 13, 1), minor=True)

    # Save plot
    plt.tight_layout()
    plt.savefig("measurements_part2b/plot2b.pdf")


if __name__ == '__main__':
    measurements = part2b()
    plot(measurements)
