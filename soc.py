
import sys



socvolt = [
(100.00,3.650),
(99.50,3.450),
(99.00,3.375),
(90.00,3.350),
(80.00,3.325),
(70.00,3.300),
(60.00,3.275),
(50.00,3.263),
(40.00,3.250),
(30.00,3.225),
(20.00,3.200),
(14.00,3.150),
(9.50,3.000),
(5.00,2.800),
(0.00,2.500),
]

minvolt = socvolt[-1][1]
maxvolt = socvolt[0][1]

def lookup(v):

    if v <= minvolt:
        return 0.0
    
    if v >= maxvolt:
        return 100.0

    for i in range(len(socvolt)):

        (soc, volt) = socvolt[i]

        if v >= volt:
            # print("found:", v, volt, socvolt[i])
            if i > 0:
                # print("nsock:", socvolt[i-1])
                (nsoc, nvolt) = socvolt[i-1]
                # return nsoc + ((v - nvolt)/(volt - nvolt)) * (soc - nsoc)
                inp = v - volt
                assert(inp >= 0)
                dy = nsoc - soc
                assert(dy > 0)
                dx = nvolt - volt
                assert(dx > 0)
                return soc + inp * dy / dx
            assert(0)
            


if __name__ == "__main__":

    print("socvolt:", socvolt)

    print("2.4v:", lookup(2.4))
    print("4v:", lookup(4))
    print("3.275:", lookup(3.275))
    print("3.270:", lookup(3.270))
    print(f"52.32v / {52.32/16}v", lookup(52.32/16), lookup(52.32/16)*450/100.0)

    for  i in range(20):

        v = maxvolt - i*(maxvolt-minvolt)/20

        print(f"{v:5.3} volt: {lookup(v)}%")

    v = float(sys.argv[1])
    soc = lookup(v)
    print(f"\n{v} v -> {soc} % {soc*450/100} Ah")

