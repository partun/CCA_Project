import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def main() -> None:
    interference_types = ('without', 'cpu', 'l1d', 'l1i', 'l2', 'llc', 'membw')
    run_cnt = 3

    measurements = {
        interference : {
            i: pd.read_csv(f'part1/measurements_part1/{interference}_{i:d}_client-agent.csv', delimiter=';')
            for i in range(run_cnt)
        }
        for interference in interference_types
    }

    # Setup figure
    fig = plt.figure()
    fig_ax = fig.gca()

    # Plot line
    for interference in interference_types:

        qps = pd.DataFrame({f'run{i}': measurements[interference][i]['QPS'] for i in range(run_cnt)})

        p95 = pd.DataFrame({f'run{i}': measurements[interference][i]['p95'] / 1000 for i in range(run_cnt)})

        fig_ax.errorbar(
            x=qps.mean(axis=1),
            y=p95.mean(axis=1),
            xerr=qps.std(axis=1),
            yerr=p95.std(axis=1),
            label=interference,
            marker="o",
            markersize=8,
            markerfacecolor="none",
            capsize=4
        )

    # # Style figure
    # fig_ax.set_title(
    #     "Response time of System A.\nError bars: $1s$. (10 rep. per point)",
    #     fontsize=16,
    #     fontweight="bold",
    #     pad=10
    # )
    fig_ax.set_xlabel("QPS", fontsize=16)
    fig_ax.set_ylabel("95th %-tile response time (ms)", fontsize=16)
    fig_ax.legend(loc='upper right', fontsize=14)
    fig_ax.grid(True, color='lightgray', linestyle='--', linewidth=1)
    fig_ax.tick_params(labelsize=12)
    fig_ax.set_xlim(left=0, right=80000)
    fig_ax.set_ylim(bottom=0, top=10)
    fig_ax.set_yticks(range(0, 11, 1))
    fig_ax.set_xticks(range(0, 80001, 10000), labelrotation=45)
    fig_ax.set_xticks(range(0, 80001, 5000), minor=True)

    


    # Save plot
    plt.tight_layout()
    plt.savefig("plot1a.pdf")




if __name__ == '__main__':
    main()