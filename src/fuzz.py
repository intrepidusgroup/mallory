from random import randint

overflowstrings = ["A" * 255, "A" * 256, "A" * 257, "A" * 420, "A" * 511, "A" * 512, "A" * 1023, "A" * 1024, "A" * 2047, "A" * 2048, "A" * 4096, "A" * 4097, "A" * 5000, "A" * 10000, "A" * 20000, "A" * 32762, "A" * 32763, "A" * 32764, "A" * 32765, "A" * 32766, "A" * 32767, "A" * 32768, "A" * 65534, "A" * 65535, "A" * 65536, "%x" * 1024, "%n" * 1025 , "%s" * 2048, "%s%n%x%d" * 5000, "%s" * 30000, "%s" * 40000, "%.1024d", "%.2048d", "%.4096d", "%.8200d", "%99999999999s", "%99999999999d", "%99999999999x", "%99999999999n", "%99999999999s" * 1000, "%99999999999d" * 1000, "%99999999999x" * 1000, "%99999999999n" * 1000, "%08x" * 100, "%%20s" * 1000,"%%20x" * 1000,"%%20n" * 1000,"%%20d" * 1000, "%#0123456x%08x%x%s%p%n%d%o%u%c%h%l%q%j%z%Z%t%i%e%g%f%a%C%S%08x%%#0123456x%%x%%s%%p%%n%%d%%o%%u%%c%%h%%l%%q%%j%%z%%Z%%t%%i%%e%%g%%f%%a%%C%%S%%08x"]

def bitflipping(data,mangle_percentage = 7):
    l = len(data)
    n = int(l*mangle_percentage/100) # 7% of the bytes to be modified

    for i in range(0,n): # We change the bytes
        r = randint(0,l-1)
        data = data[0:r] + chr(randint(0,255)) + data[r+1:]
    return data

def bofinjection(data):
    l = len(data)
    r = randint(0,len(overflowstrings)-1)
    data = data[0:r] + overflowstrings[r] + data[r-l:]
    return data


def fuzz(data, bit_flip_percentage = 20, bof_injection_percentage = 20, bit_flip_density = 7):
    
    #print "Fuzz:"
    #print "    bfp:" + str(bit_flip_percentage)
    #print "    bip:" + str(bof_injection_percentage)
    
    r = randint(0,100)
    #print "    first r:" + str(r)
    was_fuzzed = False
    if r<=bit_flip_percentage:
        was_fuzzed = True
        data = bitflipping(data, bit_flip_density)

    #print "    second r:" + str(r)
    r = randint(0,100)
    if r<=bof_injection_percentage:
        was_fuzzed = True
        data = bofinjection(data)
    return was_fuzzed, data

