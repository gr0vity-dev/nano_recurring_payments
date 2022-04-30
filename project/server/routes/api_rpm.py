from flask import jsonify, request
from project.server.api.db_access import rpm_seed, rpm_seed_index
from . import routes


@routes.route("/api/rpm/<seed>", methods=["GET", "DELETE"])
# @limiter.limit("3/hour")
def rpm_seed_hood(seed):
    json_msg = None if request.method == 'GET' else request.json
    res = rpm_seed(seed, request.method, json_msg) 
    return jsonify(res[0]), res[1]

#ONLY 1 RP per destination from the same seed and index
@routes.route("/api/rpm/<seed>/<index>", methods=["GET", "POST", "PUT", "DELETE" ])
# @limiter.limit("3/hour")
def rpm_seed_index_hood(seed, index):
    json_msg = None if request.method == 'GET' else request.json
    res = rpm_seed_index(seed,index, request.method, json_msg)
    return jsonify(res[0]), res[1]