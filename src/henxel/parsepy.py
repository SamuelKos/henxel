import tokenize
import io


# When indentation deepens, only one indent-token is generated showing current depth:
## TokenInfo(type=5 (INDENT), string='\t\t', start=(5, 0), end=(5, 2), line='\t\tprint(i)\n')

# So end[1] == current indentation depth when indenting


# When indentation diminishes, one dedent-token per indentation level being removed is generated.

# Here dedent from two levels to zero:
## TokenInfo(type=6 (DEDENT), string='', start=(7, 0), end=(7, 0), line='f1()\n')
## TokenInfo(type=6 (DEDENT), string='', start=(7, 0), end=(7, 0), line='f1()\n')

# Dedent one level from two to one:
## TokenInfo(type=6 (DEDENT), string='', start=(7, 1), end=(7, 1), line='\tprint(l)\n')

# Dedent one level from three to two:
## TokenInfo(type=6 (DEDENT), string='', start=(8, 2), end=(8, 2), line='\t\tprint(l)\n')

# Dedent two levels from three to one:
## TokenInfo(type=6 (DEDENT), string='', start=(8, 1), end=(8, 1), line='\tprint(l)\n')
## TokenInfo(type=6 (DEDENT), string='', start=(8, 1), end=(8, 1), line='\tprint(l)\n')

# So start[1] == end[1] == current indentation depth when dedenting


testfile = '/home/samuel/pyyttoni/aa.py'


def parser(fname):
	
	try:
		with open( fname, 'rb' ) as f:
		
			tokens = tokenize.tokenize( f.readline )
		
				
			for token in tokens:
				
				# token.line contains line as string which contains token.
				print(token)
##				if token.type == tokenize.NAME:
##					print(token)
				
						
			
	except IndentationError as e:
		pass
	
		
	except tokenize.TokenError as ee:
		pass
	

	
parser(testfile)
