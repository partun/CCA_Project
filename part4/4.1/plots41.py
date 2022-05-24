from cProfile import label, run
from itertools import product
import pandas as pd
import matplotlib.pyplot as plt
from psutil import cpu_percent, cpu_stats


def plot41a(run_cnt=3):
    # Setup figure
    fig = plt.figure(figsize=(10, 5))
    fig_ax = fig.gca()

    for color, (t, c) in zip(
            ('tab:blue', 'tab:orange', 'tab:green', 'tab:red'), product((1, 2), (1, 2))):
        qps = []
        for i in range(run_cnt):
            with open(f'c{c}_t{t}/memcached{i+1}_c{c}_t{t}', 'r') as input_file:
                qps.append(pd.read_csv(
                    input_file, delim_whitespace=True, header=1))

        qps_traces = pd.DataFrame(
            {f'run{i}': qps[i]['QPS'] for i in range(run_cnt)})

        p95_traces = pd.DataFrame(
            {f'run{i}': qps[i]['p95'] / 1000 for i in range(run_cnt)})

        # print(qps_traces)

        fig_ax.errorbar(
            x=qps_traces.mean(axis=1),
            y=p95_traces.mean(axis=1),
            xerr=qps_traces.std(axis=1),
            yerr=p95_traces.std(axis=1),
            label=f'T={t}, C={c}',
            # marker='o' if c == 1 else 'x',
            # linestyle='-' if t == 1 else '--',
            color=color,
            markersize=8,
            markerfacecolor="none",
            capsize=4
        )

    fig_ax.plot(
        [0, 125000],
        [1.5, 1.5],
        linestyle=':',
        label='SLO',
        color='tab:grey'
    )

    fig_ax.set_xlabel("QPS", fontsize=16)
    fig_ax.set_ylabel("95th %-tile response time (ms)", fontsize=16)
    fig_ax.legend(loc='upper left', fontsize=14)
    fig_ax.grid(True, color='lightgray', linestyle='--', linewidth=1)
    fig_ax.tick_params(labelsize=12)
    fig_ax.set_xlim(left=0, right=125000)
    fig_ax.set_ylim(bottom=0, top=1.75)
    # fig_ax.set_yticks(range(0, 11, 1))

    fig_ax.set_xticks(range(0, 120001, 20000),
                      labels=(f'{i}k' for i in range(0, 121, 20)))
    fig_ax.set_xticks(range(0, 120001, 5000), minor=True)

    # Save plot
    plt.tight_layout()
    plt.savefig("plot41a.pdf")


def plot41d(run_cnt=3):
    for color, (t, c) in zip(
            ('tab:blue', 'tab:orange', 'tab:green', 'tab:red'), product((1, 2), (1, 2))):
        # Setup figure
        fig = plt.figure(figsize=(10, 5))
        fig_ax = fig.gca()
        fig_ax2 = fig_ax.twinx()

        start_times = []
        cpu_usage = []
        qps = []
        for i in range(run_cnt):
            with open(f'c{c}_t{t}/memcached{i+1}_c{c}_t{t}', 'r') as input_file:
                df = pd.read_csv(input_file, delim_whitespace=True, header=1)

                start_times.append(df['ts_start'][0] / 1000)
                df['ts_start'] = df['ts_start'].map(
                    lambda x: x / 1000 - start_times[i])
                df['ts_end'] = df['ts_end'].map(
                    lambda x: x / 1000 - start_times[i])
                qps.append(df)

            with open(f'c{c}_t{t}/cpu{i+1}_c{c}_t{t}', 'r') as cpu_usage_file:
                df = pd.read_csv(cpu_usage_file, header=None)
                if c == 1:
                    cpu_usage.append(pd.DataFrame(
                        {'cpu': df[0], 'timestamp': df[4].map(lambda x: x - start_times[i])}))
                else:
                    cpu_usage.append(pd.DataFrame(
                        {'cpu': df[0] + df[1], 'timestamp': df[4].map(lambda x: x - start_times[i])}))

        mem_qps = pd.DataFrame(
            {f'run{i}': qps[i]['QPS'] for i in range(run_cnt)})
        mem_start = pd.DataFrame(
            {f'run{i}': qps[i]['ts_start'] for i in range(run_cnt)})
        mem_end = pd.DataFrame(
            {f'run{i}': qps[i]['ts_end'] for i in range(run_cnt)})

        mem_p95 = pd.DataFrame(
            {f'run{i}': qps[i]['p95'] / 1000 for i in range(run_cnt)})

        fig_ax.errorbar(
            x=mem_qps.mean(axis=1),
            y=mem_p95.mean(axis=1),
            xerr=mem_qps.std(axis=1),
            yerr=mem_p95.std(axis=1),
            label=f'P95 T={t}, C={c}',
            # marker='o',
            linestyle='-',
            color=color,
            markersize=8,
            markerfacecolor="none",
            capsize=4
        )

        cpu_x = []
        cpu_y = []
        cpu_max = []
        for start, end, real_qps in zip(
            mem_start.mean(axis=1),
            mem_end.mean(axis=1),
            mem_qps.mean(axis=1)
        ):
            usage_sum = 0
            usage_max = 0
            cnt = 0
            for i in range(run_cnt):
                for i, measurement in cpu_usage[i].iterrows():
                    if start <= measurement['timestamp'] <= end:
                        usage_max = max(usage_max, measurement['cpu'])
                        usage_sum += measurement['cpu']
                        cnt += 1

            cpu_x.append(real_qps)
            cpu_y.append(usage_sum / cnt)
            cpu_max.append(usage_max)

        fig_ax2.errorbar(
            x=cpu_x,
            y=cpu_max,
            # xerr=cpu_x.std(axis=1),
            # yerr=cpu_y.std(axis=1),
            label=f'CPU T={t}, C={c}',
            marker='x',
            linestyle='--',
            color=color,
            markersize=6,
            markerfacecolor="none",
            capsize=4
        )

        fig_ax.plot(
            [0, 125000],
            [1.5, 1.5],
            linestyle=':',
            label='SLO',
            color='tab:grey'
        )

        fig_ax.set_xlabel("QPS", fontsize=16)
        fig_ax.set_ylabel("95th %-tile response time (ms)", fontsize=16)
        # fig_ax.legend(loc='upper left', fontsize=12)
        fig_ax.grid(True, color='lightgray', linestyle='--', linewidth=1)
        fig_ax.tick_params(labelsize=12)

        fig_ax.set_xlim(left=0, right=125000)
        fig_ax.set_ylim(bottom=0, top=1.65)

        fig_ax.set_xticks(range(0, 120001, 20000),
                          labels=(f'{i}k' for i in range(0, 121, 20)))
        fig_ax.set_xticks(range(0, 120001, 5000), minor=True)
        # fig_ax.set_yticks(range(0, 11, 1))
        # fig_ax.set_xticks(range(0, 80001, 10000), labelrotation=45)
        # fig_ax.set_xticks(range(0, 80001, 5000), minor=True)

        fig.legend(
            loc='lower right', fontsize=12, bbox_to_anchor=(0.92, 0.14))
        fig_ax2.set_ylabel("CPU usage (%)", fontsize=16)

        if c == 2:
            fig_ax2.set_ylim(bottom=0, top=206.25)
            fig_ax2.set_yticks(range(0, 201, 25))
            # fig_ax2.set_yticks(range(0, 201, 20))

        else:
            fig_ax2.set_ylim(bottom=0, top=103.125)
            fig_ax2.set_yticks(range(0, 101, 25))
            # fig_ax2.set_yticks(range(0, 101, 10))

        # Save plot
        plt.tight_layout()
        plt.savefig(f"plot41d_{t}t{c}c.pdf")


if __name__ == '__main__':
    plot41a()
    plot41d()
