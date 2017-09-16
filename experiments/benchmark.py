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
import version1b
import standard_algorithm
import window

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

def version1b_entry(world, starts, goals, start_time, max_time):
    agents = [version1b.Agent(world, starts[i], goals[i])
              for i in range(len(starts))]
    return version1b.version1(agents, start_time, max_time, False)

def standard_algorithm_entry(world, starts, goals, start_time, max_time):
    return standard_algorithm.standard_algorithm(len(starts), world, starts,
                                                 goals, start_time, max_time)

def window_entry(world, starts, goals, start_time, max_time, window_size):
    agents = [window.Agent(world, starts[i], goals[i], window_size)
              for i in range(len(starts))]
    return window.window_version(agents, window_size, start_time, max_time,
                                 False)

Algorithm = namedtuple('Algorithm', ['name', 'entry', 'kwargs'])
ALGORITHMS = [
    Algorithm('OD+ID', odid_entry, {}),
    Algorithm('Naive', poc_entry, {}),
    Algorithm('Base version', version1_entry, {}),
    Algorithm('Version 1b', version1b_entry, {}),
    Algorithm('Window 8', window_entry, {'window_size': 8}),
    Algorithm('Window 4', window_entry, {'window_size': 4}),
    Algorithm('Window 2', window_entry, {'window_size': 2}),
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
    result = ['instance', 'num agents', 'optimal length', 'optimal makespan']
    for algorithm in ALGORITHMS:
        result += [algorithm.name, f'{algorithm.name}_length',
                   f'{algorithm.name}_makespan']
    writer.writerow(result)

    global_start_time = timeit.default_timer()
    for problem in problems:
        print(f"Problem has {len(problem[1])} agents")
        optimal_length = 0
        optimal_makespan = 0
        try:
            for i in range(len(problem[1])):
                dist = rra_star.RRAstar(problem[0], problem[1][i],
                                        problem[2][i])
                optimal_length += dist.dist(problem[1][i])
                if dist.dist(problem[1][i]) > optimal_makespan:
                    optimal_makespan = dist.dist(problem[1][i])
        except rra_star.NoValidPathExists:
            optimal_length = 'NA'
            makespan = 'NA'

        result = [instance, len(problem[1]), optimal_length, optimal_makespan]
        for algorithm in ALGORITHMS:
            start_time = timeit.default_timer()
            try:
                paths = algorithm.entry(*problem,
                                        start_time=start_time,
                                        max_time=MAX_TIME, **algorithm.kwargs)
                length = sum(len(p) for p in paths)
                makespan = max(len(p) for p in paths)
                end_time = timeit.default_timer()
                result += [end_time - start_time, length, makespan]
            except odid.TimeExceeded:
                print('Time exceeded')
                result += ['NA', 'NA', 'NA']
            except (rra_star.NoValidPathExists, util.NoPathsFoundException):
                print('No valid path exists')
                result += ['NA', 'NA', 'NA']
            except version1b.ConflictNotSolved:
                print('Could not find a solution to a conflict')
                result += ['NA', 'NA', 'NA']
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
