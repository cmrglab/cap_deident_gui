

def parse_list(listStr):    #utility function parses string to listStr delimiting',' and '-'
    sc = listStr.split(',')
    for (i,s) in enumerate(sc):
        sc[i] = s.strip()

    sd = []
    for i in sc:
        if i.find('-') != -1:
            temp = i.split('-')
            min = int(temp[0])
            max = int(temp[1])
            for i in range(min, max + 1):
                sd.append(i)
        else:
            try:
                sd.append(int(i))
            except: 
                raise ParseListError
    return sd

def parse_list_reg_exp(labelStr):
    import re

    if type(labelStr) == type(0):
        return [labelStr]
    else:
        p = re.compile(labelStr)
        matched = []
        #for lab in userVars:
        #   if p.match(lab):
        #       matched.extend(ParseList( lab))
        if matched == []:
            matched.extend(parse_list( labelStr ))
        return matched

if __name__ == '__main__':
    tests = ['1-5',
              '1 -3',
              '1,2,4',
              '2, 4, 6',
              '1 - 4, 6, 8, 10',
              '1-4,5,6,8-15',
            ]
            
    for index in range(len(tests)):
        print("%s yields %s" % (tests[index], parse_list_reg_exp(tests[index])))

