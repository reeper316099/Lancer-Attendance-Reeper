from website import create_app

def start_webserver():
    print("Starting web server...")

    create_app().run(debug=True, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    start_webserver()
