# -*- coding: utf-8 -*-
from pprint import pprint
import sys
import timeit

import rra_star
from simulation import util, visualisation
import id as odid
import poc
import version1

MAX_TIME = 2

def main(runs, max_agents):
    # Generate problems
    problems = []
    while len(problems) < runs:
        for i in range(2, max_agents):
            problems.append(util.generate_problem(i, 16, 16, 0.2))
            if len(problems) == runs:
                break

    f = open('poc_bench.csv', 'w')
    i = 0
    f.write('num,od,poc,version1\n')

    global_start_time = timeit.default_timer()
    for problem in problems:
        f.write(f'{i},')
        i += 1
        # Run OD+ID
        start_time = timeit.default_timer()
        try:
            odid.odid2(len(problem[1]), *problem, start_time=start_time,
                       max_time=MAX_TIME)
            end_time = timeit.default_timer()
            f.write(f'{end_time-start_time},')
        except odid.TimeExceeded:
            end_time = timeit.default_timer()
            print('OD+ID failed')
            f.write('NA,')
        except (rra_star.NoValidPathExists, util.NoPathsFoundException):
            print('No valid path exists')
            f.write('NA,')
        finally:
            print(f'OD  time: {(end_time - start_time) * 1000:5.3f}ms')

        # Run proof of concept
        start_time = timeit.default_timer()
        try:
            agents = [poc.Agent(problem[0], problem[1][i], problem[2][i])
                for i in range(len(problem[1]))]
            poc.poc(agents, start_time=start_time, max_time=MAX_TIME)
            end_time = timeit.default_timer()
            f.write(f'{end_time-start_time},')
        except odid.TimeExceeded:
            end_time = timeit.default_timer()
            print('POC failed')
            f.write('NA,')
        except (rra_star.NoValidPathExists, util.NoPathsFoundException):
            print('No valid path exists')
            f.write('NA,')
        finally:
            print(f'POC time: {(end_time - start_time) * 1000:5.3f}ms')

        # Run Version 1
        start_time = timeit.default_timer()
        try:
            agents = [version1.Agent(problem[0], problem[1][i], problem[2][i])
                for i in range(len(problem[1]))]
            version1.version1(agents, start_time, MAX_TIME, False)
            end_time = timeit.default_timer()
            f.write(f'{end_time-start_time}\n')
        except odid.TimeExceeded:
            end_time = timeit.default_timer()
            print('Version1 failed')
            f.write('NA\n')
        except (rra_star.NoValidPathExists, util.NoPathsFoundException):
            print('No valid path exists')
            f.write('NA\n')
        finally:
            print(f'Version1 time: {(end_time - start_time) * 1000:5.3f}ms')

        # Write latest results to file
        f.flush()
    global_end_time = timeit.default_timer()

    print(f'Final time: {(global_end_time - global_start_time) * 1000:5.3f}ms')
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
