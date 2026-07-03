
import os
if __name__ == '__main__':
    # Force the app to extract Render's dynamic host port or default to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
