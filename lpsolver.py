import pulp

lp_problem = pulp.LpProblem('Minimize Z', pulp.LpMinimize)

x1 = pulp.LpVariable('x1', lowBound=0)
x2 = pulp.LpVariable('x2', lowBound=0)
z = pulp.LpVariable('z', lowBound=0)

lp_problem += x1 + x2 == 12
lp_problem += x1 <= 5
lp_problem += x2 <= 10
lp_problem += 5 * z >= x1
lp_problem += 10 * z >= x2

lp_problem += z

lp_problem.solve()


print("Status:", pulp.LpStatus[lp_problem.status])
print("Optimal Solution:")
print("x1 =", pulp.value(x1))
print("x2 =", pulp.value(x2))
print("z =", pulp.value(z))
