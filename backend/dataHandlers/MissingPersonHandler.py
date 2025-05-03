import json
import uuid
def add_to_db(first_name, last_name,details,created_by,vector):
    """
    Adds data to the database.
    """
    data=None
    try:
        with open("database/MissingPersons.json", "r") as db:
            data=json.loads(db.read())
    except FileNotFoundError:
        data = { "missingPersons" : []}
    if data is None:
        data = { "missingPersons" : []}
    data["missingPersons"].append({
        "first_name": first_name,
        "last_name": last_name,
        "details": details,
        "created_by": created_by,
        "vector": vector,
        "uuid": str(uuid.uuid4()),
    })
    with open("database/MissingPersons.json", "w") as db:
        db.write(json.dumps(data, indent=4))
    return data["missingPersons"][-1]["uuid"]


def get_from_db():
    """
    Gets data from the database.
    """
    data = None
    try:
        with open("database/MissingPersons.json", "r") as db:
            data = db.read()
    except FileNotFoundError:
        return [{}]
    if data is None:
        return [{}]
    else:
        data = json.loads(data)
    
    return [{"first_name":person["first_name"],"last_name":person["last_name"],"uuid":person["uuid"],} for person in data['missingPersons']]