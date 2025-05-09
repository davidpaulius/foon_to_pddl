from __future__ import print_function

'''
FOON_to_PDDL (FOON to PDDL Translator):
----------------------------------------
-- Written and maintained by:
    * David Paulius (dpaulius@cs.brown.edu / davidpaulius@tum.de)

-- Special thanks to Alejandro Agostini (alejandro.agostini@uibk.ac.at) for references and help in legacy code,
    as well as guiding me in this project.

NOTE: If using this program and/or annotations provided by our lab, please kindly cite our papers
	so that others may find our work:
* Paulius et al. 2016 - https://ieeexplore.ieee.org/abstract/document/7759413/
* Paulius et al. 2018 - https://ieeexplore.ieee.org/abstract/document/8460200/
'''

''' License
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.
'''

import sys
import os
import getopt
import random

last_updated = '21st March, 2025'

# -- attempt to import the FGA script:
path_to_FOON_code = os.path.join(os.path.dirname(__file__), './foon_api/')

# NOTE: we need to import some files from the FOON API directory:
if path_to_FOON_code not in sys.path:
    # -- add the directory to the FOON API scripts to the current path:
    sys.path.append(path_to_FOON_code)

try:
    import FOON_graph_analyser as fga
except ImportError:
    print(" -- ERROR: Missing 'FOON_graph_analyzer.py'!")
    print("\t-- Download here: https://github.com/davidpaulius/foon_api")
    sys.exit()
#end

# -- variables for the FOON subgraph file name and a kitchen items file (optional - defaults to creating one with starting nodes)
FOON_subgraph_file = None
FOON_inputs_file = None

# NOTE: experimental!
# -- provide a list of ingredients that a macro plan should "ignore"
ingredients_to_ignore = []

# -- these are the names of the PDDL files that are created from the FOON file:
FOON_domain_file, FOON_problem_file = None, None

# NOTE: pddl_format takes the value of either:
#   1. 'OCP' -- this will generate object-centered files for TAMP based on object-centered predicates
#   2. 'FOON' -- this will generate PDDL files used to replicate task tree retrieval using the given FOON file.
pddl_format = 'OCP'

# NOTE: file_type (optional): this determines whether we are making only a domain file or only a problem file.
#	if not provided, both files are made regardless.
file_type = None

def _check_args():
    global FOON_subgraph_file, pddl_format, file_type
    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'fi:fo:ty:h', ['file=', 'format=', 'type=', 'help'])

        for opt, arg in opts:

            if opt in ('-fi', '--file'):
                print("  -- File '" + str(arg) + "' will be converted to PDDL.")
                FOON_subgraph_file = str(arg)

            elif opt in ('-fo', '--format'):
                pddl_format = str(arg)
                print('  -- Using ' + ('object-centered predicates' if pddl_format == 'OCP' else 'FOON-based POs and objects') + '.')

            elif opt in ('-ty', '--type'):
                file_type = int(arg)
                print('  -- Producing a ' + ('domain' if file_type == 1 else 'problem') + ' file.')

            else:
                pass
    except getopt.GetoptError:
        sys.exit()
#enddef


def _reviseObjectLabels(S):
    chars_to_remove = ['{}', '{', ',', '}', ' ', '-']
    string = S
    for C in chars_to_remove:
        if C == '{}' or C == '}':
            string = string.replace(C, '')
        else:
            string = string.replace(C, '_')

    return string
#enddef


def _convert_to_PDDL(option, file_type=None, ingredient_dropout=0):
    if option == 'FOON':
        _create_PDDL_FOON(file_type)
    elif option == 'OCP':
        _create_PDDL_OCP(file_type, ingredient_dropout=ingredient_dropout)
    else:
        sys.exit(' -- ERROR: Invalid PDDL format provided! Use either \'OCP\' for TAMP format or \'FOON\' for task tree retrieval format.')
#enddef


def _create_PDDL_FOON(file_type=None):
    # NOTE: these are for the FOON-based creation of PDDL files; objects are created using the ID and ingredient name to describe objects.
    #	in other words, there will be one object instance per node in FOON.

    def _create_domain_file():
        global FOON_subgraph_file

        if not FOON_subgraph_file:
            FOON_subgraph_file = input('-- Enter file name and path to the FOON graph to be converted: > ')

        # NOTE: PDDL conversion to domain needs to be done in the following steps:
        #	1. First, extract all of the object nodes needed to represent the provided FOON.
        #		-- We will have to use an object key (using the FOON classes) to describe each object in a unique way.
        #	2. Second, extract each functional unit from the subgraph file; each of these will form our actions.

        # -- create a FOON using the FGA code's _constructFOON() method
        fga._constructFOON(FOON_subgraph_file)

        # -- now that we have all functional units read, we can proceed to the annotation phase:

        # -- create the file we are going to write to:
        pddl_file = open(os.path.splitext(FOON_subgraph_file)[0] + '_domain.pddl', 'w')

        pddl_file.write('(define (domain universal_FOON)\n')
        pddl_file.write('\n')
        pddl_file.write('(:requirements :adl)\n')

        pddl_file.write('\n')

        # -- at the macro level, we will only have types of "object":
        pddl_file.write('(:types\n')
        pddl_file.write('\tobject_node - object\n')
        pddl_file.write(')\n')

        pddl_file.write('\n')

        # -- write all objects (step 1 from above) as constants (as per suggestions on FD forum):
        pddl_file.write('(:constants\n')
        for N in fga.nodes_lvl3:
            if N.is_objectNode():
                pddl_file.write('\t' + _reviseObjectLabels(N.getObjectKey()) + ' - object_node\n')
        pddl_file.write(')\n')

        pddl_file.write('\n')

        # -- write predicates section of file:
        pddl_file.write('(:predicates\n')
        pddl_file.write('\t(is_available ?obj - object_node)\n')
        pddl_file.write(')\n')

        pddl_file.write('\n')

        # -- writing actions section of file:
        for FU in fga.FOON_lvl3:
            pddl_file.write('(:action functional_unit_' + str(fga.FOON_lvl3.index(FU)) + '\n')
            pddl_file.write('\t; description: <' + FU.getWord2VecSentence() + '>\n')

            # NOTE: skip adding parameters and just work on the constants:
            # {
                # # -- writing parameters (i.e. input and output objects):
                # pddl_file.write('\t:parameters (\n')
                # -- writing input objects:
                # pddl_file.write('\t\t; -- input objects are as follows:\n')
                # for x in range(FU.getNumberOfInputs()):
                # 	pddl_file.write('\t\t?input_' + str(x) + ' - ' + _reviseObjectLabels(FU.getInputList()[x].getObjectKey()) + '\n')

                # # -- writing output objects:
                # pddl_file.write('\t\t; -- output objects are as follows:\n')
                # for x in range(FU.getNumberOfOutputs()):
                # 	pddl_file.write('\t\t?output_' + str(x) + ' - ' + _reviseObjectLabels(FU.getOutputList()[x].getObjectKey()) + '\n')
                # pddl_file.write('\t)\n')
            # }

            pddl_file.write('\t:parameters ( )\n')

            pddl_file.write('\t:precondition (and\n')
            for N in FU.getInputList():
                pddl_file.write('\t\t(' + 'is_available ' + _reviseObjectLabels(N.getObjectKey()) + ')\n')
            pddl_file.write('\t)\n')

            pddl_file.write('\t:effect (and\n')
            for N in FU.getOutputList():
                pddl_file.write('\t\t(' + 'is_available ' + _reviseObjectLabels(N.getObjectKey()) + ')\n')
            pddl_file.write('\t)\n')

            pddl_file.write(')\n')

            pddl_file.write('\n')

        #endfor

        pddl_file.write(')')

        # -- make sure to close the file after writing to it:
        pddl_file.close()

    def _create_problem_file():
        global FOON_subgraph_file, FOON_inputs_file

        if not FOON_subgraph_file:
            FOON_subgraph_file = input('-- Enter file name and path to the FOON graph to be converted: > ')

        if not FOON_inputs_file:
            FOON_inputs_file = input('-- Enter file name and path to the environment / kitchen items file to be converted: > ')

        # NOTE: PDDL conversion to problem file needs to be done in the following steps:
        #	1. Read the kitchen items / environment file that will usually be provided to the task tree retrieval algorithm.
        #		-- Each item is listed one by one, where they can be delineated by '//' or other tokens.
        #	2. Read an existing domain file to get all of the possible objects that could exist.
        #	3. Write the kitchen items (as their respective object key) as objects that can possibly exist

        # -- read the objects available to us (i.e. the kitchen) using FGA _identifyKitchenItems function:
        kitchen_items = fga._identifyKitchenItems(FOON_inputs_file)

        # -- create the file we are going to write to:
        pddl_file = open(os.path.splitext(FOON_subgraph_file)[0].replace('_domain', '') + '_problem.pddl', 'w')
        domain_file = open(FOON_subgraph_file, 'r')
        domain_lines = domain_file.readlines()

        pddl_file.write(domain_lines[0].replace('domain', 'problem') + '\n')
        pddl_file.write('\n')
        pddl_file.write(  domain_lines[0].split('(define ')[1].replace('domain', ':domain') + '\n')
        pddl_file.write('\n')

        # objects_starting_line = 0
        # while True:
        # 	objects_starting_line += 1
        # 	if '(:types' in domain_lines[objects_starting_line]:
        # 		objects_starting_line += 1
        # 		break

        # pddl_file.write(')\n')
        # pddl_file.write('\n')

        # NOTE: no need to write objects since we are adopting the constants from the domain file:
        # # -- write all objects (step 1 from above):
        # pddl_file.write('(:objects\n')
        # while ')' not in domain_lines[objects_starting_line]:
        # 	object_line = domain_lines[objects_starting_line].split(' - ')
        # 	pddl_file.write(object_line[0] + ' - ' + object_line[0].replace('\t', '') + '\n')
        # 	objects_starting_line += 1

        # pddl_file.write(')\n')

        pddl_file.write('(:init' + '\n')
        for item in kitchen_items:
            pddl_file.write('\t' + '(is_available ' + _reviseObjectLabels(item.getObjectKey()) + ')\n')

        pddl_file.write(')\n')
        pddl_file.write('\n')

        pddl_file.write(')')

        # -- make sure to close the file after writing to it:
        pddl_file.close()

    if file_type == 1:
        _create_domain_file()
    elif file_type == 2:
        _create_problem_file()
    else:
        _create_domain_file()
        _create_problem_file()
    #endif
#enddef


def _create_PDDL_OCP(file_type=None, ingredient_dropout=0):
    # NOTE: these functions are to convert the given subgraph to the object-centered predicate format
    #	as used in Agostini et al, 2021 - https://arxiv.org/abs/2007.08251

    global FOON_subgraph_file, FOON_inputs_file, FOON_domain_file, FOON_problem_file, ingredients_to_ignore

    # -- these are the physical state of matter that we will care about when parsing FOON graphs:
    state_types = ['whole', 'diced', 'chopped', 'sliced', 'mixed', 'ground', 'juiced', 'spread']

    # -- objects where they "contain" items on top of them rather than inside (i.e., they will have "air" on top):
    air_on_objects = ['plate', 'pizza pan', 'cutting board']

    # -- these are objects that will be treated as containers:
    ingr_in_objects = []

    if not FOON_subgraph_file:
        FOON_subgraph_file = input('-- Enter file name and path to the FOON graph to be converted: > ')

    def _create_domain_file():
        print(" -- [FOON_to_PDDL] : Creating domain file named '" + FOON_domain_file + "'...")

        # NOTE: PDDL conversion to domain needs to be done in the following steps:
        #	1. First, extract all of the object nodes needed to represent the provided FOON.
        #		-- We will have to use an object key (using the FOON classes) to describe each object in a unique way.
        #	2. Second, extract each functional unit from the subgraph file; each of these will form our actions.

        # -- check for all possible object (ingredients + utensils + containers)
        # 	and ingredient-only types:
        object_types = set()

        for N in fga.FOON_nodes[-1]:
            if isinstance(N, fga.FOON.Object):
                object_types.add(N.getObjectLabel())
                # -- we will subtract the entire list from objects that have been containers:
                # if N.hasIngredients():
                    # ingredient_types.add(N.getObjectLabel())

        # -- sort ingredient names in alphabetical order:
        object_types = sorted(list(object_types))

        if ingredient_dropout != 0:
            # NOTE: the intuition here is to randomly drop a certain number of ingredients from
            #   preconditions of generated planning operators!

            # -- we will randomly decide on the number of ingredients to drop out, which could be either:
            if ingredient_dropout == 1:
                #  1) no more than half of the required ingredients.
                num_dropout = random.randint(1, round(len(ingredients_to_ignore) / 2.0))
            else:
                #  2 no more than all but one ingredient left:
                num_dropout = random.randint(1, int(len(ingredients_to_ignore) - 1))
            #endif

            # -- now we create our ingredient "black list" by randomly popping ingredients
            #       until we are left with the number of ingredients we wish to drop:
            while len(ingredients_to_ignore) > num_dropout:
                ingredients_to_ignore.pop( random.randint(0, len(ingredients_to_ignore) - 1) )
            #endfor

        #endif

        # -- now that we have all functional units read, we can proceed to the annotation phase:

        # -- create the file we are going to write to:
        pddl_file = open(FOON_domain_file, 'w')

        if ingredients_to_ignore:
            for X in range(len(ingredients_to_ignore)):
                ingredients_to_ignore[X] = _reviseObjectLabels(ingredients_to_ignore[X])

            # -- print the list of ingredients that are removed to the terminal...
            print('  -- NOTE: The following ingredients will be dropped: ' + str(ingredients_to_ignore))

            # ... and also write a comment about it in the domain file:
            pddl_file.write('; NOTE: the following ingredients will be dropped:\n')
            pddl_file.write(';\t' + str(ingredients_to_ignore) + '\n')

        # NOTE: use this to define a specific domain; otherwise, it's best to call everything
        #       the 'universal_FOON' domain:
        # pddl_file.write('(define (domain ' + str(os.path.splitext(FOON_subgraph_file)[0]) + ')\n')

        pddl_file.write('(define (domain universal_FOON)\n')
        pddl_file.write('\n')
        pddl_file.write('(:requirements :adl)\n')

        pddl_file.write('\n')

        pddl_file.write('(:types \n')
        pddl_file.write('\tobject - object\n')
        pddl_file.write(')\n')

        pddl_file.write('\n')

        # NOTE: we define all objects as constants for now. Future work should allow object instances.
        # -- write all possible object types from the subgraph as constants:
        pddl_file.write('(:constants\n')
        pddl_file.write('\t; objects from provided FOON subgraph:\n')
        for N in object_types:
            pddl_file.write('\t' + str(_reviseObjectLabels(N)) + ' - object\n')

        # -- objects that were used by Alejandro for describing objects being collision-free:
        pddl_file.write('\n\t; objects used in Agostini et al. 2021 - https://arxiv.org/abs/2007.08251\n')
        pddl_file.write('\t' + 'air' + ' - object\n')
        pddl_file.write('\t' + 'table' + ' - object\n')

        pddl_file.write(')\n')

        pddl_file.write('\n')

        pddl_file.write('(:predicates\n')
        # -- write predicates section of file (predicates are object-centered predicates):
        pddl_file.write('\t; object-state predicates (from Agostini et al. 2021 - https://arxiv.org/abs/2007.08251)\n')
        pddl_file.write('\t(in ?obj_1 - object ?obj_2 - object)\n')
        pddl_file.write('\t(on ?obj_1 - object ?obj_2 - object)\n')
        pddl_file.write('\t(under ?obj_1 - object ?obj_2 - object)\n')
        pddl_file.write('\n')

        # -- some predicates are also state-based (driven by perception):
        pddl_file.write('\t; physical state predicates (from FOON)\n')
        for S in state_types:
            pddl_file.write('\t(is-' + S + ' ?obj_1 - object)\n')

        pddl_file.write(')\n')

        pddl_file.write('\n')

        # -- writing actions section of file:
        for FU in fga.FOON_lvl3:
            # -- old way: naming planning operators as "functional_unit_XXXX":
            # pddl_file.write('(:action functional_unit_' + str(fga.FOON_lvl3.index(FU)) + '\n')

            # -- list of objects that should be ignored when repeating predicates from preconditions:
            objects_to_ignore = []

            # -- creating name for planning operators (PO) based on FOON action label and objects:
            PO_name = str(FU.getMotion().getMotionLabel())
            for N in range(FU.getNumberOfInputs()):
                # -- finding the active or focal object based on the action label:
                focal_object = ''
                if not FU.getInputNodes()[N].hasIngredients():
                    if PO_name in ['pick-and-place', 'pour', 'sprinkle', 'insert'] and FU.getInputDescriptor(N) == 1:
                        # -- 'pick-and-place' and 'pour' are done on an object with motion descriptor 1:
                        focal_object = FU.getInputNodes()[N].getObjectLabel()
                    elif PO_name in ['slice', 'dice', 'chop', 'cut', 'scoop', 'scoop and pour'] and FU.getInputDescriptor(N) == 0:
                        # -- object being acted upon with the above labels will have a motion descriptor 0:
                        focal_object = FU.getInputNodes()[N].getObjectLabel()

                elif PO_name == 'mix' or PO_name == 'stir':
                    focal_object = 'ingredients'

                if focal_object:
                    PO_name += '_' + focal_object
                    break

            pddl_file.write('(:action ' + _reviseObjectLabels(PO_name) + '_' + str(fga.FOON_lvl3.index(FU)) + '\n')

            pddl_file.write('\t; description: <' + FU.getWord2VecSentence() + '>\n')

            pddl_file.write('\t:parameters ( )\n')

            # -- preconditions: all input nodes and their initial states before an action is executed
            pddl_file.write('\t:precondition (and\n')

            preconditions = []
            for N in FU.getInputList():
                # -- position_specified: flag to check if there were any object-centered information assigned to object node:
                position_specified = False

                # -- review all states in an object node:
                for S in N.getStatesList():
                    if S[1] in ['in', 'on', 'under'] and bool(S[2]):
                        # -- get the corresponding labels:
                        oc_relation, this_obj, relative_obj = str(S[1]), str(_reviseObjectLabels(N.getObjectLabel())), str(_reviseObjectLabels(S[2]))
                        position_specified = True

                        if S[2] == 'nothing': relative_obj = 'air'

                        if relative_obj == 'air':
                            if oc_relation in ['under']:
                                oc_relation = 'on'
                                this_obj, relative_obj = relative_obj, this_obj
                            else:
                                continue

                        statement = [oc_relation, relative_obj, this_obj]

                        # -- handling containers which "hold" things on top of it (viz. cutting board):
                        if S[2] in ingr_in_objects:
                            statement[0] = 'in'

                        # -- append predicate to the list of precondition predicates for this planning operator:
                        preconditions.append(statement)
                        if S[1] == 'on' and relative_obj != 'air': # if S[1] in ['in', 'on']:
                            preconditions.append( ['under', this_obj, relative_obj] )

                        # -- check if there are any other states existing that required the relative object's name:
                        for pred in preconditions:
                            if 'LOC' in pred:
                                pred[pred.index('LOC')] = relative_obj

                    # if S[1] in ['empty']:
                    #     # -- emptiness is described by the object concept "air":
                    #     preconditions.append( [('on' if N.getObjectLabel() in air_on_objects else 'in'), str(_reviseObjectLabels(N.getObjectLabel())), 'air'] )

                    # if 'contains' in S[1]:
                    #     for I in N.getIngredients():
                    #         preconditions.append( [('on' if N.getObjectLabel() in air_on_objects else 'in'), str(_reviseObjectLabels(N.getObjectLabel())), _reviseObjectLabels(I)] )

                    if S[1] in state_types:
                        if S[1] == 'mixed':
                            # -- assumption: if something is mixed, then on the *lower* level, the container can be seen as a target for stirring to occur.
                            #		therefore, we got to find out where the object is located to then make changes to it later.
                            preconditions.append(['is-mixed', 'LOC', None])
                            #effects.append(['is-mixed', str(_reviseObjectLabels(N.getObjectLabel())), None])
                        else:
                            # -- else, just treat other types of structural states differently:
                            preconditions.append( ['is-'+ str(S[1]), str(_reviseObjectLabels(N.getObjectLabel())), None] )

                # -- if no position is specified explicitly, then we can assume that the objects are on the work surface:
                if not position_specified:
                    # -- for now, let's randomly assign certain objects to different parts of the table (i.e., table_m, table_l, or table_r):
                    table_part = table_positions[int(random.random() * len(table_positions))]

                    preconditions.append( ['under', str(_reviseObjectLabels(N.getObjectLabel())), table_part] )
                    preconditions.append( ['on', table_part, str(_reviseObjectLabels(N.getObjectLabel()))] )

            # -- remove any duplicate preconditions (turn lists to tuples then back again):
            preconditions = [list(y) for y in set([tuple(x) for x in preconditions])]

            # NOTE: dropped predicates are those containing references to objects we want removed from the recipe:
            dropped_predicates = []
            for predicate in preconditions:
                # -- if a predicate contains an ingredient that needs to be ignored, then we comment it out:
                if bool(set(predicate) & set(ingredients_to_ignore)):
                    dropped_predicates.append(predicate)
                else:
                    pddl_file.write('\t\t(' + predicate[0] + ' ' + predicate[1] + (str(' ' + predicate[2]) if predicate[2] and len(predicate) > 2 else '') + ')\n')

            # -- some objects can be dropped (i.e., simply commented out) from the PDDL file:
            if dropped_predicates:
                pddl_file.write('\n\t\t; NOTE: the following predicates were removed due to ingredient dropout:\n')
                for predicate in dropped_predicates:
                    pddl_file.write('\t\t; (' + predicate[0] + ' ' + predicate[1] + (str(' ' + predicate[2]) if predicate[2] and len(predicate) > 2 else '') + ')\n')

            pddl_file.write('\t)\n')

            # -- preconditions: all output nodes and their initial states after an action is executed
            pddl_file.write('\t:effect (and\n')

            effects = []
            for N in FU.getOutputList():
                # -- position_specified: flag to check if there were any object-centered information assigned to object node:
                position_specified = False

                # -- review all states in an object node:
                for S in N.getStatesList():
                    if S[1] in ['in', 'on', 'under'] and bool(S[2]):
                        # -- get the corresponding labels:
                        oc_relation, this_obj, relative_obj = str(S[1]), str(_reviseObjectLabels(N.getObjectLabel())), str(_reviseObjectLabels(S[2]))
                        position_specified = True

                        if S[2] == 'nothing': relative_obj = 'air'

                        if relative_obj == 'air':
                            if oc_relation in ['under']:
                                oc_relation = 'on'
                                this_obj, relative_obj = relative_obj, this_obj
                            else:
                                continue

                        statement = [oc_relation, relative_obj, this_obj]

                        # -- handling containers which "hold" things on top of it (viz. cutting board):
                        if S[2] in ingr_in_objects:
                            statement[0] = 'in'

                        # -- append predicate to the list of effect predicates for this planning operator:
                        effects.append(statement)
                        if S[1] == 'on': # if S[1] in ['in', 'on']:
                            effects.append( ['under', this_obj, relative_obj] )

                        # -- check if there are any other states existing that required the relative object's name:
                        for pred in effects:
                            if 'LOC' in pred:
                                pred[pred.index('LOC')] = relative_obj

                    # if S[1] in ['empty']:
                    #     # -- emptiness is described by the object concept "air":
                    #     effects.append( [('on' if N.getObjectLabel() in air_on_objects else 'in'), str(_reviseObjectLabels(N.getObjectLabel())), 'air'] )

                    # if 'contains' in S[1]:
                    #     for I in N.getIngredients():
                    #         effects.append( [('on' if N.getObjectLabel() in air_on_objects else 'in'), str(_reviseObjectLabels(N.getObjectLabel())), _reviseObjectLabels(I)] )

                    if S[1] in state_types:
                        if S[1] == 'mixed':
                            # -- assumption: if something is mixed, then on the *lower* level, the container can be seen as a target for stirring to occur.
                            #		therefore, we got to find out where the object is located to then make changes to it later.
                            effects.append(['is-mixed', 'LOC', None])
                            #effects.append(['is-mixed', str(_reviseObjectLabels(N.getObjectLabel())), None])
                        else:
                            # -- else, just treat other types of structural states differently:
                            effects.append( ['is-'+ str(S[1]), str(_reviseObjectLabels(N.getObjectLabel())), None] )

                # -- if no position is specified explicitly, then we can assume that the objects are on the work surface:
                if not position_specified:
                    if FU.getMotion().getMotionLabel() == 'scoop':
                        if FU.getMotionDescriptor(FU.getOutputNodes().index(N), is_input=False) == 1 and N.hasIngredients():
                            # -- if we are scooping, then the object would actually be in the hand and not the table:
                            objects_to_ignore.append(N.getObjectLabel())
                    else:
                        table_part = table_positions[int(random.random() * len(table_positions))]

                        effects.append( ['under', str(_reviseObjectLabels(N.getObjectLabel())), table_part] )
                        effects.append( ['on', table_part, str(_reviseObjectLabels(N.getObjectLabel()))] )

            # -- remove any duplicate effects (turn lists to tuples then back again):
            preconditions = [list(y) for y in set([tuple(x) for x in preconditions])]

            parsed_effects = []
            for predicate in effects:
                # -- checking for any effects that are not in preconditions (new effects) as well as removing duplicates:
                if predicate not in preconditions and predicate not in parsed_effects:
                    parsed_effects.append(predicate)

            pddl_file.write('\t\t; new effects of executing this functional unit:\n')
            for predicate in parsed_effects:
                pddl_file.write('\t\t(' + predicate[0] + ' ' + predicate[1] + (str(' ' + predicate[2]) if predicate[2] and len(predicate) > 2 else '') + ')\n')

            # NOTE: we are searching for any predicates that may exist in both preconditions and effects:
            unchanged_preconditions = []
            for predicate in preconditions:
                if predicate in effects:
                    unchanged_preconditions.append(predicate)

            # negated_preconditions = []
            # for predicate_1 in parsed_effects:
            #     for predicate_2 in unchanged_preconditions:
            #         # -- checking for partial overlap for negation of states:
            #         if predicate_1[0] == predicate_2[0] and predicate_1[1] == predicate_2[1] and predicate_1[2] != predicate_2[2]:
            #             # -- looking for any evidence of changes:
            #             add_to_negation = False

            #             if predicate_2[0] == 'under' and predicate_2[2] == 'table':
            #                 # -- in the case of an object that used to be on the table,
            #                 #       we need to negate that predicate:
            #                 add_to_negation = True

            #             # NOTE: checking if ingredients have been transferred in some way:
            #             if not add_to_negation:

            #                 for N in FU.getOutputList():
            #                     if 'air' in predicate_2:
            #                         if N.getObjectLabel() == predicate_2[1].replace('_', ' ') and len(N.getIngredients()) > 0:
            #                             # -- intuition :- if an object was seen as empty (i.e., has "air") but now it has ingredients,
            #                             #       then we need to check if that object now contains at least ingredient:
            #                             add_to_negation = True

            #                     elif N.getObjectLabel() == predicate_2[2].replace('_', ' ') and predicate_2[1].replace('_', ' ') not in N.getIngredients():
            #                         # -- intuition :- if an object was under something before,
            #                         #       we check if there is evidence that the object is no longer under that object
            #                         #           (e.g., the container is empty or no longer contains that object)
            #                         add_to_negation = True

            #                     if add_to_negation:
            #                         break

            #             if add_to_negation:
            #                 negated_preconditions.append(predicate_2)
            #                 unchanged_preconditions.remove(predicate_2)

            #         elif predicate_1[0] != predicate_2[0] and predicate_1[0] in ['on', 'under'] and predicate_2[0] in ['on', 'under']:
            #             # -- maybe there is a predicate that indicates some other state change for something else:
            #             if predicate_1[1] == predicate_2[2] and predicate_1[2] == predicate_2[1]:
            #                 # -- state-wise negation:
            #                 negated_preconditions.append(predicate_2)
            #                 unchanged_preconditions.remove(predicate_2)

            #         elif predicate_1[0] != predicate_2[0] and predicate_1[1] == predicate_2[1] and predicate_1[2] == predicate_2[2]:
            #             # -- state-wise negation:
            #             negated_preconditions.append(predicate_2)
            #             unchanged_preconditions.remove(predicate_2)

            negated_preconditions = []
            for predicate in preconditions:
                if predicate not in parsed_effects and predicate not in unchanged_preconditions:
                    negated_preconditions.append(predicate)

            if unchanged_preconditions:
                pddl_file.write('\n\t\t; preconditions that did not get changed in some way:\n')
                for predicate in unchanged_preconditions:
                    #if len(set(objects_to_ignore) & set(predicate)) == 0: # -- uncomment this to ignore return to table for some objects
                    pddl_file.write('\t\t(' + predicate[0] + ' ' + predicate[1] + (str(' ' + predicate[2]) if predicate[2] and len(predicate) > 2 else '') + ')\n')

            if negated_preconditions:
                pddl_file.write('\n\t\t; negated preconditions:\n')
                for predicate in negated_preconditions:
                    pddl_file.write('\t\t(not (' + predicate[0] + ' ' + predicate[1] + (str(' ' + predicate[2]) if predicate[2] and len(predicate) > 2 else '') + ') )\n')

            pddl_file.write('\t)\n')

            pddl_file.write(')\n')

            pddl_file.write('\n')

        #endfor

        pddl_file.write(')')

        # -- make sure to close the file after writing to it:
        pddl_file.close()
    #enddef

    def _create_problem_file():
        print(" -- [FOON_to_PDDL] : Creating problem file named '" + FOON_problem_file + "'...")

        # NOTE: PDDL conversion to problem file needs to be done in the following steps:
        #	1. Read the kitchen items / environment file that will usually be provided to the task tree retrieval algorithm.
        #		-- Each item is listed one by one, where they can be delineated by '//' or other tokens.
        #	2. Read an existing domain file to get all of the possible objects that could exist.
        #	3. Write the kitchen items (as their respective object key) as objects that can possibly exist

        # -- read the objects available to us (i.e. the kitchen) using FGA's _identifyKitchenItems function:
        if FOON_inputs_file:
            # -- use an existing list with the following:
            kitchen_items = fga._identifyKitchenItems(FOON_inputs_file)
        else:
            # -- just in case, delete the current inputs-only node list and generate a new one:
            try:
                os.remove('FOON-input_only_nodes.txt')
            except FileNotFoundError:
                pass
            kitchen_items = fga._identifyKitchenItems()
        #end

        # -- create the file we are going to write to:
        pddl_file = open(os.path.splitext(FOON_subgraph_file)[0].replace('_domain', '') + '_problem.pddl', 'w')
        domain_file = open(os.path.splitext(FOON_subgraph_file)[0] + '_domain.pddl', 'r')
        domain_lines = domain_file.readlines()

        # -- use the domain file's domain name for defining this problem:
        start = 0
        while domain_lines[start].startswith(';'):
            # -- this is done in case we have some comments about dropout:
            start += 1

        if ingredients_to_ignore:
            for X in range(len(ingredients_to_ignore)):
                ingredients_to_ignore[X] = _reviseObjectLabels(ingredients_to_ignore[X])

            # -- write the list of dropped ingredients to the problem file:
            pddl_file.write('; NOTE: the following ingredients will be dropped:\n')
            pddl_file.write(';\t' + str(ingredients_to_ignore) + '\n')

        pddl_file.write(domain_lines[start].replace('domain', 'problem') + '\n')
        pddl_file.write(domain_lines[start].split('(define ')[1].replace('domain', ':domain') + '\n')

        pddl_file.write('(:init' + '\n')

        initiation_set, already_seen = [], []
        for N in kitchen_items:
            # -- position_specified: flag to check if there were any object-centered information assigned to object node:
            position_specified = False

            # -- review all states in an object node:
            for S in N.getStatesList():
                if S[1] in ['in', 'on', 'under'] and bool(S[2]):
                    # -- get the corresponding labels:
                    oc_relation, this_obj, relative_obj = str(S[1]), str(_reviseObjectLabels(N.getObjectLabel())), str(_reviseObjectLabels(S[2]))
                    position_specified = True

                    if S[2] == 'nothing': relative_obj = 'air'

                    if relative_obj == 'air':
                        if oc_relation in ['under']:
                            oc_relation = 'on'
                            this_obj, relative_obj = relative_obj, this_obj
                        else:
                            continue

                    initiation_set.append( [oc_relation, relative_obj, this_obj] )
                    if S[1] == 'on' and relative_obj != 'air': # if S[1] in ['in', 'on']:
                        initiation_set.append( ['under', this_obj, relative_obj] )

                    # -- check if there are any other states existing that required the relative object's name:
                    for pred in initiation_set:
                        if 'LOC' in pred:
                            pred[pred.index('LOC')] = relative_obj

                # if S[1] in ['empty']:
                #     # -- emptiness is described by the object concept "air":
                #     initiation_set.append( [('on' if N.getObjectLabel() in air_on_objects else 'in'), str(_reviseObjectLabels(N.getObjectLabel())), 'air'] )

                # if S[1] == 'contains':
                #     for I in N.getIngredients():
                #         initiation_set.append( [('on' if N.getObjectLabel() in air_on_objects else 'in'), str(_reviseObjectLabels(N.getObjectLabel())), _reviseObjectLabels(I)] )

                if S[1] in state_types:
                    if S[1] == 'mixed':
                        # -- assumption: if something is mixed, then on the *lower* level, the container can be seen as a target for stirring to occur.
                        #		therefore, we got to find out where the object is located to then make changes to it later.
                        initiation_set.append(['is-mixed', 'LOC', None])
                    else:
                        # -- else, just treat other types of structural states differently:
                        initiation_set.append( ['is-'+ str(S[1]), str(_reviseObjectLabels(N.getObjectLabel())), None] )

            # -- if no position is specified explicitly, then we can assume that the objects are on the work surface:
            if not position_specified:
                # -- for now, let's randomly assign certain objects to different parts of the table (i.e., table_m, table_l, or table_r):
                table_part = table_positions[int(random.random() * len(table_positions))]

                initiation_set.append( ['under', str(_reviseObjectLabels(N.getObjectLabel())), table_part] )
                initiation_set.append( ['on', table_part, str(_reviseObjectLabels(N.getObjectLabel()))] )
            #endif
        #endfor

        for predicate in initiation_set:
            if predicate not in already_seen:
                already_seen.append(predicate)
                pddl_file.write('\t(' + predicate[0] + ' ' + predicate[1] + (str(' ' + predicate[2]) if predicate[2] and len(predicate) > 2 else '') + ')\n')

        pddl_file.write(')\n')
        pddl_file.write('\n')

        pddl_file.write('(:goal (and\n')

        # -- now we need to define the goal for this subgraph by using the goal markers found in subgraphs:
        goal_set, already_seen = [], []
        for N in fga.FOON_nodes[2]:
            # -- make sure we look only at object nodes (as motion nodes are also in this list) and the object node must be a goal:
            if not isinstance(N, fga.FOON.Object) or not N.isGoal:
                continue

            # -- position_specified: flag to check if there were any object-centered information assigned to object node:
            position_specified = False

            for S in N.getStatesList():
                if S[1] in ['in', 'on', 'under'] and bool(S[2]):
                    # -- get the corresponding labels:
                    oc_relation, this_obj, relative_obj = str(S[1]), str(_reviseObjectLabels(N.getObjectLabel())), str(_reviseObjectLabels(S[2]))
                    position_specified = True

                    if S[2] == 'nothing': relative_obj = 'air'

                    if relative_obj == 'air':
                        if oc_relation in ['under']:
                            oc_relation = 'on'
                            this_obj, relative_obj = relative_obj, this_obj
                        else:
                            continue

                    goal_set.append( [oc_relation, relative_obj, this_obj] )
                    if S[1] == 'on' and relative_obj != 'air':
                        goal_set.append( ['under', this_obj, relative_obj] )

                    # -- check if there are any other states existing that required the relative object's name:
                    for pred in goal_set:
                        if 'LOC' in pred:
                            pred[pred.index('LOC')] = relative_obj

                # if S[1] in ['empty']:
                #     # -- emptiness is described by the object concept "air":
                #     goal_set.append( [('on' if N.getObjectLabel() == 'cutting board' else 'in'), str(_reviseObjectLabels(N.getObjectLabel())), 'air'] )

                # if S[1] == 'contains':
                #     for I in N.getIngredients():
                #         initiation_set.append( [('on' if N.getObjectLabel() in air_on_objects else 'in'), str(_reviseObjectLabels(N.getObjectLabel())), _reviseObjectLabels(I)] )

                if S[1] in state_types:
                    if S[1] == 'mixed':
                        # -- assumption: if something is mixed, then on the *lower* level, the container can be seen as a target for stirring to occur.
                        #		therefore, we got to find out where the object is located to then make changes to it later.
                        goal_set.append(['is-mixed', 'LOC', None])
                    else:
                        # -- else, just treat other types of structural states differently:
                        goal_set.append( ['is-'+ str(S[1]), str(_reviseObjectLabels(N.getObjectLabel())), None] )

            # -- if no position is specified explicitly, then we can assume that the objects are on the work surface (i.e., table):
            if not position_specified:
                # -- for now, let's randomly assign certain objects to different parts of the table (i.e., table_m, table_l, or table_r):
                table_part = table_positions[int(random.random() * len(table_positions))]

                goal_set.append( ['under', str(_reviseObjectLabels(N.getObjectLabel())), table_part] )
                goal_set.append( ['on', table_part, str(_reviseObjectLabels(N.getObjectLabel()))] )

        for predicate in goal_set:
            # -- if there were some ingredients we wanted to drop, then we drop them also from the goal:
            if bool(set(predicate) & set(ingredients_to_ignore)):
                continue

            if predicate not in already_seen:
                pddl_file.write('\t(' + predicate[0] + ' ' + predicate[1] + (str(' ' + predicate[2]) if predicate[2] and len(predicate) > 2 else '') + ')\n')
                already_seen.append(predicate)

        pddl_file.write('))\n')

        pddl_file.write('\n)')

        # -- make sure to close the file after writing to it:
        pddl_file.close()
    #enddef

    # -- older table_positions (directly from Alejandro) = ['tablel', 'tablem', 'tabler']
    table_positions = ['table']

    FOON_domain_file = os.path.splitext(FOON_subgraph_file)[0] + '_domain.pddl'
    FOON_problem_file = os.path.splitext(FOON_subgraph_file)[0] + '_problem.pddl'

    # -- create a FOON using the FGA code's _constructFOON() method
    fga._constructFOON(FOON_subgraph_file)

    fga.flag_buildObjectToUnitMap = True

    fga._buildInternalMaps()

    if file_type == 1:
        _create_domain_file()
    elif file_type == 2:
        _create_problem_file()
    else:
        _create_domain_file()
        print()
        _create_problem_file()
        print()
    #endif
#enddef


if __name__ == '__main__':

    print('\n< FOON_to_PDDL: converting FOON graph to PDDL code (last updated: ' + last_updated + ')>\n')

    _check_args()
    _convert_to_PDDL(pddl_format, file_type)
