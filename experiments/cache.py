# -*- coding: utf-8 -*-
from collections import namedtuple
import csv
from datetime import datetime
import sys
import timeit

import rra_star
from simulation import util
import id as odid
import version1
import version1b
import window

MAX_TIME = 2
OBSTACLES = 0.2

def version1_entry(world, starts, goals, start_time, max_time, weights,
                   cache):
    agents = [version1.Agent(world, starts[i], goals[i], weights=weights,
                             caching=cache)
              for i in range(len(starts))]
    return version1.version1(agents, start_time, max_time, False)

def version1b_entry(world, starts, goals, start_time, max_time, weights,
                   cache):
    agents = [version1b.Agent(world, starts[i], goals[i], weights=weights,
                              caching=cache)
              for i in range(len(starts))]
    return version1b.version1(agents, start_time, max_time, False)

def window_entry(world, starts, goals, start_time, max_time, window_size,
                 weights, cache):
    agents = [window.Agent(world, starts[i], goals[i], window_size, weights,
                           caching=cache)
              for i in range(len(starts))]
    return window.window_version(agents, window_size, start_time, max_time,
                                 False)

Weights = namedtuple('Weights',
                     ['path_len', 'conflict_count', 'partial_solved'])

Algorithm = namedtuple('Algorithm', ['name', 'entry', 'kwargs'])
ALGORITHMS = [
    Algorithm('Base', version1_entry,
              {'weights': Weights(4.743788, 5.290992, 1)}),
    Algorithm('Plus', version1b_entry,
              {'weights': Weights(0.3129151, 5.569737, 2677335)}),
    Algorithm('Window2', window_entry,
              {'window_size': 2, 'weights': Weights(3.113396, 9.46371, 1)}),
    Algorithm('Window4', window_entry,
              {'window_size': 4, 'weights': Weights(8.735623, 7.914287, 1)}),
    Algorithm('Window8', window_entry,
              {'window_size': 8, 'weights': Weights(9.352366, 22.87437, 1)}),
]

def main(runs, max_agents):
    # Generate problems
    problems = []
    while len(problems) < runs:
        for i in range(2, max_agents + 1):
            problems.append(util.generate_problem(i, 16, 16, OBSTACLES))
            if len(problems) == runs:
                break

    instance = 0
    line = []
    f = open(f'results/cache-{datetime.now()}.csv', 'w')
    writer = csv.writer(f)
    result = ['instance', 'num agents', 'optimal length', 'algorithm', 'cache',
              'time', 'length']
    writer.writerow(result)

    global_start_time = timeit.default_timer()
    for problem in problems:
        print(f'Problem has {len(problem[1])} agents')
        optimal_length = 0
        try:
            for i in range(len(problem[1])):
                dist = rra_star.RRAstar(problem[0], problem[1][i],
                                        problem[2][i])
                optimal_length += dist.dist(problem[1][i])
        except rra_star.NoValidPathExists:
            optimal_length = 'NA'

        for algorithm in ALGORITHMS:
            for cache in [True, False]:
                result = [instance, len(problem[1]), optimal_length,
                          algorithm.name, cache]
                start_time = timeit.default_timer()
                try:
                    paths = algorithm.entry(*problem,
                                            start_time=start_time,
                                            max_time=MAX_TIME,
                                            cache=cache,
                                            **algorithm.kwargs)
                    length = sum(len(p) for p in paths)
                    end_time = timeit.default_timer()
                    result += [end_time - start_time, length]
                except (odid.TimeExceeded, rra_star.NoValidPathExists,
                        util.NoPathsFoundException,
                        version1b.ConflictNotSolved):
                    result += ['NA', 'NA']

                writer.writerow(result)
                f.flush()
        instance += 1
    global_end_time = timeit.default_timer()
    print(f'Total time {(global_end_time - global_start_time) * 1000:5.3f}ms')
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
