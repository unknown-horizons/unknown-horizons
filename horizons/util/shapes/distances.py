# Point

def distance_point_point(p1, p2):
	return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
	
def distance_point_tuple(point, (x, y)):
	return ((point.x - x) ** 2 + (point.y - y) ** 2) ** 0.5
	
def distance_point_circle(point, circle):
	dist = point.distance(circle.center) - circle.radius
	return dist if dist >= 0 else 0

def distance_point_rect(point, rect):
	return ((max(rect.left - point.x, 0, point.x - rect.right) ** 2) +
            (max(rect.top - point.y, 0, point.y - rect.bottom) ** 2)) ** 0.5
	
def distance_point_annulus(point, annulus):
	dist = point.distance(annulus.center)
	if dist < annulus.min_radius:
		return annulus.min_radius - dist
	if dist > annulus.max_radius:
		return dist - annulus.max_radius
	return 0

# Circle

def distance_circle_circle(c1, c2):
	dist = c1.distance(c2.center) - c1.radius - c2.radius
	return dist if dist >= 0 else 0

def distance_circle_tuple(circle, (x, y)):
	dist = ((circle.center.x - x) ** 2 + (circle.center.y - y) ** 2) ** 0.5 - circle.radius
	return dist if dist >= 0 else 0

def distance_circle_annulus(circle, annulus):
	dist = circle.distance(annulus.center) - circle.radius - annulus.max_radius
	return dist if dist >= 0 else 0

# Rect

def distance_rect_rect(r1, r2):
	return ((max(r1.left - r2.right, 0, r2.left - r1.right) ** 2) +
            (max(r1.top - r2.bottom, 0, r2.top - r1.bottom) ** 2)) ** 0.5
	
def distance_rect_tuple(rect, (x, y)):
	return ((max(rect.left - x, 0, x - rect.right) ** 2) +
            (max(rect.top - y, 0, y - rect.bottom) ** 2)) ** 0.5

def distance_rect_circle(rect, circle):
	dist = rect.distance(circle.center) - circle.radius
	return dist if dist >= 0 else 0

def distance_rect_annulus(rect, annulus):
	dist = rect.distance(annulus.center) - annulus.max_radius
	return dist if dist >= 0 else 0

# Annulus

def distance_annulus_annulus(a1, a2):
	dist = a1.distance(a2.center) - a1.max_radius - a2.max_radius
	return dist if dist >= 0 else 0

def distance_annulus_tuple(annulus, (x, y)):
	dist = ((annulus.center.x - x) ** 2 + (annulus.center.y - y) ** 2) ** 0.5
	if dist < annulus.min_radius:
		return annulus.min_radius - dist
	if dist > annulus.max_radius:
		return dist - annulus.max_radius
	return 0


# DEBUG
if __name__ == '__main__':
	import itertools
	import distances
	shapes = ('rect', 'point', 'tuple', 'circle', 'annulus')
	for s1, s2 in itertools.product(shapes, shapes):
		if not (hasattr(distances, 'distance_%s_%s' % (s1, s2)) or
		        hasattr(distances, 'distance_%s_%s' % (s2, s1))):
			print 'missing distance between', s1, s2
