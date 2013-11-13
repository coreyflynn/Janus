import cmap.io.gct as gct
import copy
import math
import networkx as nx
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

def graph_from_square_frame(square_frame):
 	'''
 	generates are networkx graph from the provided square frame.  The nodes in the generated
 	graph are named for the columns in the square frame and the edge weights in the graph are the
 	average scores in the square_frame for each pairwise

 	INPUTS
 	------
 	square_frame: a square pandas DataFrame containing all pairwise conenctions upon which to build
 		the graph

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
 			if not math.isnan(square_frame[row][col]) and not math.isnan(square_frame[row][col]):
	 			weight = (square_frame[row][col] + square_frame[row][col]) / 2.0
	 			G.add_edge(row,col,weight=weight)

 	return G


	
