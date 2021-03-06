2017-03-06
==========
Spend a couple of days trying to implement OD (so far without conflict
detection). Found that it first still had execution time exponential in the
number of agents. It turned out that a move should be 0 cost if an agent was
in its goal position and its action is `wait`. If this wasn't done then OD
would act more like BFS.

2017-04-04
==========
Create a separate module for problem generation and visualisation. Use random.shuffle to pick start and goal positions while making sure that they are unique,
although agents may still start in each others goal position.

2017-04-11
==========
Path simulation for finding conflicts should look at single time step while
path planning. One path is not complete yet so it could incorrectly result in
an agent going through an end point.

2017-04-14
==========
Instead of using a predefined order all agents find the conflicts that they
have. Each agent in turn gets to resolve its first conflict, resulting in a
new set of paths. Currently it is not checked whether other agents in the
conflict have prior conflicts, this is something which should be done for it to
function properly.

Conflicts are resolved in a very simple manner, all possible priority order
permutations are generated and all are checked. The one with the lowest
makespan is chosen. In the future not all permutations should be calculated;
if one agent having the highest priority is bad for the others then all
permutations where it has the highest priority should be discarded. This can
possibly be done in a simular method to Dijkstra's algorithm. A dialogue system
should be part of this.

The results for all A\* searches can possibly be cached to speed up the result,
but it may also mean that moves that are not allowed are retained in the
came\_from table. This direction should probably be investigated.

2017-04-15
==========
It may be beneficial to remove agents from each other's priority list before
trying to resolve a conflict. Investigation with statistical analysis may be
necessary to see if this is true. It seems that the PoC algorithm can find a
solution more often when agents are removed from the priority list.

2017-04-18
==========
Next time: write literature stuff. Pollock, argumentation and cooperative
pathfinding. Tool: table with parameters from literature what covers what.

2017-05-07
==========
Send an overview of literature read to Bart.

2017-05-15
==========
Write a script to benchmark OD+ID so that graphs of running times can be
created. Edit both methods to accept a maximum run time to keep benchmark time
low.

2017-07-09
==========
Changed how priorities work in version 1. Instead of assigning all agents a
position in the ordering, only a part of the agents can be assigned a position.
This means that agents that have not been given a position are automatically
sharing the last position, so a conflict with multiple agents can have only one
agent in first place, one in second place, and all others sharing third place.
Agents who share a position do not have to take each other's positions into
account.
