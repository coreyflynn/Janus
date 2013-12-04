import cmap.io.gct as gct
import copy
import math
import networkx as nx
import numpy as np
import cmap.util.mongo_utils as mu

def read_gctx(path):
	'''
	reads in the file at the specified path and returns a gctx object
	
	INPUTS
	------
	path: the path at which the file to be read should be found

	OUTPUTS
	-------
	gcto: a gct.GCT() object holding the parsed gctx data

	'''
	gcto = gct.GCT(path,read=True)
	return gcto

def slice_gctx_column(gcto,col):
	'''
	slices the given column out of the the gct object supplied in gct

	INPUTS
	------
	gcto: a gct.GCT() object to be sliced
	col: the column to be sliced out, either as an index or as a named column

	OUTPUT
	------
	series: a pandas.Series holding the column of data that was sliced
	'''
	# if an index was passed, grab the appropriate column from the DataFrame
	if type(col) == int:
		col = gcto.frame.columns[col]

	# slice the column from the DataFrame an return it
	series = copy.copy(gcto.frame[col])
	return series.dropna()

def get_index_above_N(series,N=90):
	'''
	given an input pandas Series, returns a pandas Series containing all entries
	above a value of N in the input series

	INPUTS
	------
	series: a pandas Series in which to look for values greater than N
	N: a value cutoff 

	OUTPUTS
	-------
	cutoff_index_list = a lit of all the index names with vlaues above N
	'''
	cutoff_series = series[series > N]
	return copy.copy(cutoff_series.index)

def get_square_frame_from_index(gcto,indices):
	'''
	takes a list of indeces and extract the square matrix of data for those indices 
	from a given gcto object

	INPUTS
	------
	gcto: a gct.GCT object from which to extract data
	indices: a list of named indices to be extracted from gcto 

	OUTPUTS
	-------
	square_frame: a pandas.DataFrame holding all pairwise scores for the members of indices
	'''
 	gcto_frame = copy.copy(gcto.frame)
 	square_frame = gcto_frame[indices].reindex(indices)
 	return square_frame

def graph_from_square_frame(square_frame,weight_min=None):
 	'''
 	generates are networkx graph from the provided square frame.  The nodes in the generated
 	graph are named for the columns in the square frame and the edge weights in the graph are the
 	average scores in the square_frame for each pairwise

 	INPUTS
 	------
 	square_frame: a square pandas DataFrame containing all pairwise conenctions upon which to build
 		the graph
 	weight_min: a minimum weight for edges to be included in the graph.  By edfault all edges 
 		are included

 	OUTPUTS
 	-------
 	G: the generated networkx graph
 	'''
 	# first generate the nodes, naming them for the columns in square_frame and attaching metadata
 	# from mongo
 	CM = mu.CMapMongo(mongo_location=None, collection='pert_info')
 	G = nx.Graph()
 	for col in square_frame.columns:
 		metadata = CM.find({'pert_id':col})[0]
 		G.add_node(col,attr_dict=metadata)

 	#next generate all of the weighted edges
 	for row in square_frame.columns:
 		for col in square_frame.columns:
 			if not math.isnan(square_frame[row][col]) and not math.isnan(square_frame[col][row]):
	 			weight = (square_frame[row][col] + square_frame[col][row]) / 2.0
	 			if weight_min is not None:
	 				if weight >= weight_min:
			 			G.add_edge(row,col,weight=100 - weight)
			 	else:
			 		G.add_edge(row,col,weight=100 - weight)

 	return G

def graph_from_gctx_column(gcto,col,N=90,min_weight=None):
 	'''
	slices the given column out of the the gct object supplied in gct and creates
	a graph from the members of that column that have a score above N.  The input 
	gct is assumed to be a square matrix of data an annotations that can be mined
	for the construction of the graph.  All edges in the graph are preserved unless
	min_weight is given in which case only those edges in the adjacency matrix with
	a weight over min_weight.  Weights are taken to be the average score between two
	nodes in the adjacency matrix. 

	INPUTS
	------
	gcto: a gct.GCT() object to be sliced
	col: the column to be sliced out, either as an index or as a named column
	N: a value cutoff
	weight_min: a minimum weight for edges to be included in the graph.  By edfault all edges 
 		are included

	OUTPUT
	------
	G: the generated networkx graph
	'''
	#slice out the desired column
	col_data = slice_gctx_column(gcto,col)

	# get the indices of the entries in the column scoring over threshold
	indices = get_index_above_N(col_data,N)

	# construct an adjacency matrix from those indices
	sq = get_square_frame_from_index(gcto,indices)

	# build the graph and return it
	G = graph_from_square_frame(sq)
	return G

def pruned_graph_at_weight(G,weight):
	'''
	prune the input graph to contain only nodes that have an edges of the specified
	weight or below.

	INPUTS
	------
	G: a networkx graph to be pruned
	weight: the weight below which to trim edges

	OUTPUT
	------
	pruned_G: the pruned networkx graph
	'''
	# make a copy of the input graph
	pruned_G = G.copy()

	# prune the edges that fall above the weight cutoff
	pruned_G.remove_edges_from([x for x in pruned_G.edges(data=True) if x[2]['weight'] > weight])

	# prune nodes that have no edges
	for node in pruned_G.nodes():
	    if len(pruned_G.edges(node)) == 1:
	        pruned_G.remove_node(node)

	#return the pruned graph
	return pruned_G

def get_connected_components_and_distances_ratios_from_subgraph(G,Gsub,min_size=4):
	'''
	returns the connected components in the subgraph given and their average 
	distance ratios of insternal distances to external distances.  This requires
	that the full graph is specified as well as the subgraph to be computed on.

	INPUTS
	------
	G: a full networkx graph
	Gsub: a subgraph of G containing only the nodes and edges to be used for
		connected component analysis
	min_size: the minimum size of a connected component to be considered as a
		real component. defaults to 4

	OUTPUTS
	-------
	connected_components: a list of all the connected components in the graph
	distance_ratios: a list of all teh distance ratios for the connected_components
	average_distance_ratio: the average distance ratio across all components
	'''
	# compute the all pairs distance for the full graph
	all_dist = nx.all_pairs_dijkstra_path_length(G)

	# find connected components in the subgraph
	concomp = nx.connected_components(Gsub)
	concomp = [x for x in concomp if len(x) >= min_size]

	# for each connected component, find the internal distance, external distance, and compute
	# their ratio
	ratios = []
	for c in concomp:
		internal_distances = []
		external_distances = []
		
		# internal_distances
		for i in c:
			for j in c:
				if i != j:
					internal_distances.append(all_dist[i][j])

		# external_distances
		non_c = list(set(G.nodes()).difference(set(c)))
		for i in c:
			for j in non_c:
				external_distances.append(all_dist[i][j])

		#ratio
		ratios.append(np.mean(internal_distances) / np.mean(external_distances))

	# return the results
	average_ratio = np.mean(ratios)
	return concomp, ratios, average_ratio
