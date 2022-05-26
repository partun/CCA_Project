from itertools import chain
import pandas as pd
from datetime import datetime, timedelta, time
import matplotlib.pyplot as plt


def create_all_plots_for_3a():
    for i in range(3):
        plot3a(i + 1)


def plot3a(run_index: int):

    with open(f'schedules/memcached_log_03_run{run_index:d}.csv') as log_file:
        memcached_qos = pd.read_csv(log_file, delim_whitespace=True, header=1)

    interval = timedelta(seconds=20)
    with open(f'schedules/memcached_log_03_run{run_index:d}.csv') as log_file:
        for line in log_file.readlines():
            start_time = datetime.strptime(
                line[:-1], r"%a %b  %d %H:%M:%S %Z %Y") + interval
            break

    memcached_qos['timestamp'] = pd.Series((
        i * 20 for i in range(memcached_qos.shape[0])
    ))

    def convert_to_relative_time(time_str):
        return (
            datetime.strptime(time_str, r"%H:%M:%S").replace(
                year=start_time.year, month=start_time.month, day=start_time.day
            )
            - start_time
        ).total_seconds()

    with open(f'schedules/times_{run_index:d}.csv') as times_file:
        workload_times = pd.read_csv(times_file, sep=';')
        workload_times['start'] = workload_times['start'].map(
            convert_to_relative_time)
        workload_times['end'] = workload_times['end'].map(
            convert_to_relative_time)

    print(workload_times)

    # Setup figure
    fig = plt.figure(figsize=(10, 5))
    fig_ax = fig.gca()

    colors = ('blue', 'orange', 'green', 'red', 'purple', 'pink')
    workloads = reversed((2, 4, 1, 3, 5, 0))
    for j, i in enumerate(workloads):
        # fig_ax.plot(
        #     [workload['start'], workload['start']],
        #     [0, 1000],
        #     label=workload['workload'],
        #     markersize=8,
        #     markerfacecolor="none",
        # )

        print(workload_times['workload'][i])

        fig_ax.broken_barh(
            [(workload_times['start'][i],
              workload_times['duration_seconds'][i])],
            (0.1 * j, 0.1),
            label=workload_times['workload'][i],
            facecolors=colors[j],
            url='adf'
        )
        fig_ax.text(
            workload_times['start'][i],
            0.1 * j + 0.05,
            f"  {workload_times['workload'][i]}: {workload_times['start'][i]:.0f}s",
            va='center',
            zorder=1
        )
        pass

    # Plot line
    fig_ax.plot(
        memcached_qos['timestamp'],
        memcached_qos['p95'] / 1000,
        label='p95',
        marker="o",
        markersize=8,
        markerfacecolor="none",
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
    fig_ax.set_xlabel("Time (s)", fontsize=14)
    fig_ax.set_ylabel("95th %-tile response time (ms)", fontsize=14)
    fig_ax.legend(loc='lower right', fontsize=10)
    fig_ax.grid(True, color='lightgray', linestyle='--', linewidth=1)
    # fig_ax.tick_params(labelsize=12)
    fig_ax.set_xlim(left=0, right=300)
    fig_ax.set_ylim(bottom=0, top=0.6)
    # fig_ax.set_yticks(range(0, 11, 1))
    # fig_ax.set_xticks(range(0, 80001, 10000), labelrotation=45)
    # fig_ax.set_xticks(range(0, 80001, 5000), minor=True)

    # Save plot
    plt.tight_layout()
    plt.savefig(f"plot3a_run{run_index:d}.pdf")


if __name__ == '__main__':
    create_all_plots_for_3a()
