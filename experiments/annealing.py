# -*- coding: utf-8 -*-
from collections import namedtuple
import csv
from datetime import datetime
import math
import random
import sys
import timeit

import rra_star
from simulation import util
import id as odid
import version1
import version1b
import poc
import window


def poc_entry(world, starts, goals, start_time, max_time):
    agents = [poc.Agent(world, starts[i], goals[i])
              for i in range(len(starts))]
    return pop.poc(agents, start_time, max_time)

def version1_entry(world, starts, goals, start_time, max_time):
    agents = [version1.Agent(world, starts[i], goals[i])
              for i in range(len(starts))]
    return version1.version1(agents, start_time, max_time, False)

def version1b_entry(world, starts, goals, start_time, max_time):
    agents = [version1b.Agent(world, starts[i], goals[i])
              for i in range(len(starts))]
    return version1b.version1(agents, start_time, max_time, False)

def window_entry(world, starts, goals, start_time, max_time, window_size):
    agents = [window.Agent(world, starts[i], goals[i], window_size)
              for i in range(len(starts))]
    return window.window_version(agents, window_size, start_time, max_time,
                                 False)

Algorithm = namedtuple('Algorithm', ['name', 'entry', 'kwargs'])
ALGORITHMS = [
    Algorithm('Base version', version1_entry, {}),
    Algorithm('Version 1b', version1b_entry, {}),
    Algorithm('Window 2', window_entry, {'window_size': 2}),
    Algorithm('Window 4', window_entry, {'window_size': 4}),
    Algorithm('Window 8', window_entry, {'window_size': 8}),
]

Weights = namedtuple('Weights',
                     ['path_len', 'conflict_count', 'partial_solved'])

MAX_TIME = 2
OBSTACLES = 0.2
SIGMA = 1

def eval_weights(algorithm, weights, num_problems, max_agents):
    # Generate problems
    problems = []
    while len(problems) < num_problems:
        for i in range(2, max_agents):
            problems.append(util.generate_problem(i, 16, 16, OBSTACLES))
            if len(problems) == num_problems:
                break

    actual = []
    optimal = []
    for world, starts, goals in problems:
        start_time = timeit.default_timer()
        optimal.append(0)
        agents = [version1.Agent(world, starts[i], goals[i], weights=weights)
                  for i in range(len(starts))]
        # Calculate the sum length of the paths
        try:
            for agent in agents:
                agent.plan(start_time=start_time, max_time=MAX_TIME)
                optimal[-1] += len(agent.path)
        except (odid.TimeExceeded, rra_star.NoValidPathExists,
                util.NoPathsFoundException, version1b.ConflictNotSolved):
            actual.append(float('inf'))
            continue
        # Do the actual cooperative planning
        try:
            res = algorithm.entry(world, starts, goals, start_time, MAX_TIME,
                                    **algorithm.kwargs)
            actual.append(sum(len(path) for path in res['paths']))
        except (odid.TimeExceeded, rra_star.NoValidPathExists,
                util.NoPathsFoundException, version1b.ConflictNotSolved):
            actual.append(float('inf'))

    diff = [res[1] - res[0] for res in zip(optimal, actual)
                           if res[1] != float('inf')]
    print(diff)
    if len(diff) == 0:
        return float('inf')
    return sum(diff) / len(diff)

def main(max_temp, problems, max_agents):
    if len(ALGORITHMS) == 1:
        name = f'results/annealing-{ALGORITHMS[0].name}-{datetime.now()}.csv'
    else:
        name = f'results/annealing-{datetime.now()}.csv'
    line = []
    f = open(name, 'w')
    writer = csv.writer(f)
    titles = ['temp']
    weights = {}
    scores = {}
    for algorithm in ALGORITHMS:
        titles += [f'{algorithm.name}_score',
                   f'{algorithm.name}_len',
                   f'{algorithm.name}_conflicts',
                   f'{algorithm.name}_partial']
        weights[algorithm.name] = Weights(random.uniform(1, 10),
                                          random.uniform(1, 10),
                                          random.uniform(1, 10))
    writer.writerow(titles)

    result = [max_temp]
    for algorithm in ALGORITHMS:
        score = eval_weights(algorithm, weights[algorithm.name], problems,
                             max_agents)
        scores[algorithm.name] = score
        result += [score, weights[algorithm.name].path_len,
                   weights[algorithm.name].conflict_count,
                   weights[algorithm.name].partial_solved]
    writer.writerow(result)
    f.flush()

    for temp in range(max_temp - 1, 0, -1):
        result = [temp]
        for algorithm in ALGORITHMS:
            ws = weights[algorithm.name]
            print(algorithm.name, temp, ws)
            new_weights = Weights(abs(random.gauss(ws.path_len, SIGMA)),
                                  abs(random.gauss(ws.conflict_count, SIGMA)),
                                  abs(random.gauss(ws.partial_solved, SIGMA)))
            new_score = eval_weights(algorithm, new_weights, problems,
                                     max_agents)
            print(new_score, score, temp)
            prob = math.exp(-(new_score - score) / temp * max_temp)
            if new_score < scores[algorithm.name] or random.random() <= prob:
                weights[algorithm.name] = new_weights
                scores[algorithm.name] = new_score
            result += [scores[algorithm.name],
                       weights[algorithm.name].path_len,
                       weights[algorithm.name].conflict_count,
                       weights[algorithm.name].partial_solved]
        writer.writerow(result)
        f.flush()
    f.close()

if __name__ == '__main__':
    try:
        max_temp = int(sys.argv[1])
    except IndexError:
        max_temp = 100
    try:
        problems = int(sys.argv[2])
    except IndexError:
        problems = 25
    try:
        max_agents = int(sys.argv[3])
    except IndexError:
        max_agents = 25
    try:
        algorithm = int(sys.argv[4])
        ALGORITHMS = [ALGORITHMS[algorithm]]
    except IndexError:
        pass
    main(max_temp, problems, max_agents)
