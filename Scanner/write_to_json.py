import json
import pprint

output_file = "arbs.json"


def clear_arbs_json():
    with open(output_file, "w") as output:
        output.write("")


def write_to_json(obj):
    # Serialize object
    arb_json = json.dumps([obj.__dict__])

    # # Read arbs.json
    try:
        with open(output_file, "r") as output:
            arbs_json = json.loads(output.read())
    except:
        with open(output_file, "w") as out:
            out.write(arb_json)
        return

    arbs_json.append(obj.__dict__)

    with open(output_file, "w") as output:
        output.write(json.dumps(arbs_json))


def print_arbs():
    # Pretty print
    with open(output_file, "r") as output:
        arbs_json = json.loads(output.read())
    pprint.pprint(arbs_json)
