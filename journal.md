2017-03-06
==========
Spend a couple of days trying to implement OD (so far without conflict
detection). Found that it first still had execution time exponential in the
number of agents. It turned out that a move should be 0 cost if an agent was
in its goal position and its action is `wait`. If this wasn't done then OD
would act more like BFS.
