import os, sys, json
import numpy as np
from operator import itemgetter

class ReferenceFlower:
    def __init__(self, data):
        self.reference_flower = data

    def calculate_node_size(self, original_node, new_sum):
        o_sum = original_node["sum"]
        o_size = original_node["size"]
        new_size = (o_size * new_sum / o_sum) if o_sum > 0 else 0
        # print(o_sum, o_size, new_sum, new_size)
        return new_size

    def calculate_edge_weight(self, original_edge, new_weight):
        o_weight = original_edge["o_weight"]
        o_norm_weight = original_edge["weight"]
        # print(o_weight, o_norm_weight, new_weight)
        if o_weight == 0:
            return 0
        new_norm_weight = o_norm_weight * new_weight / o_weight
        return new_norm_weight

    def compare(self, new_flower):
        ntype = ["author", "conf", "inst", "fos"]
        filtered_flower = [self.reference_flower[type] for type in ntype]
        for nidx, nflower in enumerate(new_flower):
            new_names = [ff["name"] for ff in nflower["nodes"]]
            filtered_names = [filtered_flower[nidx]["nodes"][0]["name"]]
            flower_dict = {}
            for i, n in enumerate(filtered_flower[nidx]["nodes"]):
                if n["id"] > 0 and n["name"] in new_names:
                    original_index = new_names.index(n["name"])
                    n["new_size"] = self.calculate_node_size(n, nflower["nodes"][original_index]["sum"])
                    n["new_weight"] = nflower["nodes"][original_index]["weight"]
                    filtered_names.append(n["name"])
                elif n["id"] == 0:
                    n["new_size"] = 1
                else:
                    n["new_size"] = -1

            # print("filtered_names", filtered_names)
            for old_l in filtered_flower[nidx]["links"]:
                for new_l in nflower["links"]:
                    if nflower["nodes"][new_l["source"]]["name"] == filtered_flower[nidx]["nodes"][old_l["source"]]["name"]\
                        and nflower["nodes"][new_l["target"]]["name"] == filtered_flower[nidx]["nodes"][old_l["target"]]["name"]\
                        and new_l["type"] == old_l["type"]:
                        old_l["new_weight"] = self.calculate_edge_weight(old_l, new_l["o_weight"])
                        break
                    else:
                        old_l["new_weight"] = 0
        return filtered_flower

    def data(self):
        return json.dumps(self.reference_flower)


def compare_flowers(reference_flower_data, flower_info):
    reference_flower = ReferenceFlower(json.loads(reference_flower_data))
    filtered_flower = reference_flower.compare(flower_info)
    # print(filtered_flower["links"])
    return filtered_flower
