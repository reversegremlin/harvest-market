from app import app

if __name__ == "__main__":
    # Run the application on port 5000 and bind to all network interfaces
    app.run(host="0.0.0.0", port=5000)
