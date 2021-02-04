def or_query_builder(base_query, inputs):
    if len(inputs) > 1:
        out = "Or({})"
        sub_constraints = [base_query.format(input) for input in inputs]
        out = out.format(", ".join(sub_constraints))
    elif len(inputs) == 1:
        out= base_query.format(inputs[0])
    else:
        out = ""
    return out


def or_query_builder_list(base_query, ids):
    ''' or_query_builder, but returns a list of expressions to prevent url
        being too long.
    '''
    query_list = list()
    inputs = list() + ids
    while inputs:
        if len(inputs) > 1:
            out = "Or({})"
            sub_constraints = list()
            # Incrementally add constraints
            while len(', '.join(sub_constraints)) + len(out) < 1000 and inputs:
                sub_constraints.append(base_query.format(inputs.pop(0)))
                
            out = out.format(", ".join(sub_constraints))
        elif len(inputs) == 1:
            out = base_query.format(inputs.pop(0))
        else:
            out = ""

        # Add current string
        query_list.append(out)

    return query_list
