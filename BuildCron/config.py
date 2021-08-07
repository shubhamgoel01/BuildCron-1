from bson import ObjectId


def stringify_object_id(obj):
    if type(obj) is list:
        [stringify_object_id(o) for o in obj]
    elif type(obj) is dict:
        for k in obj:
            if type(obj[k]) is ObjectId:
                obj[k] = str(obj[k])
            else:
                stringify_object_id(obj[k])