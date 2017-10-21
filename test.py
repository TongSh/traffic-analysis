from math import *
def angle_avg(angle,n):
    diff = 0.0
    last = angle[0]
    sum  = angle[0]
    i = 0
    print last
    for i in range(1,n):
        last += (angle[i] - angle[i - 1] + 180) % 360 - 180
        sum  += last
        #print last
    sum = float(sum)
    return (sum/n)%360


lat1,lon1,lat2,lon2 = 39.89855,116.47144,39.89845,116.47144

a = lat1 - lat2
b = lon1 - lon2
s = 2*asin(sqrt(sin(a/2)*sin(a/2)+cos(lat1)*cos(lat2)*sin(b/2)*sin(b/2)))*6378.13
print s