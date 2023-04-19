(define (domain universal_FOON)

(:requirements :adl)

(:types 
	object - object
)

(:constants
	; objects used in Agostini et al. 2021 - https://arxiv.org/abs/2007.08251
	air - object
	table - object

	; objects from provided FOON subgraph:
	cup - object
	bowl - object
	water - object
	bottle - object
)

(:predicates
	; object-state predicates (from Agostini et al. 2021 - https://arxiv.org/abs/2007.08251)
	(in ?obj_1 - object ?obj_2 - object)
	(on ?obj_1 - object ?obj_2 - object)
	(under ?obj_1 - object ?obj_2 - object)

	; physical state predicates (from FOON)
	(is-whole ?obj_1 - object)
	(is-diced ?obj_1 - object)
	(is-chopped ?obj_1 - object)
	(is-sliced ?obj_1 - object)
	(is-mixed ?obj_1 - object)
	(is-ground ?obj_1 - object)
	(is-juiced ?obj_1 - object)
	(is-spread ?obj_1 - object)
)

(:action fill_0
	; description: <bottle cup water fill cup water >
	:parameters (
	)
	:precondition (and
		(on table bottle)
		(under bottle table)
		(in cup air)
		(on table cup)
		(under cup table)
		(in bottle water)
		(under water bottle)
	)
	:effect (and
		; new effects of executing this functional unit:
		(in cup water)
		(under water cup)

		; preconditions that did not get changed in some way:
		(under bottle table)
		(in bottle water)
		(on table cup)
		(under cup table)

		; negated preconditions:
		(not (in cup air) )
	)
)

(:action pour_water_1
	; description: <cup water bowl pour bowl water cup >
	:parameters (
	)
	:precondition (and
		(on table cup)
		(under cup table)
		(in cup water)
		(under water cup)
		(in bowl air)
		(on table bowl)
		(under bowl table)
	)
	:effect (and
		; new effects of executing this functional unit:
		(in bowl water)
		(under water bowl)
		(in cup air)

		; preconditions that did not get changed in some way:
		(on table bowl)
		(under bowl table)
		(on table cup)
		(under cup table)

		; negated preconditions:
		(not (in bowl air) )
		(not (in cup water) )
	)
)

)