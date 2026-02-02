import random
def genotp():
    otp=''
    up=[chr(i) for i in range (ord('A'),ord('Z')+1)]
    lw=[chr(i) for i in range (ord('a'),ord('z')+1)]
    for i in range(2):
        otp=otp+random.choice(up)+str(random.randint(0,9))+random.choice(lw)
    return otp
