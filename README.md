# FOON-to-PDDL (FOON\_to\_PDDL.py) #

This code repository contains Python scripts that are designed to convert files from the [**FOON**](https://www.foonets.com) (short for the **functional object-oriented network**) dataset into [**PDDL**](https://planning.wiki/) problem and domain files.

This requires code (specifically the ```FOON_graph_analyzer.py``` and ```FOON_classes.py``` files) from the **FOON\_API** repository, which can be found [here](https://bitbucket.org/davidpaulius/foon_api/src/master/).

---

# License

>    This program is free software: you can redistribute it and/or modify
>    it under the terms of the GNU General Public License as published by
>    the Free Software Foundation, either version 3 of the License, or
>    (at your option) any later version.
>
>    This program is distributed in the hope that it will be useful,
>    but WITHOUT ANY WARRANTY; without even the implied warranty of
>    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
>    GNU General Public License for more details.
>
>    You should have received a copy of the GNU General Public License
>    along with this program.  If not, see <https://www.gnu.org/licenses/>.

---

# Running the FOON\_to\_PDDL.py script

To run this code, simply use the following line in your terminal or command line:
```
>> python FOON_to_PDDL.py --file='example.txt' [ --type=1/2] [--help]
```

Where ```example.txt``` in ```--file'example.txt'``` is the name of the text file containing the FOON graph description. 

There is an optional parameter ```--type```, which is used to only produce a single file (either domain or problem). The parameter ```--type``` takes a value of either ```1``` (domain) or ```2``` (problem). 

---

# What is happening under the hood?

A FOON subgraph file describes a cooking procedure in the form of a bipartite graph (meaning it has two types of nodes).
The _FOON graph analyzer_ (or _FGA_) (found in the **FOON_API** repository) is used to load a graph from a subgraph file.

### Translating a FOON graph to a FOON domain file

From a loaded subgraph, each functional unit is translated into _planning operators_ (defined as ```:action```). The _input nodes_ are used to define the preconditions (defined as ```:preconditions```), and the _output nodes_ are used to define the effects of the action (defined as ```:effects```). 

This is done with the following steps:

1. Take the name of an object node and set that to the current object in focus�s name (denoted as ```<focus_object>```).

2. Parse through all of the states of the object node, taking note of the following:

	-- If a node has some spatial/geometric relation state to another object (e.g. ```in [bowl]```), then the relation and the relative object are taken to produce the predicate (e.g. ```(in bowl <focus_object>)```). This is done for relations ```in```, ```on```, and ```under```. Please refer to [Agostini et al.](https://arxiv.org/abs/2007.08251) for more details on object-centered predicates.

	-- If a node has a physical state that cannot be described with object-centered predicates but which is relevant to the action (based on one's requirements), then create a predicate for that state. Examples of such states are ```whole```, ```chopped```, and ```mixed```. Many others exist in FOON.

3. If there is no indication of a spatial/geometric relation state, then assume that the object is on the working surface and the surface is under the object (i.e., ```(on table <focus_object>)``` and ```(under <focus_object> table)```).

Objects were assumed to be constants (i.e., only one instance of each object), but multiple instances of objects could be considered. However, this is not native to FOON.

### Translating a FOON graph to a FOON problem file
The ```:init``` section of the problem file considers all _starting nodes_ in the FOON file. *Starting nodes* are those nodes that are never seen as output nodes. This carries the assumption that these objects are in their basic or natural state. All of these nodes are identified using a function from the FGA (```fga._identifyKitchenItems()```). For each node, the same rules as above are applied to create predicates.

---

# Using the FOON domain and problem files

Once the files have been generated, you can use any off-the-shelf planner (e.g., [PDDL4J](https://github.com/pellierd/pddl4j) or [Fast-Downward](https://github.com/aibasel/downward)) to see if a plan can be generated. If a plan cannot be found with any FOON graph file that you are testing, be sure to carefully review the problem file for any rogue predicates that are not being satisfied in planning.

---

# FOON Graphs for Translation

There are two examples provided in this repository: ```FOON-pour_water.txt``` and ```FOON-0076-bloody_mary.txt``` (which is a simplified version of the version found in the FOON dataset).

Other graphs can also be downloaded from the **FOON\_API** repository or the [FOON website](http://foonets.com/foon_subgraphs/subgraphs/).

---

### Need Assistance? Have Questions about our Papers?

Please contact the main developer David Paulius at <davidpaulius@usf.edu> or <dpaulius@cs.brown.edu>.
