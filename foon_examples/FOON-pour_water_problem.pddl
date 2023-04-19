(define (problem universal_FOON)

(:domain universal_FOON)

(:init
	(on table bottle)
	(under bottle table)
	(in cup air)
	(on table cup)
	(under cup table)
	(in bottle water)
	(under water bottle)
	(in bowl air)
	(on table bowl)
	(under bowl table)
)

(:goal (and
	(on table bowl)
	(under bowl table)
	(in bowl water)
))

)