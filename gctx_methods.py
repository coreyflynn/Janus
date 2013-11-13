import cmap.io.gct as gct
import copy
import pandas as pd

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
	return copy.copy(gcto.frame[col])

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
	
