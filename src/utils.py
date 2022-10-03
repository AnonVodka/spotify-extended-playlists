
from typing import Tuple

class utils():
    
    def __init__(self):
        pass

    @staticmethod
    def remove_duplicates_from_list(a, return_duplicates=False) -> Tuple[list, list]:
        b = []
        d = []
        for el in a:
            if el not in b:
                b.append(el)
            else:
                d.append(el)

        return (b, d) if return_duplicates else b

    @staticmethod
    def get_diff_between_lists(a, b, c = None) -> Tuple[list, list]:
        not_in_a = []
        not_in_b = []

        for el in a:
            if c is None:
                if el not in b:
                    not_in_b.append(el)
            else:
                if el not in b and el not in c:
                    not_in_b.append(el)
        
        for el in b:
            if c is None:
                if el not in a:
                    not_in_a.append(el)
            else:
                if el not in a and el not in c:
                    not_in_a.append(el)

        return (not_in_a, not_in_b)
