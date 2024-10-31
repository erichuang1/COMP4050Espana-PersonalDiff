from src.main import create_app

if __name__ == '__main__':
    app = create_app()
    print("Server is starting...")
    app.run(host='0.0.0.0', port=80, debug=True)#, ssl_context=('cert.pem', 'key.pem'))
