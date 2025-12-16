# encoding = "utf-8"

from typing import Dict


class Instruction:
    """An instruction template."""

    def __init__(self):
        self.id = None

    def initialization(self, args=None):
        '''initialization an instruction and its corresponding description'''
        raise NotImplementedError("`initialization` not implemented.")

    def build_description(self):
        '''build a one-sentence English instruction description based on the current instruction'''
        raise NotImplementedError("`build_description` not implemented.")

    def get_instruction_args(self):
        '''get the instruction arguments'''
        raise NotImplementedError("`get_instruction_args` not implemented.")

    def modification(self):
        '''modify the instruction and its corresponding description'''
        raise NotImplementedError("`modification` not implemented.")

    def check_following(self, generation):
        '''check whether the generation satisfies the instruction'''
        raise NotImplementedError("`check_following` not implemented.")

    @staticmethod
    def check_query_completeness(query, prev_args, cur_args):
        '''check whether the synthesized query is complete'''
        raise NotImplementedError("`check_query_completeness` not implemented.")
