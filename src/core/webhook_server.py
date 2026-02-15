"""
Webhook server for Stripe integration.

This can be run as a standalone server or integrated into an existing Flask/FastAPI app.

Usage:
    # Standalone
    python webhook_server.py
    
    # Or integrate into existing app
    from webhook_server import create_webhook_blueprint
    app.register_blueprint(create_webhook_blueprint())
"""
import os
import sys
import logging
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, request, jsonify, Blueprint
from stripe_integration import StripeLicenseManager, STRIPE_WEBHOOK_SECRET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_webhook_blueprint() -> Blueprint:
    """
    Create a Flask Blueprint for Stripe webhooks.
    
    Usage:
        from webhook_server import create_webhook_blueprint
        app.register_blueprint(create_webhook_blueprint(), url_prefix='/webhook')
    """
    bp = Blueprint('stripe_webhook', __name__)
    
    # Initialize license manager
    license_manager = StripeLicenseManager()
    
    @bp.route("/stripe", methods=["POST"])
    def stripe_webhook():
        """
        Receive Stripe webhook events.
        
        Configure this URL in Stripe Dashboard:
        https://yourdomain.com/webhook/stripe
        """
        payload = request.data
        signature = request.headers.get("Stripe-Signature")
        
        if not signature:
            logger.error("Missing Stripe-Signature header")
            return jsonify({"error": "Missing signature"}), 400
        
        success, error_msg, license_info = license_manager.handle_webhook(
            payload, signature
        )
        
        if not success:
            logger.error(f"Webhook processing failed: {error_msg}")
            return jsonify({"error": error_msg}), 400
        
        if license_info:
            logger.info(f"License created: {license_info.get('key')} for {license_info.get('email')}")
        
        # Always return 200 to Stripe (prevent retries for handled events)
        return jsonify({"status": "success"}), 200
    
    @bp.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy"}), 200
    
    return bp


def create_app() -> Flask:
    """Create Flask app with webhook endpoint."""
    app = Flask(__name__)
    
    # Register webhook blueprint
    app.register_blueprint(create_webhook_blueprint(), url_prefix='/webhook')
    
    @app.route("/", methods=["GET"])
    def index():
        """Root endpoint."""
        return jsonify({
            "service": "SortMind License Server",
            "version": "1.0.0",
            "endpoints": {
                "webhook": "/webhook/stripe",
                "health": "/webhook/health"
            }
        })
    
    return app


def main():
    """Run standalone webhook server."""
    # Check required environment variables
    required_vars = ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nSet these in your environment or .env file")
        sys.exit(1)
    
    app = create_app()
    
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    print(f"🚀 Starting webhook server on port {port}")
    print(f"📡 Webhook URL: http://localhost:{port}/webhook/stripe")
    print(f"💚 Health check: http://localhost:{port}/webhook/health")
    
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
