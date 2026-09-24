"""Reproduce the finite Chair44 certificates from scratch (generic-port closure model).

Expected output: closed 30, classes 12, candidates 1194, atlas 44, parent candidates 697,
disjoint 116, legal 44, halving identity True; 33 first shells, 15 survive pruning, each with a
unique parent hypothesis, 0 completion failures; weak self-similarity leaves 12 classes;
virtual-pointer relations: exactly three.
"""
from fast import full2, Engine
from chair44 import chair44_children
from parent import analyse
from shells import run_checks, completion_check
from wss import WSSSystem
from vp import vp_relations

E = Engine(3)
S = full2(3, chair44_children(), E=E)
print(S.summary())
out, proto, closed, uf, atlas = analyse(3, chair44_children(), verbose=False)
ss, shells, alive, report = run_checks(proto, atlas, chair44_children())
completion_check(ss, shells, alive, report)
print("classes with weak self-similarity:", WSSSystem(E, chair44_children()).nclasses)
print("virtual-pointer relations:", dict(vp_relations(E, E.make_children(chair44_children()))))
