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

def version1_entry(world, starts, goals, start_time, max_time, weights):
    agents = [version1.Agent(world, starts[i], goals[i], weights=weights)
        for i in range(len(starts))]
    return version1.version1(agents, start_time, max_time, False)

def version1b_entry(world, starts, goals, start_time, max_time, weights):
    agents = [version1b.Agent(world, starts[i], goals[i], weights=weights)
        for i in range(len(starts))]
    return version1b.version1(agents, start_time, max_time, False)

Weights = namedtuple('Weights',
                     ['path_len', 'conflict_count', 'partial_solved'])

Algorithm = namedtuple('Algorithm', ['name', 'entry', 'kwargs'])
ALGORITHMS = [
    Algorithm('Base', version1_entry,
              {'weights': Weights(4.743788, 5.290992, 1)}),
    Algorithm('Plus', version1b_entry,
              {'weights': Weights(0.3129151, 5.569737, 2.677335)}),
]

def main(runs, max_agents):
    problems = []
    while len(problems) < runs:
        for i in range(2, max_agents + 1):
            problems.append(util.generate_problem(i, 16, 16, OBSTACLES))
            if len(problems) == runs:
                break

    instance = 0
    line = []
    f = open(f'results/conflictsize-{datetime.now()}.csv', 'w')
    writer = csv.writer(f)
    result = ['instance', 'num.agents'] + list(range(2, 6))
    writer.writerow(result)

    global_start_time = timeit.default_timer()
    for problem in problems:
        num_agents = len(problem[1])
        results = [instance, num_agents] + [0] * 4
        print(f"Problem has {num_agents} agents")
        start_time = timeit.default_timer()
        agents = [version1b.Agent(problem[0], problem[1][i], problem[2][i],
                                weights=Weights(0.3129151, 5.569737, 2.677335))
                  for i in range(len(problem[1]))]
        try:
            ret = version1b.version1(agents, start_time, MAX_TIME, False)
            for conflict in ret['sizes']:
                results[conflict] += 1
        except (odid.TimeExceeded, rra_star.NoValidPathExists,
                util.NoPathsFoundException, version1b.ConflictNotSolved):
            result = [instance, num_agents] + ['NA'] * 4
        writer.writerow(results)
        f.flush()
        instance += 1


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
