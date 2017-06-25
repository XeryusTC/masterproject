# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime
import sys
import timeit

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
              for i in range(len(starts))
    return version1.version1(agents, start_time, max_time, False)

def main(runs, max_agents):
    # Generate problems
    problems = []
    while len(problems) < runs:
        for i in range(2, max_agents):
            problems.append(util.generate_problem(i, 16, 16, OBSTACLES))
            if len(problems) == runs:
                break

    f = open(f'benchmark-{datetime.now()}.csv', 'w')
    i = 0

    f.close()


if __name__ == '__main__':
    try:
        runs = sys.argv[1]
    except IndexError:
        runs = 100
    try:
        max_agents = sys.argv[2]
    except IndexError:
        max_agents = 25
    main(runs, max_agents)
