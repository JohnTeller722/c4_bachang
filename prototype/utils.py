import os
from model import Experiment, ComponentType, Component
import yaml


RANGECONFIG_VERSION=1.0


def component_repr(dumper, component):
    attrs = []
    subattrs = {"types": component.types.name, "config": component.config}
    # subattrs.append(("UUID", component.UUID))
    # subattrs.append(("types", component.types.name))
    # subattrs.append(("config", component.config))
    attrs.append((component.name, subattrs))
    # print(attrs)
    return dumper.represent_mapping(u'tag:yaml.org,2002:map', attrs)


def write_exp(_t):
    yaml.SafeDumper.add_representer(ComponentType, yaml.representer.SafeRepresenter.represent_int)
    yaml.SafeDumper.add_representer(Component, component_repr)
    try:
        os.mkdir("./resource/"+_t.name)
    except FileExistsError:
        pass
    data = dict()
    data["version"] = RANGECONFIG_VERSION
    data.update(_t.dict_dump())
    with open(f"./resource/{_t.name}/range-config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, yaml.SafeDumper, allow_unicode=True, sort_keys=False)

if __name__ == "__main__":
    a = Experiment("test1")
    a.from_yaml(yml_file="./resource/Flask SSTI/range-config.yaml")
    a.name = "COPY"
    write_exp(a)
    b = Experiment("test2")
    b.from_yaml(yml_file="./resource/COPY/range-config.yaml")
    print(b.dict_full())

    
