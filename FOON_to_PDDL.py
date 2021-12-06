'''
FOON_to_PDDL (Translator from FOON to PDDL):
-------------------------------------------
-- Written and maintained by: 
	* David Paulius (dpaulius@cs.brown.edu / davidpaulius@tum.de)

NOTE: If using this program and/or annotations provided by our lab, please kindly cite our papers
	so that others may find our work:
* Paulius et al. 2016 - https://ieeexplore.ieee.org/abstract/document/7759413/
* Paulius et al. 2018 - https://ieeexplore.ieee.org/abstract/document/8460200/

'''

### License
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.

from __future__ import print_function
import sys, os, getopt

from numpy.lib.arraysetops import isin

sys.path.append('FOON_scripts')

try:
	import FOON_graph_analyzer as fga
except ImportError:
	print(" -- ERROR: Missing 'FOON_graph_analyzer.py'!")
	print("\t-- Download here: https://bitbucket.org/davidpaulius/foon_api/src/master/")
	sys.exit()
#end

# -- variables for the FOON subgraph file name and a kitchen items file (optional - defaults to creating one with starting nodes)
FOON_subgraph_file = None
FOON_inputs_file = None

# -- these are the names of the PDDL files that are created from the FOON file:
FOON_domain_file, FOON_problem_file = None, None

# NOTE: selection: this determines whether we are making object-centered files or regular FOON-based files.
selection = 2

# NOTE: file_type (optional): this determines whether we are making only a domain file or only a problem file.
#	if not provided, both files are made regardless.
file_type = None

def _check_args():
	global FOON_subgraph_file, selection, file_type
	
	try:
		opts, _ = getopt.getopt(sys.argv[1:], 'fi:fo:ty:h', ['file=', 'format=', 'type=', 'help'])

		for opt, arg in opts:

			if opt in ('-fi', '--file'):
				print("  -- File '" + str(arg) + "' will be converted to PDDL.")
				FOON_subgraph_file = str(arg)

			elif opt in ('-fo', '--format'):
				selection = str(arg)
				print('  -- Using ' + ('object-centered predicates' if selection == 'OCP' else 'FOON-based POs and objects') + '.')

			elif opt in ('-ty', '--type'):
				file_type = int(arg)
				print('  -- Producing a ' + ('domain' if file_type == 1 else 'problem') + ' file.')
			
			elif opt in ('-h', '--help'):
				print(' -- ERROR: Incorrect argument given! Please use one of the following:')
				print('\t\t --file="XXX.txt" - provide the file named XXX.txt to the script;')
				print('\t\t --type=[1/2] - optional parameter to just produce a single PDDL file (either domain (1) or problem (2))')
				
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

def _create_PDDL_files(file_type=None):
	# NOTE: these functions are to convert the given subgraph to the object-centered predicate format
	#	as used in Agostini et al, 2021 - https://arxiv.org/abs/2007.08251

	import random

	global FOON_subgraph_file, FOON_inputs_file, FOON_domain_file, FOON_problem_file

	state_types = ['whole', 'diced', 'chopped', 'sliced', 'mixed']
	
	# -- objects where they "contain" items on top of them rather than inside (i.e., they will have "air" on top):
	surface_objects = ['pizza pan', 'plate']

	if not FOON_subgraph_file:
		FOON_subgraph_file = input('-- Enter file name and path to the FOON graph to be converted: > ')

	def _create_domain_file():
		print(' -- [FOON_to_PDDL] : Creating domain file...')

		# NOTE: PDDL conversion to domain needs to be done in the following steps:
		#	1. First, extract all of the object nodes needed to represent the provided FOON.
		#		-- We will have to use an object key (using the FOON classes) to describe each object in a unique way.
		#	2. Second, extract each functional unit from the subgraph file; each of these will form our actions.

		# -- create a FOON using the FGA code's _constructFOON() method
		fga._constructFOON(FOON_subgraph_file)

		object_types = set()
		# -- check for all possible object types:
		for N in fga.FOON_nodes[2]:
			if isinstance(N, fga.FOON.Object):
				object_types.add(N.getObjectLabel())

		# -- now that we have all functional units read, we can proceed to the annotation phase:

		# -- create the file we are going to write to:
		pddl_file = open(FOON_domain_file, 'w')

		# pddl_file.write('(define (domain ' + str(os.path.splitext(FOON_subgraph_file)[0]) + ')\n')
		pddl_file.write('(define (domain universal_FOON)\n')
		pddl_file.write('\n')
		pddl_file.write('(:requirements :adl)\n')
		
		pddl_file.write('\n')

		pddl_file.write('(:types \n')
		pddl_file.write('\tobject - object\n')
		pddl_file.write(')\n')

		pddl_file.write('\n')

		# -- write all possible object types based on the subgraph:
		pddl_file.write('(:constants\n')
		pddl_file.write('\t; objects used in Agostini et al. 2021 - https://arxiv.org/abs/2007.08251\n')
		pddl_file.write('\t' + 'air' + ' - object\n')
		pddl_file.write('\t' + 'table' + ' - object\n')
		pddl_file.write('\n\t; objects from provided FOON subgraph:\n')
		for N in object_types:
			pddl_file.write('\t' + str(_reviseObjectLabels(N)) + ' - object\n')

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
	
			pddl_file.write('(:action functional_unit_' + str(fga.FOON_lvl3.index(FU)) + '\n')

			# -- list of objects that should be ignored when repeating predicates from preconditions:
			objects_to_ignore = []

			# -- creating name for planning operators (PO) based on FOON action label and objects:
			#PO_name = str(FU.getMotion().getMotionLabel())
			#for N in range(FU.getNumberOfInputs()):
			#	# -- finding the active or focal object based on the action label:
			#	focal_object = ''
			#	if not FU.getInputNodes()[N].hasIngredients():
			#		if PO_name in ['pick-and-place', 'pour', 'sprinkle', 'insert'] and FU.getInputDescriptor(N) == 1:
			#			# -- 'pick-and-place' and 'pour' are done on an object with motion descriptor 1:
			#			focal_object = FU.getInputNodes()[N].getObjectLabel()
			#		elif PO_name in ['slice', 'dice', 'chop', 'cut', 'scoop', 'scoop and pour'] and FU.getInputDescriptor(N) == 0:
			#			# -- object being acted upon with the above labels will have a motion descriptor 0:
			#			focal_object = FU.getInputNodes()[N].getObjectLabel()
			#
			#	elif PO_name == 'mix' or PO_name == 'stir':
			#		focal_object = 'ingredients'
			#	if focal_object:
			#		PO_name += '_' + focal_object
			#		break
			#
			#pddl_file.write('(:action ' + _reviseObjectLabels(PO_name) + '_' + str(fga.FOON_lvl3.index(FU)) + '\n')

			pddl_file.write('\t; description: <' + FU.getWord2VecSentence() + '>\n')

			# -- writing parameters (i.e. input and output objects):
			pddl_file.write('\t:parameters (\n')

			pddl_file.write('\t)\n')

			# -- preconditions: all input nodes and their initial states before an action is executed
			pddl_file.write('\t:precondition (and\n')

			preconditions = []
			for N in FU.getInputList():
				# -- position_specified: flag to check if there were any object-centered information assigned to object node:
				position_specified = False

				# -- review all states in an object node:
				for S in N.getStatesList():
					if S[1] in ['in', 'on', 'under']:
						# -- get the corresponding labels:
						this_obj, relative_obj = str(_reviseObjectLabels(N.getObjectLabel())), str(_reviseObjectLabels(S[2]))
						position_specified = True

						preconditions.append( [str(S[1]), relative_obj, this_obj] )	
						if S[1] in ['in', 'on']:
							preconditions.append( ['under', this_obj, relative_obj] )	

						# -- check if there are any other states existing that required the relative object's name:
						for pred in preconditions:
							if 'LOC' in pred:
								pred[pred.index('LOC')] = relative_obj

					if S[1] in ['empty']:
						# -- emptiness is described by the object concept "air":
						preconditions.append( [('on' if N.getObjectLabel() in surface_objects else 'in'), str(_reviseObjectLabels(N.getObjectLabel())), 'air'] )	

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

			for predicate in preconditions:
				pddl_file.write('\t\t(' + predicate[0] + ' ' + predicate[1] + (str(' ' + predicate[2]) if predicate[2] and len(predicate) > 2 else '') + ')\n')	

			pddl_file.write('\t)\n')

			# -- preconditions: all output nodes and their initial states after an action is executed
			pddl_file.write('\t:effect (and\n')

			effects = []
			for N in FU.getOutputList():
				# -- position_specified: flag to check if there were any object-centered information assigned to object node:
				position_specified = False

				# -- review all states in an object node:
				for S in N.getStatesList():
					if S[1] in ['in', 'on', 'under']:
						# -- get the corresponding labels:
						this_obj, relative_obj = str(_reviseObjectLabels(N.getObjectLabel())), str(_reviseObjectLabels(S[2]))
						position_specified = True

						effects.append( [str(S[1]), relative_obj, this_obj] )	
						if S[1] in ['in', 'on']:
							effects.append( ['under', this_obj, relative_obj] )	

						# -- check if there are any other states existing that required the relative object's name:
						for pred in effects:
							if 'LOC' in pred:
								pred[pred.index('LOC')] = relative_obj
					if S[1] in ['empty']:
						# -- emptiness is described by the object concept "air":
						effects.append( [('on' if N.getObjectLabel() in surface_objects else 'in'), str(_reviseObjectLabels(N.getObjectLabel())), 'air'] )	

					if S[1] in state_types:
						if S[1] == 'mixed':
							# -- assumption: if something is mixed, then on the *lower* level, the container can be seen as a target for stirring to occur.
							#		therefore, we got to find out where the object is located to then make changes to it later.
							effects.append(['is-mixed', 'LOC', None])
			
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

			parsed_effects = []
			for predicate in effects:
				# -- checking for any effects that are not in preconditions (new effects) as well as removing duplicates:
				if predicate not in preconditions and predicate not in parsed_effects:
					parsed_effects.append(predicate)

			pddl_file.write('\t\t; new effects of executing this functional unit:\n')
			for predicate in parsed_effects:
				pddl_file.write('\t\t(' + predicate[0] + ' ' + predicate[1] + (str(' ' + predicate[2]) if predicate[2] and len(predicate) > 2 else '') + ')\n')	

			unchanged_preconditions = []
			for predicate_1 in preconditions:
				found_corresponding_pred = False
				for predicate_2 in effects:
					if predicate_1[0] not in ['on', 'in', 'under'] and predicate_2[0] not in ['on', 'in', 'under']:
						found_corresponding_pred = True

					elif predicate_1[0] == predicate_2[0] and predicate_1[1] == predicate_2[1]:
						found_corresponding_pred = True

				if not found_corresponding_pred:
					unchanged_preconditions.append(predicate_1)

			for predicate in effects:
				if predicate in preconditions:
					unchanged_preconditions.append(predicate)

			if unchanged_preconditions:
				pddl_file.write('\n\t\t; preconditions that did not get changed in some way:\n')
				for predicate in unchanged_preconditions:
					#if len(set(objects_to_ignore) & set(predicate)) == 0: # -- uncomment this to ignore return to table for some objects
					pddl_file.write('\t\t(' + predicate[0] + ' ' + predicate[1] + (str(' ' + predicate[2]) if predicate[2] and len(predicate) > 2 else '') + ')\n')	

			negated_preconditions = []
			for predicate_1 in parsed_effects:
				# -- ignore any states that completely match or are duplicated (these are for predicates that are still true):
				if predicate_1 in preconditions:
					continue

				for predicate_2 in preconditions:
					if predicate_2 in unchanged_preconditions:
						continue

					# -- checking for partial overlap for negation of states:
					if predicate_1[0] == predicate_2[0] and predicate_1[1] == predicate_2[1] and predicate_1[2] != predicate_2[2]:
						if predicate_1[2] == 'air' or predicate_2[2] == 'air':			
							# -- location-wise negation (if an object now becomes empty -- filled with "air"):
							negated_preconditions.append(predicate_2)

					elif predicate_1[0] != predicate_2[0] and predicate_1[1] == predicate_2[1] and predicate_1[2] == predicate_2[2]: 
						# -- state-wise negation:
						negated_preconditions.append(predicate_2)

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
		print(' -- [FOON_to_PDDL] : Creating problem file...')

		# NOTE: PDDL conversion to problem file needs to be done in the following steps:
		#	1. Read the kitchen items / environment file that will usually be provided to the task tree retrieval algorithm.
		#		-- Each item is listed one by one, where they can be delineated by '//' or other tokens.
		#	2. Read an existing domain file to get all of the possible objects that could exist.
		#	3. Write the kitchen items (as their respective object key) as objects that can possibly exist 

		# -- create a FOON using the FGA code's _constructFOON() method
		fga._constructFOON(FOON_subgraph_file)
		fga._buildInternalMaps()

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

		pddl_file.write(domain_lines[0].replace('domain', 'problem') + '\n')

		pddl_file.write(domain_lines[0].split('(define ')[1].replace('domain', ':domain') + '\n')

		pddl_file.write('(:init' + '\n')

		initiation_set, already_seen = [], []
		for N in kitchen_items:
			# -- position_specified: flag to check if there were any object-centered information assigned to object node:
			position_specified = False

			# -- review all states in an object node:
			for S in N.getStatesList():
				if S[1] in ['in', 'on', 'under']:
					# -- get the corresponding labels:
					this_obj, relative_obj = str(_reviseObjectLabels(N.getObjectLabel())), str(_reviseObjectLabels(S[2]))
					position_specified = True

					initiation_set.append( [str(S[1]), relative_obj, this_obj] )	
					if S[1] in ['in', 'on']:
						initiation_set.append( ['under', this_obj, relative_obj] )	

					# -- check if there are any other states existing that required the relative object's name:
					for pred in initiation_set:
						if 'LOC' in pred:
							pred[pred.index('LOC')] = relative_obj

				if S[1] in ['empty']:
					# -- emptiness is described by the object concept "air":
					initiation_set.append( [('on' if N.getObjectLabel() in surface_objects else 'in'), str(_reviseObjectLabels(N.getObjectLabel())), 'air'] )	

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
				if S[1] in ['in', 'on', 'under']:
					# -- get the corresponding labels:
					this_obj, relative_obj = str(_reviseObjectLabels(N.getObjectLabel())), str(_reviseObjectLabels(S[2]))
					position_specified = True

					goal_set.append( [str(S[1]), relative_obj, this_obj] )	
					if S[1] == 'on':
						goal_set.append( ['under', this_obj, relative_obj] )	

					# -- check if there are any other states existing that required the relative object's name:
					for pred in goal_set:
						if 'LOC' in pred:
							pred[pred.index('LOC')] = relative_obj

				if S[1] in ['empty']:
					# -- emptiness is described by the object concept "air":
					goal_set.append( [('on' if N.getObjectLabel() == 'cutting board' else 'in'), str(_reviseObjectLabels(N.getObjectLabel())), 'air'] )	

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
			if predicate not in already_seen:
				pddl_file.write('\t(' + predicate[0] + ' ' + predicate[1] + (str(' ' + predicate[2]) if predicate[2] and len(predicate) > 2 else '') + ')\n')
				already_seen.append(predicate)	

		pddl_file.write('))\n')

		pddl_file.write('\n)')

		# -- make sure to close the file after writing to it:
		pddl_file.close()
	#enddef

	
	# -- if using multiple parts of the table, you can uncomment and use the following:
	#table_positions = ['tablel', 'tablem', 'tabler']
	table_positions = ['table']

	FOON_domain_file = os.path.splitext(FOON_subgraph_file)[0] + '_domain.pddl'
	FOON_problem_file = os.path.splitext(FOON_subgraph_file)[0] + '_problem.pddl'

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
	_check_args()
	_create_PDDL_files(file_type)
