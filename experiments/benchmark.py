# -*- coding: utf-8 -*-
from collections import namedtuple
import csv
from datetime import datetime
import sys
import timeit

import rra_star
from simulation import util
import id as odid
import poc
import version1

MAX_TIME = 2
OBSTACLES = 0.2

def odid_entry(world, starts, goals, start_time, max_time):
    return odid.odid2(len(starts), world, starts, goals, start_time,
                      max_time)

def poc_entry(world, starts, goals, start_time, max_time):
    agents = [poc.Agent(world, starts[i], goals[i])
              for i in range(len(starts))]
    return poc.poc(agents, start_time, max_time)

def version1_entry(world, starts, goals, start_time, max_time):
    agents = [version1.Agent(world, starts[i], goals[i])
              for i in range(len(starts))]
    return version1.version1(agents, start_time, max_time, False)

Algorithm = namedtuple('Algorithm', ['name', 'entry'])
ALGORITHMS = [
    Algorithm('OD+ID', odid_entry),
    Algorithm('Naive', poc_entry),
    Algorithm('Base version', version1_entry),
]

def main(runs, max_agents):
    # Generate problems
    problems = []
    while len(problems) < runs:
        for i in range(2, max_agents):
            problems.append(util.generate_problem(i, 16, 16, OBSTACLES))
            if len(problems) == runs:
                break

    instance = 0
    line = []
    f = open(f'results/benchmark-{datetime.now()}.csv', 'w')
    writer = csv.writer(f)
    result = ['instance'] + [algorithm.name for algorithm in ALGORITHMS]
    writer.writerow(result)

    global_start_time = timeit.default_timer()
    for problem in problems:
        result = [instance]
        for algorithm in ALGORITHMS:
            start_time = timeit.default_timer()
            try:
                algorithm.entry(*problem,
                                start_time=start_time,
                                max_time=MAX_TIME)
                end_time = timeit.default_timer()
                result.append(end_time - start_time)
            except odid.TimeExceeded:
                print('Time exceeded')
                result.append('NA')
            except (rra_star.NoValidPathExists, util.NoPathsFoundException):
                print('No valid path exists')
                result.append('NA')
            finally:
                end_time = timeit.default_timer()
                print(algorithm.name, 'time:',
                    f'{(end_time - start_time) * 1000:5.3f}ms')
        writer.writerow(result)
        f.flush()
        instance += 1
    global_end_time = timeit.default_timer()
    print(f'Total time: {(global_end_time - global_start_time) * 1000:5.3f}ms')
    f.close()

if __name__ == '__main__':
    try:
        runs = int(sys.argv[1])
    except IndexError:
        runs = 100
    try:
        max_agents = int(sys.argv[2])
    except IndexError:
        max_agents = 25
    main(runs, max_agents)
