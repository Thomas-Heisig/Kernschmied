import sys
fname='app/services/settings_catalog.py'
stack=[]
with open(fname,'r', encoding='utf-8') as f:
    for i,line in enumerate(f, start=1):
        for j,ch in enumerate(line, start=1):
            if ch=='(':
                stack.append((i,j,line.strip()))
            elif ch==')':
                if stack:
                    stack.pop()
                else:
                    print('Unmatched ) at',i,j)
                    sys.exit(0)
if stack:
    print('Unmatched ( count', len(stack))
    print('Top unmatched at line,col:', stack[-1])
else:
    print('All matched')
