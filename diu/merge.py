from copy import deepcopy


def merge(a, b):
    """
    Recursively merge datasets of a and b together so that:

    * Dicts are (recursively) merged
    * Lists are appended together
    * Other types take the value from b

    A ValueError is raised when trying to merge two items of
    a different type.
    """
    if type(a) != type(b):
        raise ValueError(
            "Trying to merge two different types of data:\n"
            "Value A {a_type} = {a_value}\n\n"
            "Value B {b_type} = {b_value}\n".format(
                a_type=type(a),
                a_value=a,
                b_type=type(b),
                b_value=b,
            )
        )

    result = None
    if isinstance(b, list):
        result = list(set(a + b))
    elif isinstance(b, dict):
        result = deepcopy(a)
        for k, v in b.items():
            if k in result:
                result[k] = merge(result[k], v)
            else:
                result[k] = deepcopy(v)
    else:
        return b
    return result
