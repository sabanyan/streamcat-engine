class Schema:
    def __init__(self, nodes):
        self.nodes = nodes
        self.edges = []

cols = ['Time']
for i in range(5):
    cols += [f'{i}_3H', f'{i}_3V', f'{i}_4H', f'{i}_4V']

print(cols)
