fname='app/services/settings_catalog.py'
start=3350
end=3590
count=0
with open(fname,'r', encoding='utf-8') as f:
    for i,line in enumerate(f, start=1):
        if i<start:
            continue
        if i> end:
            break
        # naive counting
        for ch in line:
            if ch=='(':
                count+=1
            elif ch==')':
                count-=1
        print(i, count, line.rstrip())
