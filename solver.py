from collections import defaultdict
import pulp


# x2 = pulp.LpVariable('x2', lowBound=0)

# switch list
s = []
# cap i j = link capacity of si --- sj
cap = defaultdict(lambda:defaultdict(lambda:None)) 

d = defaultdict(lambda:defaultdict(lambda:None)) 
# linknumber i j = si --- (number) --- sj
# linknumber = defaultdict(lambda:defaultdict(lambda:None)) 

def sorted_tuple(a,b):
    return tuple([a,b])

# s = [0,1,2,3,4]
# cap[0][1] = 5
# cap[1][2] = 5
# cap[2][3] = 5
# cap[3][4] = 5
# cap[4][1] = 5
# # add symmetric weight below like cap[1][0] = 5
# # cap[0][1] = 5
# # cap[1][0] = 5

# cap[1][0] = cap[0][1]
# cap[2][1] = cap[1][2]
# cap[3][2] = cap[2][3]
# cap[4][3] = cap[3][4]
# cap[1][4] = cap[4][1]

# d[0][3] = 5
# d[3][1] = 5
# d[2][0] = 3

# s = [0,1,2]
# cap[0][1] = 5
# cap[0][2] = 10
# cap[1][0] = 5
# cap[2][0] = 10
# d[1][2] = 3
# d[1][0] = 2

s = [1,2,3,4]
d[1][3] = 7
d[3][1] = 2
d[2][4] = 3
d[4][2] = 2
cap[1][2] = 10
cap[2][3] = 10
cap[1][4] = 10
cap[4][3] = 10

cap[2][1] = cap[1][2]
cap[3][2] = cap[2][3]
cap[4][1] = cap[1][4]
cap[3][4] = cap[4][3]
# s: switch list
# cap: capacity matrix
# d: demand matrix
def func(s,cap,d):
    # i j k = flow of si to sj through link k
    f = defaultdict(lambda: defaultdict(dict))
    g = defaultdict(lambda: defaultdict(dict))
    lp_problem = pulp.LpProblem('MinimizeZ', pulp.LpMinimize)

    # Initialization
    z = pulp.LpVariable('z', lowBound=0)
    for s1 in s:
        for s2 in s:
            if s1 == s2:
                continue
            for s3 in s:
                for s4 in s:
                    if s3 == s4:
                        continue
                    if cap[s3][s4]:
                        f[s1][s2][sorted_tuple(s3,s4)] = pulp.LpVariable('f|{}|{}|{}_{}'.format(s1,s2,s3,s4), lowBound=0)
    
    # Capacity constraint (#1)
    for u in s:
        for v in s:
            if u == v:
                continue
            if cap[u][v]:       
                total_flow = []
                for i in s:
                    for j in s:
                        if i == j:
                            continue
                        total_flow.append(f[i][j][sorted_tuple(u,v)])
                        total_flow.append(f[i][j][sorted_tuple(v,u)])
                # total_flow <= cap
                lp_problem += sum(total_flow) <= cap[u][v]
                lp_problem += z*cap[u][v] >= sum(total_flow)
                

    # Flow conservation (#2)
    for i in s:
        for j in s:
            if i == j:
                continue
            for u in s:
                Fij_uv = []
                Fij_vu = []
                if i==u or j==u:
                        continue
                for v in s:
                    if u == v:
                        continue
                    if cap[u][v]:
                        Fij_uv.append(f[i][j][sorted_tuple(u,v)])
                        Fij_vu.append(f[i][j][sorted_tuple(v,u)])
                lp_problem += sum(Fij_uv) == sum(Fij_vu)

    for u in s:
        outDemand_u=0
        for v in s:
            if u == v:
                continue
            outDemand_u += d[u][v] if d[u][v] else 0
        
        Fij_uv = []
        Fij_vu = []
        for v in s:
            if u == v:
                continue
            if cap[u][v]: 
                i=u
                for j in s:
                    if j==u:
                        continue
                    Fij_uv.append(f[i][j][sorted_tuple(u,v)])
            
                    Fij_vu.append(f[i][j][sorted_tuple(v,u)])
        print(Fij_uv)
        print(Fij_vu)
        print(outDemand_u)
        if len(Fij_uv) and len(Fij_vu):
            lp_problem += sum(Fij_uv) == sum(Fij_vu)+outDemand_u

    # For dst nodes (#4)
    for u in s:
        inDemand_u=0
        for v in s:
            if u == v:
                continue
            inDemand_u += d[v][u] if d[v][u] else 0
        
        Fij_uv = []
        Fij_vu = []
        for v in s:
            if u == v:
                continue
            if cap[u][v]: 
                for i in s:
                    if i==u:
                        continue
                    j=u
                    Fij_uv.append(f[i][j][sorted_tuple(u,v)])
            
                    Fij_vu.append(f[i][j][sorted_tuple(v,u)])
        if len(Fij_uv) and len(Fij_vu):
            lp_problem += sum(Fij_uv) == sum(Fij_vu)-inDemand_u

    # Add additional constraint to ensure flow is 0 for switches with no demand
    for s1 in s:
        for s2 in s:
            if s1 == s2:
                continue
            if not d[s1][s2]:
                for s3 in s:
                    for s4 in s:
                        if s3 == s4:
                            continue
                        if cap[s3][s4]:
                            lp_problem += f[s1][s2][sorted_tuple(s3, s4)] == 0
    

    lp_problem += z 
    lp_problem.solve()

    print("Status:", pulp.LpStatus[lp_problem.status])
    for s1 in s:
        for s2 in s:
            if s1 == s2:
                continue
            for s3 in s:
                for s4 in s:
                    if s3 == s4:
                        continue
                    if cap[s3][s4]:
                        print('f|{}|{}|{}_{} ='.format(s1,s2,s3,s4),pulp.value(f[s1][s2][sorted_tuple(s3,s4)]))
                        g[s1][s2][sorted_tuple(s3,s4)]=pulp.value(f[s1][s2][sorted_tuple(s3,s4)])
                        
    print("z =", pulp.value(z))
    return g
    
if __name__ == "main":
    func(s,cap,d)

