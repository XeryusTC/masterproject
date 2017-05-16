# -*- coding: utf-8 -*-
from pprint import pprint
import sys
import timeit

import rra_star
from simulation import util, visualisation
import id as odid
import poc

MAX_TIME = 2

def main(runs, max_agents):
    # Generate problems
    problems = []
    while len(problems) < runs:
        for i in range(2, max_agents):
            problems.append(util.generate_problem(i, 16, 16, 0.2))
            if len(problems) == runs:
                break

    results = {'od': [], 'poc': []}
    global_start_time = timeit.default_timer()
    for problem in problems:
        # Run OD+ID
        start_time = timeit.default_timer()
        try:
            odid.odid2(len(problem[1]), *problem, max_time=MAX_TIME)
            end_time = timeit.default_timer()
            results['od'].append(end_time - start_time)
        except odid.TimeExceeded:
            end_time = timeit.default_timer()
            print('OD+ID failed')
        except (rra_star.NoValidPathExists, util.NoPathsFoundException):
            print('No valid path exists')
        finally:
            print(f'OD  time: {(end_time - start_time) * 1000:5.3f}ms')

        # Run proof of concept
        start_time = timeit.default_timer()
        try:
            start_time = timeit.default_timer()
            agents = [poc.Agent(problem[0], problem[1][i], problem[2][i])
                for i in range(len(problem[1]))]
            poc.poc(agents, start_time=start_time, max_time=MAX_TIME)
            end_time = timeit.default_timer()
            results['poc'].append(end_time - start_time)
        except odid.TimeExceeded:
            end_time = timeit.default_timer()
            print('POC failed')
        except (rra_star.NoValidPathExists, util.NoPathsFoundException):
            print('No valid path exists')
        finally:
            print(f'POC time: {(end_time - start_time) * 1000:5.3f}ms')
    global_end_time = timeit.default_timer()

    print(f'Final time: {(global_end_time - global_start_time) * 1000:5.3f}ms')
    print('Writing results to file')
    od_results = sorted(results['od'])
    poc_results = sorted(results['poc'])
    print(len(od_results), len(poc_results))
    with open('poc_bench.csv', 'w') as f:
        f.write('num,od,poc\n')
        for i in range(max(len(od_results), len(poc_results))):
            f.write(f'{i},')
            if i < len(od_results):
                f.write(f'{od_results[i]},')
            else:
                f.write('NA,')
            if i< len(poc_results):
                f.write(f'{poc_results[i]}\n')
            else:
                f.write('NA\n')

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
