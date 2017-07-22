# -*- coding: utf-8 -*-
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

MAX_TIME = 5
OBSTACLES = 0.2
SIGMA = 1

def eval_weights(weights, num_problems, max_agents):
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
        except (odid.TimeExceeded, rra_star.NoValidPathExists):
            actual.append(float('inf'))
            continue
        # Do the actual cooperative planning
        try:
            paths = version1.version1(agents, start_time, MAX_TIME, False)
            actual.append(sum(len(path) for path in paths))
        except (odid.TimeExceeded, rra_star.NoValidPathExists):
            actual.append(float('inf'))

    diff = [res[1] - res[0] for res in zip(optimal, actual)
                           if res[1] != float('inf')]
    return sum(diff) / len(diff)

def main(max_temp, problems, max_agents):
    line = []
    f = open(f'results/annealing-{datetime.now()}.csv', 'w')
    writer = csv.writer(f)
    writer.writerow(['temp', 'score', 'path_len', 'conflict_count'])
    weights = version1.Weights(random.uniform(1, 10),
                               random.uniform(1, 10))

    score = eval_weights(weights, problems, max_agents)
    result = [max_temp, score, weights.path_len, weights.conflict_count]
    writer.writerow(result)
    f.flush()
    print(score)
    for temp in range(max_temp - 1, 0, -1):
        new_weights = version1.Weights(abs(random.gauss(weights.path_len,
                                                        SIGMA)),
                                       abs(random.gauss(weights.conflict_count,
                                                        SIGMA)))
        new_score = eval_weights(new_weights, problems, max_agents)
        prob = math.exp(-(new_score - score) / temp * 100)
        if new_score < score or random.random() <= prob:
            weights = new_weights
            score = new_score
        result = [temp, score, weights.path_len, weights.conflict_count]
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
    main(max_temp, problems, max_agents)
