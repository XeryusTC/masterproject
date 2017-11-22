# -*- coding: utf-8 -*-
from collections import namedtuple
import csv
from datetime import datetime
from itertools import groupby
import sys
import timeit
from pprint import pprint

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

def version1_entry(world, starts, goals, start_time, max_time, weights):
    agents = [version1.Agent(world, starts[i], goals[i], weights=weights)
              for i in range(len(starts))]
    return version1.version1(agents, start_time, max_time, False)

def version1b_entry(world, starts, goals, start_time, max_time, weights):
    agents = [version1b.Agent(world, starts[i], goals[i], weights=weights)
              for i in range(len(starts))]
    return version1b.version1(agents, start_time, max_time, False)

def standard_algorithm_entry(world, starts, goals, start_time, max_time):
    return standard_algorithm.standard_algorithm(len(starts), world, starts,
                                                 goals, start_time, max_time)

def window_entry(world, starts, goals, start_time, max_time, window_size,
                 weights):
    agents = [window.Agent(world, starts[i], goals[i], window_size, weights)
              for i in range(len(starts))]
    return window.window_version(agents, window_size, start_time, max_time,
                                 False)

Weights = namedtuple('Weights',
                     ['path_len', 'conflict_count', 'partial_solved'])

Algorithm = namedtuple('Algorithm', ['name', 'entry', 'kwargs'])
ALGORITHMS = [
    Algorithm('ODID', odid_entry, {}),
    Algorithm('Naive', poc_entry, {}),
    Algorithm('Base', version1_entry,
              {'weights': Weights(4.743788, 5.290992, 1)}),
    Algorithm('Plus', version1b_entry,
              {'weights': Weights(0.3129151, 5.569737, 2.677335)}),
    Algorithm('Window8', window_entry,
              {'window_size': 8, 'weights': Weights(9.352366, 22.87437, 1)}),
    Algorithm('Window4', window_entry,
              {'window_size': 4, 'weights': Weights(8.735623, 7.914287, 1)}),
    Algorithm('Window2', window_entry,
              {'window_size': 2, 'weights': Weights(3.113396, 9.46371, 1)}),
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
    f = open(f'results/quality-{datetime.now()}.csv', 'w')
    writer = csv.writer(f)
    result = ['instance', 'num agents', 'algorithm', 'length', 'loops']
    writer.writerow(result)

    global_start_time = timeit.default_timer()
    for problem in problems:
        num_agents = len(problem[1])
        optimal_length = 0
        print(f"Problem has {num_agents} agents")

        for algorithm in ALGORITHMS:
            result = [instance, num_agents, algorithm.name]
            start_time = timeit.default_timer()
            try:
                data = algorithm.entry(*problem,
                                       start_time=start_time,
                                       max_time=MAX_TIME,
                                       **algorithm.kwargs)
                paths = data['paths']
                length = sum(len(p) for p in paths)
                end_time = timeit.default_timer()
                loops = calculate_loops(paths)
                result += [length, loops]
            except (odid.TimeExceeded,
                    rra_star.NoValidPathExists,
                    util.NoPathsFoundException,
                    version1b.ConflictNotSolved):
                result += ['NA', 'NA']
            writer.writerow(result)
            f.flush()
        instance += 1
    global_end_time = timeit.default_timer()
    print(f'Total time: {(global_end_time - global_start_time) * 1000:5.3f}ms')
    f.close()

def calculate_loops(paths):
    clean_paths = []
    loops = 0
    for path in paths:
        nodes = {}
        clean_path = [p for p, _ in groupby(path)]
        # get the part of the path until the agent visits its goal for
        # the first time
        clean_path = clean_path[:clean_path.index(clean_path[-1])]
        for pos in clean_path:
            try:
                nodes[pos] += 1
            except KeyError:
                nodes[pos] = 0
        loops += sum(nodes.values())
    return loops

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
