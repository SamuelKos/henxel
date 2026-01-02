# To run this file, open this file(token_stats.py) in editor and
# Choose 'run' from popup-menu

import subprocess

# Change file to be tokenized here
path = './src/henxel/fdialog.py'
cmd = 'python -m tokenize %s' % path
res = subprocess.run(cmd.split(), stdout=subprocess.PIPE).stdout


lines = res.decode()

tokens = dict()
for line in lines.splitlines():
	#print(line)
	token_type = line.split()[1]
	num = tokens.setdefault(token_type, 0)
	tokens[token_type] = num + 1

l = list(tokens.keys())
l.sort(key=lambda k: tokens[k], reverse=True)
total = sum(tokens.values())
max_keylen = max(map(len, tokens.keys()))
patt1 = '{0:%s}\t{1}\t\t{2}' % max_keylen
patt2 = '{0:%s}\t{1}\t{2}' % max_keylen

print()
print(patt2.format('TokenType', 'Percentage', 'Num tokens'))
for key in l:
	num_tags = tokens[key]
	percentage = '{:.2%}'.format(num_tags/total)
	print(patt1.format(key, percentage, num_tags))








