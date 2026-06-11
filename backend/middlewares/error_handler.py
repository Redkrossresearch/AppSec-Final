from flask import jsonify


def register_error_handlers(app):
    @app.errorhandler(ValueError)
    def value_error(error):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception("Unhandled application error: %s", error)
        return jsonify({"error": "Internal server error"}), 500
