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

s = [0,1,2,3]
cap[0][1] = 5
cap[1][2] = 15
cap[2][3] = 15
cap[3][0] = 10
cap[1][0] = 5
cap[2][1] = 15
cap[3][2] = 15
cap[0][3] = 10

d[0][2] = 12
# d[2][0] = 3
def func(s,cap,d):
    # i j k = flow of si to sj through link k
    f = defaultdict(lambda: defaultdict(dict))
    lp_problem = pulp.LpProblem('MinimizeZ', pulp.LpMinimize)

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
    
    for scur in s:
        in_flow = []
        out_flow = []
        demand = 0
        for s1 in s:
            for s2 in s:
                if s1 == s2:
                    continue
                for s4 in s:
                    if scur == s4:
                        continue
                    if cap[scur][s4]:
                        out_flow.append(f[s1][s2][sorted_tuple(scur,s4)])
                        in_flow.append(f[s1][s2][sorted_tuple(s4,scur)])
            demand +=  d[scur][s1] if d[scur][s1] else 0
            demand -=  d[s1][scur] if d[s1][scur] else 0
        # outflow - inflow = demand
        # if scur == 1:
        #     print(sum(out_flow))
        #     print(sum(in_flow))
        #     print(demand)
        lp_problem += sum(out_flow) - sum(in_flow) == demand
    
    for scur in s:
        outflow = []
        inflow = []
        demandgen = 0
        demandcon = 0
        for s_dest in s:
            if scur == s_dest:
                continue
            demandgen += d[scur][s_dest] if d[scur][s_dest] else 0
            demandcon += d[s_dest][scur] if d[s_dest][scur] else 0

            for s1 in s:
                    if s1 == scur:
                        continue
                    if cap[scur][s1]:
                        outflow.append(f[scur][s_dest][sorted_tuple(scur, s1)])
                        inflow.append(f[s_dest][scur][sorted_tuple(s1, scur)])
        lp_problem += sum(outflow) +demandcon == demandgen + sum(inflow)

    # for scur in s:
    #     flow_through_dest = []
    #     demand = 0
    #     for s_dest in s:
    #         if scur == s_dest:
    #             continue
    #         # demand += d[scur][s_dest] if d[scur][s_dest] else 0
    #         demand += d[s_dest][scur] if d[s_dest][scur] else 0

    #         for s1 in s:
    #                 if s1 == scur:
    #                     continue
    #                 if cap[scur][s1]:
    #                     flow_through_dest.append(f[s_dest][scur][sorted_tuple(s1, scur)])
    #     lp_problem += sum(flow_through_dest) == demand
    
    for s1 in s:
        for s2 in s:
            if s1 == s2:
                continue
            if cap[s1][s2]:       
                total_flow = []
                for s3 in s:
                    for s4 in s:
                        if s3 == s4:
                            continue
                        total_flow.append(f[s3][s4][sorted_tuple(s1,s2)])
                # total_flow <= cap
                lp_problem += sum(total_flow) <= cap[s1][s2]
                lp_problem += z*cap[s1][s2] >= sum(total_flow)
    
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
                    if cap[s3][s4] and pulp.value(f[s1][s2][sorted_tuple(s3,s4)]):
                        print('f|{}|{}|{}_{} ='.format(s1,s2,s3,s4),pulp.value(f[s1][s2][sorted_tuple(s3,s4)]))
                        
    print("z =", pulp.value(z))
    
    # print("\nAll Constraints:")
    # for name, constraint in lp_problem.constraints.items():
    #     print(name, ":", constraint)

func(s,cap,d)