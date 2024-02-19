from __future__ import annotations

from types import ModuleType
from typing import Tuple

import numpy
from asteval import Interpreter


class VariableTable:
    def __init__(self):
        self.variable_objs = {}
        self.variable_docs = {}
        self._parent_tables = []

    def add_variable(self, name, obj, docs):
        self.variable_objs[name] = obj
        self.variable_docs[name] = docs

    def get_variable(self, name) -> Tuple["object", str]:
        return self.variable_objs[name], self.variable_docs[name]

    def get_prompt(self, no_doc=False):
        prompt_dict = {}
        for table in self._parent_tables:
            prompt_dict.update(table.get_local_prompt_dict(no_doc=no_doc))
        prompt_dict.update(self.get_local_prompt_dict(no_doc=no_doc))
        prompt_list = [f"{prompt}" for prompt in prompt_dict.values()]
        return "\n".join(prompt_list)

    def get_local_prompt(self):
        prompt_dict = self.get_local_prompt_dict()
        prompt_list = [f"{prompt}" for prompt in prompt_dict.values()]
        return "\n".join(prompt_list)

    def get_local_prompt_dict(self, no_doc=False):
        prompt_dict = {}
        for name, docs in self.variable_docs.items():
            value = self.variable_objs[name]
            if no_doc:
                prompt_dict[name] = f"{name}: {get_repr_in_prompt(value)}"
            else:
                prompt_dict[name] = f"{name}: {docs} {get_repr_in_prompt(value)}"
        return prompt_dict

    def is_empty(self):
        return len(self.get_prompt().strip()) == 0

    def is_local_empty(self):
        return len(self.get_local_prompt().strip()) == 0

    def get_interpreter(self):
        interpreter = Interpreter(config={'import': True, 'importfrom': True})
        self.add_to_interpreter(interpreter)
        return interpreter

    def add_to_interpreter(self, interpreter: Interpreter):
        for parent_table in self._parent_tables:
            for name, obj in parent_table.variable_objs.items():
                interpreter.symtable[name] = obj
        for name, obj in self.variable_objs.items():
            interpreter.symtable[name] = obj
        return interpreter

    def push_new_table(self) -> VariableTable:
        new_table = VariableTable()
        new_table._parent_tables = self._parent_tables + [self]
        return new_table

    def pop_table(self) -> VariableTable:
        if len(self._parent_tables) == 0:
            return None
        return self._parent_tables[-1]

    def filter_table(self, names_to_keep):
        for name in list(self.variable_objs.keys()):
            if name not in names_to_keep:
                self.variable_objs.pop(name)
                self.variable_docs.pop(name)


def get_repr_in_prompt(value):
    long_limit = 3
    if isinstance(value, int) or isinstance(value, float):
        return f"Value: {value}"
    elif isinstance(value, str):
        return f"Value: '{value}'"
    elif isinstance(value, tuple) or isinstance(value, list):
        res = "[" if isinstance(value, list) else "("
        if len(value) > long_limit:
            res += get_repr_in_prompt(value[0]) + ", " + get_repr_in_prompt(
                value[1]) + ", ..."
            res += ", " + get_repr_in_prompt(value[-1])
        else:
            res += ", ".join([get_repr_in_prompt(v) for v in value])
        res += "]" if isinstance(value, list) else ")"
        return f"Value: {res}"
    elif isinstance(value, dict):
        res = "{"
        dict_kv_list = [f"{k}: {get_repr_in_prompt(v)}" for k, v in value.items()]
        if len(dict_kv_list) > long_limit:
            res += ", ".join(dict_kv_list[:long_limit])
            res += ", ..."
            res += ", ".join(dict_kv_list[-1])
        else:
            res += ", ".join(dict_kv_list)
        res += "}"
        return f"Value: {res}"
    elif isinstance(value, numpy.ndarray):
        shape = value.shape
        return f"Type: numpy array, Shape: {shape}"
    elif isinstance(value, ModuleType):
        name = value.__name__.split(".")[-1]
        return f"Module: {name}"
    else:
        repr_str, classname = get_truncated_repr(value)
        return f"Value: {repr_str} Type: {classname}"


def get_truncated_repr(obj, limit=30):
    classname = obj.__class__.__name__
    repr_str = repr(obj)
    if len(repr_str) > limit:
        repr_str = repr_str[:limit] + "..." + repr_str[-1:]
    return repr_str, classname
