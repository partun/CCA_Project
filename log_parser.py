import os
import re
import json

# DIRECTORY_PATH = 'part2a/measurements_part2a'
# RESULTS_FILE_NAME = 'realtime_results_part2a'
DIRECTORY_PATH = 'part2b/measurements_part2b'
RESULTS_FILE_NAME = 'realtime_results_part2b'


def main() -> None:

    results = dict()

    for file_name in os.listdir(DIRECTORY_PATH):
        file_path = f'{DIRECTORY_PATH}/{file_name}'
        print(file_path)
        if not file_path.endswith('.txt'):
            continue

        file_name = file_name.split('.')[0]

        with open(file_path, 'r') as file:

            for line in file.readlines():
                m = re.search(r'real\s*(\d+)m(\d+.\d*)s', line)
                if m:
                    minutes = m.group(1)
                    seconds = m.group(2)
                    print(f'{minutes}m{seconds}s')

                    results[file_name] = 60 * int(minutes) + float(seconds)

    with open(f'{DIRECTORY_PATH}/{RESULTS_FILE_NAME}.json', 'w') as result_file:
        json.dump(results, result_file, indent=4)


if __name__ == '__main__':
    main()