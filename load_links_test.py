from atomspace.core import AtomSpace
from atomspace.csv_import import import_links_csv
from atomspace.renderer import Renderer

A = AtomSpace(with_defaults=True)
R = Renderer(A)
report = import_links_csv(A, "links.csv")
print(report)


pid = A._pred_intern["Loves"]
lid = next(iter(A._by_pred[pid]))
print(R.render(lid))
