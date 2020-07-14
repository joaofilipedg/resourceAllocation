from flask_app.app import app

if __name__ == "__main__":
    try:
        app.run()
    except Exception as e:
        print(e)