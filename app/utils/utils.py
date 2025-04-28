from flask import jsonify

def create_error_response(errors, status_code=400):
    return jsonify({'errors': errors}), status_code