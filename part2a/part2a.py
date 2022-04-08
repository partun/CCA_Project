import json


def part2a() -> None:
    with open('measurements_part2a/realtime_results_part2a.json', 'r') as f:
        measurements = json.load(f)

    table = dict()
    for key, value in measurements.items():
        workload, interference = key.split('_')
        table.setdefault(workload, dict())[interference] = value

    for workload in table:
        normalized = table[workload]['none']
        for interference in table[workload]:
            table[workload][interference] = table[workload][interference] / normalized

    print(table)

    with open('measurements_part2a/relative_results_part2a.json', 'w') as f:
        json.dump(table, f, indent=4)

    interferences = ('cpu', 'l1d', 'l1i', 'l2', 'llc', 'membw')
    for workload in table:
        print(f'{workload}:')
        for interference in interferences:
            value = table[workload][interference]
            if value < 1.3:
                value_str = f'{value:.2f}'
            elif value < 2:
                value_str = '{\color{YellowOrange}' + f'{value:.2f}' + '}'
            else:
                value_str = '{\color{Red}' + f'{value:.2f}' + '}'
            print(value_str, end=' & ')
        print('')




if __name__ == '__main__':
    part2a()