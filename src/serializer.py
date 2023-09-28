#!/usr/bin/python3

import json
from enum import Enum


class Serializer(json.JSONEncoder):
    classes = dict()

    def default(self, o):  # pylint: disable=E0202
        if hasattr(o, 'json'):
            return o.json()
        if hasattr(o, '__dict__'):
            return o.__dict__
        return str(o)

    def getClassSignature(self, _dict):
        return ':'.join(sorted(_dict.keys()))

    def register(self, obj, signature=""):
        if signature == "":
            signature = self.getClassSignature(obj.__dict__)
        self.classes[signature] = type(obj)

    def serialize(self, obj, pretty: bool = False):
        d = self.unmap(obj)
        return json.dumps(d, cls=Serializer, indent="\t" if pretty else None)

    def deSerialize(self, json_data):
        obj = json.loads(json_data)
        obj = self.remap(obj)
        return obj

    def unmap(self, obj):
        if isinstance(obj, list):
            new_list = []
            for item in obj:
                new_item = self.unmap(item)
                new_list.append(new_item)
            return new_list

        if isinstance(obj, Enum):
            return obj.__str__()

        if not isinstance(obj, dict):
            if hasattr(obj, 'serialize'):
                d = obj.serialize(self)
                # return d
            elif hasattr(obj, '__dict__'):
                d = {k: v for (k, v) in obj.__dict__.items() if not k.startswith("_")}
            else:
                return obj
        else:
            d = obj

        for child in d:
            d[child] = self.unmap(d[child])
        return d

    def remap(self, obj):
        if type(obj) is list:
            new_list = []
            for item in obj:
                new_item = self.remap(item)
                new_list.append(new_item)
            return new_list

        if not isinstance(obj, dict):
            return obj

        must_remap_properties = True
        signature = self.getClassSignature(obj)
        if signature in self.classes:
            clas = self.classes[signature]
            new_obj = clas()
            if hasattr(new_obj, 'load'):
                new_obj.load(obj, self)
                must_remap_properties = False
            else:
                for key in new_obj.__dict__.keys():
                    new_obj.__dict__[key] = obj.get(key, "")

            obj = new_obj

        if must_remap_properties:
            if isinstance(obj, dict):
                props = obj
            else:
                props = obj.__dict__

            for child in props:
                props[child] = self.remap(props[child])

        return obj


# customer = entities.Customer(1, 'Stephen', datetime.datetime.now())
# customer.addresses.append(entities.Address(id=1, addresstype='Normal', street='Street', city='City', code='Code', country='Country'))
# customer.addresses.append(entities.Address(id=2, addresstype='Extra', street='Street', city='City', code='Code', country='Country'))
# customer.orders.append(entities.Order(id=1, orderdate=datetime.datetime.now(), amount=100))
# customer.orders.append(entities.Order(id=2, orderdate=datetime.datetime.now(), amount=100))
# ser = Serializer()
# ser.register(entities.Customer())
# ser.register(entities.Envelope())
# ser.register(entities.Address())
# ser.register(entities.Order())
# ser.register(utils.Version())

# envelope = entities.Envelope('create', customer)
# data = ser.serialize(envelope)
# print(data)
# item = ser.deSerialize(data)
# print(item)
# print(item.object.address)

serializer_instance = Serializer()
