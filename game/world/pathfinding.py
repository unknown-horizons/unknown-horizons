# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################


from game.util import Rect, Point

# for speed testing:
import time

class Movement:
	"""Saves walkable tiles according to unit in a seperate namespace 
	SOLDIER_MOVEMENT: move directly on any walkable tile (except water, buildings, natural obstacles such as mountains
	STORAGE_CARRIAGE_MOVEMENT: move on roads
	CARRIAGE_MOVEMENT: move within the radius of a building
	SHIP_MOVEMENT: move on water
	"""
	(SOLDIER_MOVEMENT, STORAGE_CARRIAGE_MOVEMENT, SHIP_MOVEMENT, CARRIAGE_MOVEMENT) = xrange(0,4)

def check_path(path):
	i = iter(path)
	prev = i.next()
	
	err = False
	while True:
		try:
			cur = i.next()
		except StopIteration: 
			break;
		
		dist = Point(cur[0], cur[1]).distance(Point(prev[0], prev[1]))
		
		# check if it's a horizontal or vertical or diagonal movement
		# (all else is an error)
		if dist != 1 and int((dist)*100) != 141:
			err = True
			print 'PATH ERROR FROM', prev, 'TO', cur,' DIST: ', dist
			
		prev = cur
	

	import sys
	sys.stdout.flush()
	if err:
		print 'STOPPING BECAUSE OF ERRORS'
		sys.exit()
	
def findPath(source, destination, path_nodes, diagonal = False):
	## TODO: possibility to have a rect as source (for carriages that are in a building)
	""" Finds best path from source to destination via a*-algo
	"best path" means path with shortest travel time, which 
	is not necessarily the shortest path (cause roads have different speeds)
	@param source: Rect or Point (use Rect if unit is in a building)
	@param destination: Rect or Point (same as above)
	@param path_nodes: dict { (x,y) = speed_on_coords }  or list [(x,y), ..]
	@return list of coords that are part of the best path (from first coord after source to last coord before destination) or False if no path is found
	"""
	import sys
	#real_stdout = sys.stdout
	#sys.stdout = open('/tmp/oa.log', 'w')
	t0 = time.time()
	
	# if path_nodes is a list, turn it into a dict
	if isinstance(path_nodes, list):
		path_nodes = dict.fromkeys(path_nodes, 1.0)
		
	# nodes are the keys of the following dicts (x,y)
	# the val of the keys are: [previous node, distance to this node from source, distance to destination, sum of the last two elements]
	
	# values of distance is usually measured in speed
	# since you can't calculate the speed to the destination, 
	# these distances are measured in space
	# this might become a problem, but i (totycro) won't fix it, until 
	# the values of speed or slowness and such is defined
	
	# nodes that weren't processed but will be processed:
	to_check = {}
	# nodes that have been processed:
	checked = {}
	
	source_coords = source.get_coordinates()
	for c in source_coords:
		source_to_dest_dist = Point(c).distance(destination)
		to_check[c] = [None, 0, source_to_dest_dist, source_to_dest_dist]
		path_nodes[c] = 0
		
	# if one of the dest_coords is in checked, a good path is found
	# i'm not sue if this is the best path..
	dest_coords = destination.get_coordinates()
		
	# make source and target walkable
	for c in dest_coords:
		if not path_nodes.has_key(c):
			path_nodes[c] = 0
	
	while len(to_check) is not 0: # is there an isEmpty-function?
		
		min = 99999
		cur_node_coords = None
		cur_node_data = None
		
		# find next node to check, which is the one with best rating
		
		for (node_coords, node_data) in to_check.items():
			if node_data[3] < min:
				min = node_data[3]
				cur_node_coords = node_coords
				cur_node_data = node_data
				
		#print 'NEXT_NODE', cur_node_coords, ":", cur_node_data
				
		# shortcuts:
		x = cur_node_coords[0]
		y = cur_node_coords[1]
				
		if diagonal:
			neighbors = [ (xx,yy) for xx in xrange(x-1, x+2) for yy in xrange(y-1, y+2) if (xx,yy) != (x,y) and path_nodes.has_key((xx,yy))]
		else: 
			neighbors = [ i for i in [(x-1,y), (x+1,y), (x,y-1), (x,y+1) ] if path_nodes.has_key(i) ]
		for neighbor_node in neighbors:
			if checked.has_key(neighbor_node):
				continue
			
			#print 'NEW NODE', neighbor_node
			
			if not to_check.has_key(neighbor_node):
				to_check[neighbor_node] = [cur_node_coords, cur_node_data[1]+path_nodes[cur_node_coords], destination.distance(neighbor_node) ]
				to_check[neighbor_node].append(to_check[(neighbor_node)][1] + to_check[(neighbor_node)][2])
				#print 'NEW',neighbor_node, ':', to_check[neighbor_node]
			else:
				node_distance = cur_node_data[1]+path_nodes[cur_node_coords]
				# if cur_node provides a better path to neighbor_node, use it
				if to_check[(neighbor_node)][1] > node_distance:
					to_check[(neighbor_node)][0] = cur_node_coords
					to_check[(neighbor_node)][1] = node_distance
					to_check[(neighbor_node)][3] = node_distance + to_check[(neighbor_node)][2]
					#print 'OLD',neighbor_node,':', to_check[neighbor_node]
		
		checked[cur_node_coords] = cur_node_data
		del to_check[cur_node_coords]
		
		if cur_node_coords in dest_coords:
			# found best path
			path = [ cur_node_coords ]
			previous_node = cur_node_data[0]
			while previous_node is not None:
				# maybe always append here and call list.reverse afterwards (depends on speed test results)
				path.insert(0, previous_node)
				previous_node = checked[previous_node][0]

			# the following shouldn't be necessary any more
			
			#if isinstance(destination, Point):
			#	path.append((destination.x, destination.y))
			#elif isinstance(destination, Rect):
			#	# find the node next to the last node in the path
			#	# this node has to be in the destination
			#	last_node = path[ len(path) - 1 ]
			#	if last_node[0] in xrange(destination.left, destination.right+1):
			#		node_in_dest = (last_node[0], [ last_node[1]+i for i in [1,-1] if last_node[1]+i in xrange(destination.top, destination.bottom+1) ][0])
			#	elif last_node[1] in xrange(destination.top, destination.bottom+1):
			#		node_in_dest = ([ last_node[0]+i for i in [1,-1] if last_node[0]+i in xrange(destination.left, destination.right+1) ][0], last_node[1])
			#	else: assert(False)
			#	path.append(node_in_dest)
				
			t1 = time.time()
			#print 'PATH FINDING TIME', t1-t0
			print 'PATH FROM',source,'TO', destination,':', path
			if len(path_nodes) < 20:
				print 'PATH NODES', path_nodes
			check_path(path)
			#sys.stdout = real_stdout
			return path
		
	else:
		t1 = time.time()
		#print 'PATH FINDING TIME', t1-t0
		p_k = path_nodes.keys()
		p_k.sort()
		p_di = dict.fromkeys(p_k,0)
		print '_NO_ PATH FROM',source,'TO', destination, ',PATH_NODES:', p_di
		#sys.stdout = real_stdout
		return False

def test_pathfinding():
	# basic tests
	import time
	
	p = findPath(Point(1,1), Rect(2,2,2,2), [(1,2)])
	assert(p == [(1, 1), (1, 2), (2, 2)])
	
	p = findPath(Point(1,1), Rect(2,2,2,2), [(1,2)], diagonal = True)
	assert(p == [(1, 1), (2, 2)])
	
	p = findPath(Point(1,1), Rect(3,3,3,3), [(1,2),(2,2),(2,1),(2,3)])
	assert(p ==  [(1, 1), (1, 2), (2, 2), (2, 3), (3, 3)])
	
	p = findPath(Point(1,1), Rect(3,3,5,5), [(1,2),(2,2),(2,1),(2,3)])
	assert(p ==  [(1, 1), (1, 2), (2, 2), (2, 3), (3, 3)])
	