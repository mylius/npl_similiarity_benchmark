import os
from multiprocessing import Pool, Process, Manager
import numpy as np
import importlib



def inheritors(klass):
    """Implementation based on https://stackoverflow.com/questions/5881873/python-find-all-classes-which-inherit-from-this-one"""
    subclasses = set()
    work = [klass]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                init = child()
                subclasses.add(init)
                work.append(child)
    return list(subclasses)
